import logging
from typing import List, Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from models import models
from schemas.pdf_schemas import (
    ExcelRequest,
    FinalItem,
    TransacaoDetailResponse,
)
from services.FabricanteServices.fabricante_services import (
    get_or_create_fabricante,
)
from services.ItemServices.item_services import upsert_item
from sqlalchemy import func


logger = logging.getLogger(__name__)


def create_transaction(
    db: Session,
    usuario_id: int,
    nome: Optional[str] = None,
) -> models.Transacao:

    # Busca próximo ID livre (MAX + 1)
    next_id = db.query(func.coalesce(func.max(models.Transacao.id), 0) + 1).scalar()

    db_transacao = models.Transacao(
        id=next_id,          # força o ID
        usuario_id=usuario_id,
        nome=nome,
    )

    db.add(db_transacao)
    try:
        db.commit()
        db.refresh(db_transacao)
    except Exception:
        db.rollback()
        logger.exception("Erro ao criar transação para usuário %s", usuario_id)
        raise

    return db_transacao



def link_item_to_transacao(
    db: Session,
    transacao_id: int,
    item_partnumber: str,
    quantidade: float = 1.0,
    preco: float | None = None,
) -> Optional[models.TransacaoItem]:
    """
    Cria o vínculo TransacaoItem entre uma transação e um item.
    """
    if not item_partnumber:
        logger.warning(
            "Tentativa de linkar item sem partnumber à transação %s",
            transacao_id,
        )
        return None

    db_link = models.TransacaoItem(
        transacao_id=transacao_id,
        item_partnumber=item_partnumber,
        quantidade=quantidade,
        preco_extraido=preco,
    )
    db.add(db_link)
    try:
        db.commit()
        db.refresh(db_link)
    except Exception as e:
        db.rollback()
        logger.exception(
            "Erro ao linkar item %s à transação %s: %s",
            item_partnumber,
            transacao_id,
            e,
        )
        raise

    return db_link


def get_user_transactions(
    db: Session,
    current_user: models.Usuario,
):
    """
    Lista as transações do usuário (para response_model=List[TransacaoInfo]).
    """
    return (
        db.query(models.Transacao)
        .filter(models.Transacao.usuario_id == getattr(current_user, "id"))
        .order_by(models.Transacao.created_at.desc())
        .all()
    )


def get_transaction_details(
    transacao_id: int,
    db: Session,
    current_user: models.Usuario,
) -> TransacaoDetailResponse:
    """
    Retorna os detalhes de uma transação específica, incluindo itens
    e fabricantes, já no formato do schema TransacaoDetailResponse.
    """
    db_transacao = (
        db.query(models.Transacao)
        .options(
            joinedload(models.Transacao.itens)
            .joinedload(models.TransacaoItem.item)
            .joinedload(models.Item.fabricante)
        )
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

    processed_items_list: List[FinalItem] = []

    for transacao_item in db_transacao.itens:
        item = transacao_item.item
        if not item or not item.fabricante:
            continue

        fabricante_db = item.fabricante

        pn = getattr(item, "partnumber")
        ncm_db: Any = getattr(item, "ncm", None)
        descricao_db: Any = getattr(item, "descricao", None)
        descricao_curta_db: Any = getattr(item, "descricao_curta", None)
        fabricante_nome = getattr(fabricante_db, "razao_soc")
        fabricante_endereco = getattr(fabricante_db, "endereco") or "Não encontrada"

        processed_items_list.append(
            FinalItem(
                partnumber=pn,
                fabricante=fabricante_nome,
                localizacao=fabricante_endereco,
                ncm=ncm_db or "N/A",
                descricao=descricao_db or descricao_curta_db or "",
                is_new_manufacturer=False,
            )
        )

    transacao_id_value = int(getattr(db_transacao, "id"))

    return TransacaoDetailResponse(
        transacao_id=transacao_id_value,
        processed_items=processed_items_list,
        pending_items=[],  # hoje não usamos pendentes ao reabrir o histórico
    )


def rename_transaction(
    transacao_id: int,
    novo_nome: str,
    db: Session,
    current_user: models.Usuario,
) -> dict:
    if not novo_nome or not novo_nome.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O nome não pode estar vazio.",
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

    try:
        setattr(db_transacao, "nome", novo_nome)
        db.commit()
        return {"message": "Transação renomeada com sucesso."}
    except Exception as e:
        db.rollback()
        logger.exception("Erro ao renomear transação %s", transacao_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {e}",
        )


def delete_transaction(
    transacao_id: int,
    db: Session,
    current_user: models.Usuario,
) -> dict:
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

    try:
        db.delete(db_transacao)
        db.commit()
        return {"message": "Transação excluída com sucesso."}
    except Exception as e:
        db.rollback()
        logger.exception("Erro ao excluir transação %s", transacao_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {e}",
        )


def update_transaction_items(
    transacao_id: int,
    data: ExcelRequest,
    db: Session,
    current_user: models.Usuario,
) -> dict:
    """
    Atualiza/insere itens associados a uma transação com base no ExcelRequest.
    """
    if not data.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma item fornecido.",
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

    try:
        updated_items_count = 0

        for item_data in data.items:
            item_dict = item_data.model_dump()

            db_fabricante = get_or_create_fabricante(
                db=db,
                nome=item_dict.get("fabricante", "Não identificado"),
                localizacao=item_dict.get("localizacao", "Não encontrada"),
            )
            fabricante_id = int(getattr(db_fabricante, "id"))

            db_item = upsert_item(
                db=db,
                item_data=item_dict,
                fabricante_id=fabricante_id,
            )

            if db_item is not None:
                updated_items_count += 1

                partnumber_item = getattr(db_item, "partnumber")

                link = (
                    db.query(models.TransacaoItem)
                    .filter(
                        models.TransacaoItem.transacao_id == transacao_id,
                        models.TransacaoItem.item_partnumber
                        == str(partnumber_item),
                    )
                    .first()
                )

                if not link:
                    link_item_to_transacao(
                        db=db,
                        transacao_id=transacao_id,
                        item_partnumber=str(partnumber_item),
                    )

        return {
            "message": (
                f"{updated_items_count} itens atualizados com sucesso "
                f"na transação {transacao_id}."
            ),
        }

    except Exception as e:
        logger.exception("Erro ao atualizar itens no banco de dados")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao salvar: {e}",
        )
