import io
import logging
from typing import List, Optional
from datetime import datetime 
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload 
from app.core.config import settings
from services.extract_service import extract_lines_from_pdf_bytes
from services.format_service import format_many
from services.normalize_service import normalizar_com_ollama, choose_best_ncm
from services.rag_service import RAGService, _get_or_create_rag 
from services.scraper_service import find_manufacturer_and_location
from services.auth_service import get_current_user 
from services import auth_service
from database import crud, database
from schemas import user_schemas
from models import models

router = APIRouter()
logger = logging.getLogger(__name__)

class ExtractedItem(BaseModel):
    partnumber: str
    descricao_raw: str

class ExtractionResponse(BaseModel):
    transacao_id: int
    items: List[ExtractedItem]

class ProcessRequest(BaseModel):
    items: List[ExtractedItem]

class FinalItem(BaseModel):
    partnumber: str
    fabricante: str
    localizacao: str
    ncm: str
    descricao: str
    is_new_manufacturer: bool

class ExcelRequest(BaseModel):
    items: List[FinalItem]

class TransacaoInfo(BaseModel):
    id: int
    nome: Optional[str] = None 
    created_at: datetime
    class Config:
        from_attributes = True

class RenameRequest(BaseModel):
    nome: str

class TransacaoDetailResponse(BaseModel):
    transacao_id: int
    processed_items: List[FinalItem]
    pending_items: List[ExtractedItem]


