import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models import models

logger = logging.getLogger(__name__)


def get_or_create_fabricante(
    db: Session,
    nome: str,
    localizacao: Optional[str],
) -> models.Fabricante:
    """
    Cria ou retorna um Fabricante.

    - Garante nome seguro ("Não identificado" se vier vazio);
    - Atualiza endereço se o registro existente estiver sem endereço
      e for fornecida uma nova localização;
    - Em caso de criação, gera o ID manualmente com base em MAX(id) + 1
      para evitar conflito com seeds manuais.
    """
    safe_nome = nome.strip() if nome and nome.strip() else "Não identificado"

    # 1) Tenta encontrar fabricante existente pelo nome (razao_soc)
    db_fabricante = (
        db.query(models.Fabricante)
        .filter(models.Fabricante.razao_soc == safe_nome)
        .first()
    )

    if db_fabricante:
        endereco_atual = getattr(db_fabricante, "endereco", None)
        if not endereco_atual and localizacao:
            setattr(db_fabricante, "endereco", localizacao)
            try:
                db.commit()
                db.refresh(db_fabricante)
            except Exception:
                db.rollback()
                logger.exception(
                    "Erro ao atualizar endereço do fabricante '%s'",
                    safe_nome,
                )
        return db_fabricante

    # 2) Não existe -> vamos criar um novo, calculando o próximo ID manualmente
    try:
        max_id = db.query(func.max(models.Fabricante.id)).scalar()
        next_id = (max_id or 0) + 1
    except Exception:
        logger.exception(
            "Erro ao obter MAX(id) de Fabricante. Usando ID=1 como fallback."
        )
        next_id = 1

    db_fabricante = models.Fabricante(
        id=next_id,              # <-- ID definido manualmente
        razao_soc=safe_nome,
        endereco=localizacao,
        pais_origem=localizacao,
    )

    db.add(db_fabricante)

    try:
        db.commit()
        db.refresh(db_fabricante)
    except Exception:
        db.rollback()
        logger.exception("Erro ao criar fabricante '%s'", safe_nome)
        raise

    return db_fabricante
