from typing import List

from fastapi import (
    APIRouter,
    Request,
    UploadFile,
    File,
    Depends,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from database import database
from models import models
from schemas.pdf_schemas import (
    ExtractionResponse,
    ProcessRequest,
    FinalItem,
    ExcelRequest,
    TransacaoInfo,
    RenameRequest,
    TransacaoDetailResponse,
)
from services.AuthServices.auth_service import get_current_user
from services.AuthServices import auth_service
from services.PDFServices.pdf_workflow_service import (
    extract_from_pdf as extract_from_pdf_service,
    process_items as process_items_service,
    generate_excel_response,
)
from services.TransactionServices.transactions_services import (
    update_transaction_items as update_transaction_items_service,
    get_user_transactions as get_user_transactions_service,
    get_transaction_details as get_transaction_details_service,
    rename_transaction as rename_transaction_service,
    delete_transaction as delete_transaction_service,
)
from services.PDFServices.rag_service import _get_or_create_rag

router = APIRouter()


@router.post(
    "/extract_from_pdf",
    response_model=ExtractionResponse,   # <-- CORRETO
    status_code=status.HTTP_200_OK,
)
async def extract_from_pdf(
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    """
    Inicia o fluxo: cria transação + extrai itens do PDF.
    Retorna: transacao_id + lista de itens extraídos.
    """
    return await extract_from_pdf_service(
        file=file,
        db=db,
        current_user=current_user,
    )

@router.post(
    "/process_items/{transacao_id}",
    response_model=List[FinalItem],
    status_code=status.HTTP_200_OK,
)
async def process_items(
    transacao_id: int,
    data: ProcessRequest,
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    rag_service = _get_or_create_rag(request, settings.ncm_csv_path)

    processed_rows = await process_items_service(
        transacao_id=transacao_id,
        itens_validados=data.items,
        db=db,
        current_user=current_user,
        rag_service=rag_service,
    )

    return JSONResponse(content=processed_rows)


@router.post("/generate_excel", status_code=status.HTTP_200_OK)
async def generate_excel(
    data: ExcelRequest,
    current_user: models.Usuario = Depends(get_current_user),
):
    return generate_excel_response(data)


@router.put(
    "/update_transaction/{transacao_id}",
    status_code=status.HTTP_200_OK,
)
async def update_transaction_items(
    transacao_id: int,
    data: ExcelRequest,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth_service.get_current_user),
):
    return update_transaction_items_service(
        transacao_id=transacao_id,
        data=data,
        db=db,
        current_user=current_user,
    )


@router.get(
    "/transacoes",
    response_model=List[TransacaoInfo],
    status_code=status.HTTP_200_OK,
)
async def get_user_transactions(
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth_service.get_current_user),
):
    return get_user_transactions_service(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/transacao/{transacao_id}",
    response_model=TransacaoDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_transaction_details(
    transacao_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth_service.get_current_user),
):
    return get_transaction_details_service(
        transacao_id=transacao_id,
        db=db,
        current_user=current_user,
    )


@router.put(
    "/transacao/{transacao_id}/rename",
    status_code=status.HTTP_200_OK,
)
async def rename_transaction(
    transacao_id: int,
    data: RenameRequest,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth_service.get_current_user),
):
    return rename_transaction_service(
        transacao_id=transacao_id,
        novo_nome=data.nome,
        db=db,
        current_user=current_user,
    )


@router.delete(
    "/transacao/{transacao_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_transaction(
    transacao_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth_service.get_current_user),
):
    return delete_transaction_service(
        transacao_id=transacao_id,
        db=db,
        current_user=current_user,
    )
