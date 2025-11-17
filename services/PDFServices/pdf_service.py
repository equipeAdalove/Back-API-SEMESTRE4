# services/PDFServices/pdf_service.py

import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import models
from schemas.pdf_schemas import ExtractionResponse
from services.PDFServices.pdf_workflow_service import (
    extract_from_pdf as extract_from_pdf_workflow,
)

logger = logging.getLogger(__name__)


async def extract_from_pdf(
    file: Any,
    db: Session,
    current_user: models.Usuario,
) -> ExtractionResponse:
    """
    Camada de serviço de alto nível para PDFs.

    Responsabilidades:
    - Validar se o arquivo é um PDF com nome válido;
    - Delegar para o pdf_workflow_service, que cuida de:
        * criar transação,
        * extrair itens,
        * montar o ExtractionResponse.
    """

    # Validação leve do arquivo (extensão + nome)
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie um arquivo PDF válido com nome.",
        )

    # Toda a lógica pesada fica no workflow
    try:
        return await extract_from_pdf_workflow(
            file=file,
            db=db,
            current_user=current_user,
        )
    except HTTPException:
        # Se o workflow já levantou HTTPException, só repassa
        raise
    except Exception as e:
        logger.exception("Erro inesperado no PDFService.extract_from_pdf")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar o PDF: {e}",
        )
