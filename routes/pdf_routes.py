import io
import logging
from typing import List
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
from pydantic import BaseModel

from app.core.config import settings
from services.extract_service import extract_lines_from_pdf_bytes
from services.format_service import format_many
from services.normalize_service import normalizar_com_ollama, choose_best_ncm
from services.rag_service import RAGService, _get_or_create_rag 
from services.scraper_service import find_manufacturer_and_location
from services.auth_service import get_current_user 

router = APIRouter()
logger = logging.getLogger(__name__)

class ExtractedItem(BaseModel):
    partnumber: str
    descricao_raw: str

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

# --- Endpoint /extract_from_pdf ---
@router.post("/extract_from_pdf", response_model=List[ExtractedItem], status_code=status.HTTP_200_OK)
async def extract_from_pdf(file: UploadFile = File(...), current_user: dict = Depends(get_current_user) ):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Envie um arquivo PDF válido com nome.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo vazio.")

    try:
        itens_raw: List[str] = extract_lines_from_pdf_bytes(file_bytes)
    except Exception as e:
        logger.exception("Erro extraindo PDF")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro durante a extração do PDF: {e}")

    if not itens_raw:
        logger.info(f"Nenhum item extraído do PDF: {file.filename}")
        return JSONResponse(content=[])

    itens_formatados = format_many(itens_raw)
    return JSONResponse(content=itens_formatados)

# --- Endpoint /process_items ---
@router.post("/process_items", response_model=List[FinalItem], status_code=status.HTTP_200_OK)
async def process_items(request: Request, data: ProcessRequest, current_user: dict = Depends(get_current_user)):
    itens_validados = data.items
    if not itens_validados:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lista de itens para processar está vazia.")

    rag_service = _get_or_create_rag(request, settings.ncm_csv_path)

    known_manufacturers = {"texas instruments", "samsung electro-mechanics", "intel"} # Mock

    processed_rows = []
    for item in itens_validados:
        pn = item.partnumber
        desc_raw = item.descricao_raw

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

            processed_rows.append({
                "partnumber": pn, "fabricante": fabricante, "localizacao": localizacao,
                "ncm": ncm_final, "descricao": descricao_final, "is_new_manufacturer": is_new
            })

        except Exception as e:
            logger.exception(f"Erro inesperado processando item PN {pn}")
            processed_rows.append({
                "partnumber": pn, "fabricante": "Erro Processamento", "localizacao": "",
                "ncm": "Erro", "descricao": desc_raw, "is_new_manufacturer": False
            })
            continue

    return JSONResponse(content=processed_rows)

# --- Endpoint /generate_excel ---
@router.post("/generate_excel", status_code=status.HTTP_200_OK)
async def generate_excel(data: ExcelRequest, current_user: dict = Depends(get_current_user)):
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