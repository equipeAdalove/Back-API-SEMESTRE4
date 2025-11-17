import io
import logging
from typing import List, Any, Dict, Optional

import pandas as pd
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from models import models
from schemas.pdf_schemas import (
    ExtractedItem,
    ExtractionResponse,
    ExcelRequest,
)
from services.PDFServices.extract_service import extract_items_from_pdf_bytes
from services.PDFServices.normalize_service import normalizar_com_ollama, choose_best_ncm
from services.PDFServices.rag_service import RAGService
from services.ScrapingServices.scraper_service import find_manufacturer_and_location
from services.ItemServices.item_services import (
    get_item_by_partnumber,
    upsert_item,
)
from services.FabricanteServices.fabricante_services import get_or_create_fabricante
from services.TransactionServices.transactions_services import (
    create_transaction,
    link_item_to_transacao,
)

logger = logging.getLogger(__name__)


async def extract_from_pdf(
    file,
    db: Session,
    current_user: models.Usuario,
) -> ExtractionResponse:
    """
    1) Valida o arquivo PDF enviado
    2) Cria a Transação no banco
    3) Extrai itens do PDF (AVNET / MOUSER / XWORKS)
    4) Retorna ExtractionResponse com transacao_id + itens extraídos
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie um arquivo PDF válido com nome.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo vazio.",
        )

    # Cria transação no banco via TransactionService
    try:
        usuario_id = int(getattr(current_user, "id"))
        db_transacao = create_transaction(
            db=db,
            usuario_id=usuario_id,
            nome=file.filename,
        )
    except Exception as e:
        logger.exception("Erro ao criar transação no banco")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar transação: {e}",
        )

    # Extração de itens (multi-PDF: AVNET / MOUSER / XWORKS)
    try:
        itens_raw: List[Dict[str, Optional[str]]] = extract_items_from_pdf_bytes(
            file_bytes
        )
    except Exception as e:
        logger.exception("Erro extraindo itens do PDF")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro durante a extração do PDF: {e}",
        )

    transacao_id = int(getattr(db_transacao, "id"))

    if not itens_raw:
        logger.info(f"Nenhum item extraído do PDF: {file.filename}")
        return ExtractionResponse(transacao_id=transacao_id, items=[])

    # Converte dicts -> Pydantic ExtractedItem (ncm opcional)
    itens_formatados: List[ExtractedItem] = []
    for item in itens_raw:
        partnumber = (item.get("partnumber") or "").strip()
        descricao_raw = (item.get("descricao_raw") or "").strip()
        ncm = item.get("ncm")

        itens_formatados.append(
            ExtractedItem(
                partnumber=partnumber,
                descricao_raw=descricao_raw,
                ncm=ncm,
            )
        )

    return ExtractionResponse(
        transacao_id=transacao_id,
        items=itens_formatados,
    )


async def process_items(
    transacao_id: int,
    itens_validados: List[ExtractedItem],
    db: Session,
    current_user: models.Usuario,
    rag_service: RAGService,
) -> List[dict]:
    """
    Aplica cache de banco, scraping, normalização, RAG + LLM
    e persiste os itens/relacionamentos no banco.
    """
    if not itens_validados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lista de itens para processar está vazia.",
        )

    db_transacao = (
        db.query(models.Transacao)
        .filter(
            models.Transacao.id == transacao_id,
            models.Transacao.usuario_id == getattr(current_user, "id"),
        )
        .first()
    )
    if not db_transacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada ou não pertence ao usuário.",
        )

    known_manufacturers = {"texas instruments", "samsung electro-mechanics", "intel"}

    processed_rows: List[dict] = []

    for item in itens_validados:
        pn = item.partnumber
        desc_raw = item.descricao_raw

        db_item = get_item_by_partnumber(db, pn)

        # Cache HIT
        if db_item is not None:
            ncm_db: Any = getattr(db_item, "ncm", None)
            fabricante_db: Any = getattr(db_item, "fabricante", None)

            if ncm_db and fabricante_db:
                logger.info(f"Cache HIT para PN {pn}. Usando dados do DB.")

                partnumber_db = getattr(db_item, "partnumber")
                fabricante_nome = getattr(fabricante_db, "razao_soc")
                fabricante_endereco = getattr(fabricante_db, "endereco")
                descricao_db = getattr(db_item, "descricao")

                processed_rows.append(
                    {
                        "partnumber": partnumber_db,
                        "fabricante": fabricante_nome,
                        "localizacao": fabricante_endereco,
                        "ncm": ncm_db,
                        "descricao": descricao_db,
                        "is_new_manufacturer": False,
                    }
                )

                link_item_to_transacao(
                    db=db,
                    transacao_id=transacao_id,
                    item_partnumber=str(partnumber_db),
                )
                continue

        # Cache MISS
        logger.info(f"Cache MISS para PN {pn}. Processando...")
        try:
            scraper_info = find_manufacturer_and_location(pn)
            fabricante = scraper_info.get("fabricante", "Não identificado")
            localizacao = scraper_info.get("localizacao", "Não encontrada")
            is_new = (
                fabricante != "Não identificado"
                and fabricante.lower() not in known_manufacturers
            )

            try:
                desc_norm = normalizar_com_ollama(desc_raw)
            except Exception as e:
                logger.warning(f"Fallback na normalização para PN {pn}: {e}")
                desc_norm = desc_raw

            try:
                top_candidates = rag_service.find_top_ncm(
                    desc_norm,
                    top_k=settings.top_k,
                )
                if not top_candidates:
                    raise ValueError("Nenhum candidato NCM encontrado pelo RAG.")
            except Exception as e:
                logger.warning(f"Erro RAG para PN {pn} ({desc_norm}): {e}")
                processed_rows.append(
                    {
                        "partnumber": pn,
                        "fabricante": fabricante,
                        "localizacao": localizacao,
                        "ncm": "Erro RAG",
                        "descricao": desc_raw,
                        "is_new_manufacturer": is_new,
                    }
                )
                continue

            try:
                ncm_final = choose_best_ncm(desc_norm, top_candidates)
            except Exception as e:
                logger.warning(
                    f"Erro escolha LLM para PN {pn}, usando top candidate: {e}"
                )
                ncm_final = top_candidates[0]["ncm"]

            descricao_final = next(
                (
                    c.get("descricao_longa") or c.get("descricao", "")
                    for c in top_candidates
                    if c.get("ncm") == ncm_final
                ),
                desc_norm,
            )

            item_dict = {
                "partnumber": pn,
                "fabricante": fabricante,
                "localizacao": localizacao,
                "ncm": ncm_final,
                "descricao": descricao_final,
                "descricao_raw": desc_raw,
                "is_new_manufacturer": is_new,
            }

            db_fabricante = get_or_create_fabricante(
                db=db,
                nome=fabricante,
                localizacao=localizacao,
            )
            fabricante_id = int(getattr(db_fabricante, "id"))

            db_item_salvo = upsert_item(
                db=db,
                item_data=item_dict,
                fabricante_id=fabricante_id,
            )

            if db_item_salvo is not None:
                partnumber_salvo = getattr(db_item_salvo, "partnumber")
                link_item_to_transacao(
                    db=db,
                    transacao_id=transacao_id,
                    item_partnumber=str(partnumber_salvo),
                )

            processed_rows.append(
                {
                    "partnumber": pn,
                    "fabricante": fabricante,
                    "localizacao": localizacao,
                    "ncm": ncm_final,
                    "descricao": descricao_final,
                    "is_new_manufacturer": is_new,
                }
            )

        except Exception as e:
            logger.exception(f"Erro inesperado processando item PN {pn}")
            processed_rows.append(
                {
                    "partnumber": pn,
                    "fabricante": "Erro Processamento",
                    "localizacao": "",
                    "ncm": "Erro",
                    "descricao": desc_raw,
                    "is_new_manufacturer": False,
                }
            )
            continue

    return processed_rows


def generate_excel_response(data: ExcelRequest) -> StreamingResponse:
    items_data = [item.model_dump() for item in data.items]

    if not items_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum item fornecido para gerar o Excel.",
        )

    try:
        df_out = pd.DataFrame(items_data)
        if "is_new_manufacturer" in df_out.columns:
            df_out = df_out.drop(columns=["is_new_manufacturer"])

        stream = io.BytesIO()
        with pd.ExcelWriter(stream, engine="openpyxl") as writer:
            df_out.to_excel(writer, index=False, sheet_name="resultado")
        stream.seek(0)

        filename = "pedido_classificado.xlsx"
        return StreamingResponse(
            stream,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception:
        logger.exception("Erro gerando arquivo Excel")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerar o arquivo Excel.",
        )
