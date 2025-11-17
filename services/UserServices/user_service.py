# services/UserServices/user_service.py
from typing import Dict, Any

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from models import models
from schemas import user_schemas
from services.Utils.password_utils import get_password_hash


def get_user_by_email(db: Session, email: str) -> models.Usuario | None:
    if not email:
        return None

    return (
        db.query(models.Usuario)
        .filter(models.Usuario.email == email)
        .first()
    )


def _sync_usuarios_id_sequence(db: Session) -> None:
    """
    Garante que a sequence de ID da tabela 'usuarios' esteja
    alinhada com o maior ID atual.

    Isso resolve o erro de:
    ERRO: duplicar valor da chave viola a restrição de unicidade "usuarios_pkey"
    """
    max_id = db.query(func.max(models.Usuario.id)).scalar()

    # Se não houver nenhum usuário ainda, não há o que sincronizar
    if max_id is None:
        return

    # Ajusta a sequence para MAX(id)
    # Próximo INSERT usará MAX(id) + 1
    db.execute(
        text(
            """
            SELECT setval(
                pg_get_serial_sequence('usuarios', 'id'),
                :new_value,
                true
            )
            """
        ),
        {"new_value": max_id},
    )


def create_user(
    db: Session,
    user_data: Dict[str, Any] | user_schemas.UserCreate,
) -> models.Usuario:
    """
    Cria um novo usuário no banco:
    - Sincroniza a sequence de ID (caso tenha seed manual);
    - Faz o hash da senha;
    - Insere o registro.
    """

    if isinstance(user_data, user_schemas.UserCreate):
        name = user_data.name
        email = user_data.email
        password = user_data.password
    else:
        name = str(user_data.get("name", "")).strip()
        email = str(user_data.get("email", "")).strip()
        password = str(user_data.get("password", ""))

    if not name or not email or not password:
        raise ValueError("Nome, e-mail e senha são obrigatórios para criar usuário.")

    # Garante que a sequence de ID não vá colidir com seeds manuais
    _sync_usuarios_id_sequence(db)

    hashed_password = get_password_hash(password)

    new_user = models.Usuario(
        nome=name,
        email=email,
        senha=hashed_password,
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    return new_user
