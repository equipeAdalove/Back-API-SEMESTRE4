import logging
from typing import Optional

from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field, ValidationError

from models import models

logger = logging.getLogger(__name__)


class ItemUpsertData(BaseModel):
    """
    Schema de validação para upsert de Item.

    - partnumber é obrigatório e não pode ser vazio;
    - ncm, descricao e descricao_raw são opcionais.
    """
    partnumber: str = Field(..., min_length=1)
    ncm: Optional[str] = None
    descricao: Optional[str] = None
    descricao_raw: Optional[str] = None


def upsert_item(
    db: Session,
    item_data: dict,
    fabricante_id: Optional[int],
) -> Optional[models.Item]:
    """
    Cria ou atualiza um Item.

    - Valida o payload com ItemUpsertData;
    - Atualiza NCM/descrição/descrição_curta/fabricante_id se o item existir;
    - Cria um novo registro se não existir;
    - Usa setattr para evitar problemas de tipagem (Column vs valor).
    """
    try:
        payload = ItemUpsertData(**item_data)
    except ValidationError as e:
        logger.warning("Payload inválido para upsert_item: %s", e)
        return None

    partnumber = payload.partnumber.strip()
    if not partnumber:
        logger.warning(
            "Tentativa de upsert de item sem partnumber válido: %s",
            item_data,
        )
        return None

    db_item: Optional[models.Item] = (
        db.query(models.Item)
        .filter(models.Item.partnumber == partnumber)
        .first()
    )

    if db_item:
        logger.info("Atualizando item: %s", partnumber)
        setattr(db_item, "ncm", payload.ncm)
        setattr(db_item, "descricao", payload.descricao)
        setattr(db_item, "descricao_curta", payload.descricao_raw)
        if fabricante_id is not None:
            setattr(db_item, "fabricante_id", fabricante_id)
    else:
        logger.info("Criando novo item: %s", partnumber)
        db_item = models.Item(
            partnumber=partnumber,
            ncm=payload.ncm,
            descricao=payload.descricao,
            descricao_curta=payload.descricao_raw,
            fabricante_id=fabricante_id,
        )
        db.add(db_item)

    try:
        db.commit()
        db.refresh(db_item)
    except Exception as e:
        db.rollback()
        logger.exception(
            "Erro ao salvar/atualizar item %s: %s",
            partnumber,
            e,
        )
        raise

    return db_item


def get_item_by_partnumber(
    db: Session,
    partnumber: str,
) -> Optional[models.Item]:
    """
    Busca um Item por partnumber, já fazendo joinedload do Fabricante.
    """
    pn = (partnumber or "").strip()
    if not pn:
        return None

    return (
        db.query(models.Item)
        .options(joinedload(models.Item.fabricante))
        .filter(models.Item.partnumber == pn)
        .first()
    )
