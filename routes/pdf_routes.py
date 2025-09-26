import io
import logging
from typing import List

from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd

from config import NCM_CSV_PATH, TOP_K
from services.extract_service import extract_lines_from_pdf_bytes
from services.format_service import format_many
from services.normalize_service import normalizar_com_ollama, choose_best_ncm
from services.rag_service import RAGService
from services.scraper_service import find_manufacturer_and_location
from services.predict_ncm import PredictNCMService

logger = logging.getLogger(__name__)
router = APIRouter()

def _get_or_create_rag(request: Request) -> RAGService:
    app_state = request.app.state
    rag = getattr(app_state, "rag_service", None)
    if rag is None:
        logger.info("Inicializando RAGService (carregando CSV e embeddings)...")
        rag = RAGService(NCM_CSV_PATH)
        setattr(app_state, "rag_service", rag)
    return rag

def _get_or_create_predict_ncm(request: Request) -> PredictNCMService:
    app_state = request.app.state
    predict_service = getattr(app_state, "predict_ncm_service", None)
    if predict_service is None:
        logger.info("Inicializando PredictNCMService (carregando modelo .pkl)...")
        predict_service = PredictNCMService(model_path="app/modelo_class/modelo_classificador.pkl")
        setattr(app_state, "predict_ncm_service", predict_service)
    return predict_service

@router.post("/process_pdf")
async def process_pdf(request: Request, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    try:
        itens_raw: List[str] = extract_lines_from_pdf_bytes(file_bytes)
    except Exception as e:
        logger.exception("Erro extraindo PDF")
        raise HTTPException(status_code=500, detail=f"Erro extraindo PDF: {e}")

    if not itens_raw:
        raise HTTPException(status_code=400, detail="Nenhum item encontrado no PDF.")

    itens_format = format_many(itens_raw)
    rag_service = _get_or_create_rag(request)
    predict_ncm_service = _get_or_create_predict_ncm(request)

    rows = []
    for it in itens_format:
        pn = it.get("partnumber", "")
        desc_raw = it.get("descricao_raw", "")
        
        scraper_info = find_manufacturer_and_location(pn)
        fabricante = scraper_info.get("fabricante", "Não encontrado")
        localizacao = scraper_info.get("localizacao", "Não encontrada")

        ncm_modelo_simples = ""
        try:
            ncm_modelo_simples = predict_ncm_service.suggest_ncm(desc_raw)
        except Exception as e:
            logger.error("Erro em PredictNCM: %s", e)
            ncm_modelo_simples = "ERRO"

        try:
            desc_norm = normalizar_com_ollama(desc_raw)
        except Exception as e:
            logger.warning("Fallback na normalização: %s", e)
            desc_norm = desc_raw

        try:
            top_candidates = rag_service.find_top_ncm(desc_norm, top_k=TOP_K)
            if not top_candidates:
                raise ValueError("Nenhum candidato NCM")
        except Exception as e:
            logger.exception("Erro RAG")
            rows.append({
                "partnumber": pn,
                "fabricante": fabricante,
                "localizacao": localizacao,
                "ncm_rag_llm": "Erro RAG",
                "ncm_modelo_simples": ncm_modelo_simples,
                "descricao": desc_raw
            })
            continue

        try:
            ncm_final_rag = choose_best_ncm(desc_norm, top_candidates)
        except Exception as e:
            logger.warning("Erro escolha LLM, usando top candidate: %s", e)
            ncm_final_rag = top_candidates[0]["ncm"]

        descricao_final = next(
            (c.get("descricao_longa") or c.get("descricao", "") for c in top_candidates if c.get("ncm") == ncm_final_rag),
            desc_norm
        )

        rows.append({
            "partnumber": pn,
            "fabricante": fabricante,
            "localizacao": localizacao,
            "ncm_rag_llm": ncm_final_rag,
            "ncm_modelo_simples": ncm_modelo_simples,
            "descricao_fiscal_sugerida": descricao_final
        })

    df_out = pd.DataFrame(rows, columns=["partnumber", "fabricante", "localizacao", "ncm_rag_llm", "ncm_modelo_simples", "descricao_fiscal_sugerida"])
    
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine="openpyxl") as writer:
        df_out.to_excel(writer, index=False, sheet_name="resultado")
    stream.seek(0)

    filename = file.filename.rsplit(".", 1)[0] + "_classificado.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )