import io
import logging
from typing import List
import pandas as pd
from services.extract_service import extract_lines_from_pdf_bytes
from services.format_service import format_many
from services.normalize_service import normalizar_com_ollama, choose_best_ncm
from services.rag_service import _get_or_create_rag
from services.scraper_service import find_manufacturer_and_location
from app.core.config import settings


logger = logging.getLogger(__name__)


class PDFService:
    @staticmethod
    async def process_pdf(request, file):
        if not file.filename.lower().endswith(".pdf"):
            raise ValueError("Arquivo deve ser PDF.")

        file_bytes = await file.read()
        if not file_bytes:
            raise ValueError("Arquivo vazio.")

        try:
            itens_raw: List[str] = extract_lines_from_pdf_bytes(file_bytes)
        except Exception as e:
            logger.exception("Erro extraindo PDF")
            raise RuntimeError(f"Erro extraindo PDF: {e}")

        if not itens_raw:
            raise ValueError("Nenhum item encontrado no PDF.")

        itens_format = format_many(itens_raw)
        rag_service = _get_or_create_rag(request, settings.ncm_csv_path)

        rows = []
        for it in itens_format:
            pn = it.get("partnumber", "")
            desc_raw = it.get("descricao_raw", "")
            scraper_info = find_manufacturer_and_location(pn)
            fabricante = scraper_info.get("fabricante", "Não encontrado")
            localizacao = scraper_info.get("localizacao", "Não encontrada")

            try:
                desc_norm = normalizar_com_ollama(desc_raw)
            except Exception as e:
                logger.warning("Fallback normalização: %s", e)
                desc_norm = desc_raw

            try:
                top_candidates = rag_service.find_top_ncm(desc_norm, top_k=settings.top_k)
                if not top_candidates:
                    raise ValueError("Nenhum candidato NCM")
            except Exception as e:
                logger.exception("Erro RAG")
                rows.append({
                    "partnumber": pn,
                    "fabricante": fabricante,
                    "localizacao": localizacao,
                    "ncm": "Erro RAG",
                    "descricao": desc_raw
                })
                continue

            try:
                ncm_final = choose_best_ncm(desc_norm, top_candidates)
            except Exception as e:
                logger.warning("Erro escolha LLM, usando top candidate: %s", e)
                ncm_final = top_candidates[0]["ncm"]

            descricao_final = next(
                (c.get("descricao_longa") or c.get("descricao", "") 
                 for c in top_candidates if c.get("ncm") == ncm_final),
                desc_norm
            )

            rows.append({
                "partnumber": pn,
                "fabricante": fabricante,
                "localizacao": localizacao,
                "ncm": ncm_final,
                "descricao": descricao_final
            })

        df_out = pd.DataFrame(rows, columns=["partnumber", "fabricante", "localizacao", "ncm", "descricao"])
        stream = io.BytesIO()
        with pd.ExcelWriter(stream, engine="openpyxl") as writer:
            df_out.to_excel(writer, index=False, sheet_name="resultado")
        stream.seek(0)

        filename = file.filename.rsplit(".", 1)[0] + "_classificado.xlsx"
        return stream, filename