@router.post("/extract_from_pdf", response_model=ExtractionResponse, status_code=status.HTTP_200_OK)
async def extract_from_pdf(
    file: UploadFile = File(...), 
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Envie um arquivo PDF válido com nome.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo vazio.")

    try:
        db_transacao = crud.create_transacao(db=db, usuario_id=current_user.id)
        db_transacao.nome = file.filename
        db.commit()
        db.refresh(db_transacao)
    except Exception as e:
        db.rollback()
        logger.exception("Erro ao criar transação no banco")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao iniciar transação: {e}")

    try:
        itens_raw: List[str] = extract_lines_from_pdf_bytes(file_bytes)
    except Exception as e:
        logger.exception("Erro extraindo PDF")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro durante a extração do PDF: {e}")

    if not itens_raw:
        logger.info(f"Nenhum item extraído do PDF: {file.filename}")
        return ExtractionResponse(transacao_id=db_transacao.id, items=[])

    itens_formatados = format_many(itens_raw)
    
    try:
        for item in itens_formatados:
            item_data = {
                "partnumber": item["partnumber"],
                "descricao_raw": item["descricao_raw"]
            }
            saved_item = crud.upsert_item(db, item_data=item_data, fabricante_id=None)
            if saved_item:
                crud.link_item_to_transacao(
                    db=db, 
                    transacao_id=db_transacao.id, 
                    item_partnumber=saved_item.partnumber
                )
    except Exception as e:
        logger.error(f"Erro ao salvar itens parciais: {e}")
    
    return ExtractionResponse(transacao_id=db_transacao.id, items=itens_formatados)


@router.post("/process_items/{transacao_id}", response_model=List[FinalItem], status_code=status.HTTP_200_OK)
async def process_items(
    transacao_id: int, 
    data: ProcessRequest, 
    request: Request, 
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    itens_validados = data.items
    if not itens_validados:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lista de itens para processar está vazia.")
    
    db_transacao = db.query(models.Transacao).filter(
        models.Transacao.id == transacao_id, 
        models.Transacao.usuario_id == current_user.id
    ).first()
    if not db_transacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada ou não pertence ao usuário.")

    rag_service = _get_or_create_rag(request, settings.ncm_csv_path)
    known_manufacturers = {"texas instruments", "samsung electro-mechanics", "intel"}

    processed_rows = []
    for item in itens_validados:
        pn = item.partnumber
        desc_raw = item.descricao_raw
        db_item = crud.get_item_by_partnumber(db, pn)
        
        if db_item and db_item.ncm and db_item.fabricante: 
            logger.info(f"Cache HIT para PN {pn}. Usando dados do DB.")
            processed_rows.append({
                "partnumber": db_item.partnumber,
                "fabricante": db_item.fabricante.razao_soc,
                "localizacao": db_item.fabricante.endereco,
                "ncm": db_item.ncm,
                "descricao": db_item.descricao,
                "is_new_manufacturer": False 
            })
            existing_link = db.query(models.TransacaoItem).filter(
                models.TransacaoItem.transacao_id == transacao_id,
                models.TransacaoItem.item_partnumber == db_item.partnumber
            ).first()
            if not existing_link:
                crud.link_item_to_transacao(db=db, transacao_id=transacao_id, item_partnumber=db_item.partnumber)
            continue 
        
        logger.info(f"Cache MISS para PN {pn}. Processando...")
        try:
            scraper_info = find_manufacturer_and_location(pn)
            fabricante = scraper_info.get("fabricante", "Não identificado")
            localizacao = scraper_info.get("localizacao", "Não encontrada")
            is_new = fabricante != "Não identificado" and fabricante.lower() not in known_manufacturers

            try:
                desc_norm = normalizar_com_ollama(desc_raw)
            except Exception as e:
                logger.warning(f"Fallback na normalização para PN {pn}: {e}")
                desc_norm = desc_raw

            try:
                top_candidates = rag_service.find_top_ncm(desc_norm, top_k=settings.top_k)
                if not top_candidates:
                    raise ValueError("Nenhum candidato NCM encontrado pelo RAG.")
            except Exception as e:
                logger.warning(f"Erro RAG para PN {pn} ({desc_norm}): {e}")
                processed_rows.append({
                    "partnumber": pn, "fabricante": fabricante, "localizacao": localizacao,
                    "ncm": "Erro RAG", "descricao": desc_raw, "is_new_manufacturer": is_new
                })
                continue

            try:
                ncm_final = choose_best_ncm(desc_norm, top_candidates)
            except Exception as e:
                logger.warning(f"Erro escolha LLM para PN {pn}, usando top candidate: {e}")
                ncm_final = top_candidates[0]["ncm"]

            descricao_final = next(
                (c.get("descricao_longa") or c.get("descricao", "")
                for c in top_candidates if c.get("ncm") == ncm_final),
                desc_norm
            )
            
            item_dict = {
                "partnumber": pn, 
                "fabricante": fabricante, 
                "localizacao": localizacao,
                "ncm": ncm_final, 
                "descricao": descricao_final, 
                "descricao_raw": desc_raw, 
                "is_new_manufacturer": is_new
            }

            db_fabricante = crud.get_or_create_fabricante(db, nome=fabricante, localizacao=localizacao)
            db_item_salvo = crud.upsert_item(db, item_data=item_dict, fabricante_id=db_fabricante.id)
            
            if db_item_salvo: 
                existing_link = db.query(models.TransacaoItem).filter(
                    models.TransacaoItem.transacao_id == transacao_id,
                    models.TransacaoItem.item_partnumber == db_item_salvo.partnumber
                ).first()
                if not existing_link:
                    crud.link_item_to_transacao(db, transacao_id=transacao_id, item_partnumber=db_item_salvo.partnumber)

            processed_rows.append({
                "partnumber": pn, 
                "fabricante": fabricante, 
                "localizacao": localizacao,
                "ncm": ncm_final, 
                "descricao": descricao_final, 
                "is_new_manufacturer": is_new
            })

        except Exception as e:
            logger.exception(f"Erro inesperado processando item PN {pn}")
            processed_rows.append({
                "partnumber": pn, "fabricante": "Erro Processamento", "localizacao": "",
                "ncm": "Erro", "descricao": desc_raw, "is_new_manufacturer": False
            })
            continue

    return JSONResponse(content=processed_rows)

@router.post("/generate_excel", status_code=status.HTTP_200_OK)
async def generate_excel(data: ExcelRequest, current_user: models.Usuario = Depends(get_current_user)):
    items_data = [item.model_dump() for item in data.items]
    if not items_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum item fornecido para gerar o Excel.")
    try:
        df_out = pd.DataFrame(items_data)
        if 'is_new_manufacturer' in df_out.columns:
            df_out = df_out.drop(columns=['is_new_manufacturer'])
        stream = io.BytesIO()
        with pd.ExcelWriter(stream, engine="openpyxl") as writer:
            df_out.to_excel(writer, index=False, sheet_name="resultado")
        stream.seek(0)
        filename = "pedido_classificado.xlsx"
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    except Exception as e:
        logger.exception("Erro gerando arquivo Excel")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao gerar o arquivo Excel.")
    
@router.put("/update_transaction/{transacao_id}", status_code=status.HTTP_200_OK)
async def update_transaction_items(
    transacao_id: int, 
    data: ExcelRequest, 
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth_service.get_current_user)
):
    if not data.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhuma item fornecido.")
    db_transacao = db.query(models.Transacao).filter(
        models.Transacao.id == transacao_id, 
        models.Transacao.usuario_id == current_user.id
    ).first()
    if not db_transacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada ou não pertence ao usuário.")
    try:
        updated_items_count = 0
        for item_data in data.items:
            item_dict = item_data.model_dump() 
            db_fabricante = crud.get_or_create_fabricante(
                db=db,
                nome=item_dict.get('fabricante', 'Não identificado'),
                localizacao=item_dict.get('localizacao', 'Não encontrada')
            )
            db_item = crud.upsert_item(
                db=db,
                item_data=item_dict,
                fabricante_id=db_fabricante.id
            )
            if db_item:
                updated_items_count += 1
                link = db.query(models.TransacaoItem).filter(
                    models.TransacaoItem.transacao_id == transacao_id,
                    models.TransacaoItem.item_partnumber == db_item.partnumber
                ).first()
                if not link:
                    crud.link_item_to_transacao(
                        db=db,
                        transacao_id=transacao_id,
                        item_partnumber=db_item.partnumber
                    )
        return {"message": f"{updated_items_count} itens atualizados com sucesso na transação {transacao_id}."}
    except Exception as e:
        logger.exception("Erro ao atualizar itens no banco de dados")
        db.rollback() 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno ao salvar: {e}")


@router.get("/transacoes", response_model=List[TransacaoInfo], status_code=status.HTTP_200_OK)
async def get_user_transactions(
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth_service.get_current_user)
):
    
    transacoes = db.query(models.Transacao).options(
        joinedload(models.Transacao.itens).joinedload(models.TransacaoItem.item)
    ).filter(
        models.Transacao.usuario_id == current_user.id
    ).order_by(models.Transacao.created_at.desc()).all()
    
    response_list: List[TransacaoInfo] = []
    for t in transacoes:
        is_concluido = False
        if t.itens:
            if any(ti.item and ti.item.ncm for ti in t.itens):
                is_concluido = True
        
        if is_concluido:
            response_list.append(
                TransacaoInfo(
                    id=t.id,
                    nome=t.nome,
                    created_at=t.created_at
                )
            )
            
    return response_list

@router.get("/transacao/{transacao_id}", response_model=TransacaoDetailResponse, status_code=status.HTTP_200_OK)
async def get_transaction_details(
    transacao_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth_service.get_current_user)
):
    db_transacao = db.query(models.Transacao).options(
        joinedload(models.Transacao.itens).joinedload(models.TransacaoItem.item).joinedload(models.Item.fabricante)
    ).filter(
        models.Transacao.id == transacao_id,
        models.Transacao.usuario_id == current_user.id
    ).first()

    if not db_transacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada ou não pertence ao usuário.")

    processed_items_list: List[FinalItem] = []
    pending_items_list: List[ExtractedItem] = []
    
    for transacao_item in db_transacao.itens:
        item = transacao_item.item
        if not item:
            continue
            
        if item.fabricante and item.ncm:
            processed_items_list.append(
                FinalItem(
                    partnumber=item.partnumber,
                    fabricante=item.fabricante.razao_soc,
                    localizacao=item.fabricante.endereco or "Não encontrada",
                    ncm=item.ncm,
                    descricao=item.descricao or "",
                    is_new_manufacturer=False 
                )
            )
        else:
            pending_items_list.append(
                ExtractedItem(
                    partnumber=item.partnumber,
                    descricao_raw=item.descricao_curta or item.descricao or ""
                )
            )

    return TransacaoDetailResponse(
        transacao_id=db_transacao.id, 
        processed_items=processed_items_list,
        pending_items=pending_items_list
    )

@router.put("/transacao/{transacao_id}/rename", status_code=status.HTTP_200_OK)
async def rename_transaction(
    transacao_id: int,
    data: RenameRequest,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth_service.get_current_user)
):
    if not data.nome or not data.nome.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O nome não pode estar vazio.")

    db_transacao = db.query(models.Transacao).filter(
        models.Transacao.id == transacao_id,
        models.Transacao.usuario_id == current_user.id
    ).first()

    if not db_transacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada ou não pertence ao usuário.")

    try:
        db_transacao.nome = data.nome
        db.commit()
        return {"message": "Transação renomeada com sucesso."}
    except Exception as e:
        db.rollback()
        logger.exception(f"Erro ao renomear transação {transacao_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno: {e}")
    
@router.delete("/transacao/{transacao_id}", status_code=status.HTTP_200_OK)
async def delete_transaction(
    transacao_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth_service.get_current_user)
):
    db_transacao = db.query(models.Transacao).filter(
        models.Transacao.id == transacao_id,
        models.Transacao.usuario_id == current_user.id
    ).first()

    if not db_transacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada ou não pertence ao usuário.")

    try:
        db.delete(db_transacao)
        db.commit()
        return {"message": "Transação excluída com sucesso."}
    except Exception as e:
        db.rollback()
        logger.exception(f"Erro ao excluir transação {transacao_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno: {e}")