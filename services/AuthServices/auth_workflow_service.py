# services/auth_workflow_service.py
from datetime import timedelta
import random
import string
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import models
from services.UserServices import user_service
from services.AuthServices import auth_service
from services.Utils.password_utils import verify_password, get_password_hash


def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def login(db: Session, username: str, password: str) -> dict:
    user = user_service.get_user_by_email(db, email=username)

    if not user or not verify_password(password, getattr(user, "senha")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail e/ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = auth_service.create_access_token(
        data={"sub": getattr(user, "email")},
        expires_delta=access_token_expires,
    )

    return {"data": {"access_token": access_token, "token_type": "bearer"}}


def init_password_recovery(db: Session, email: str) -> models.Usuario:
    user = user_service.get_user_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="E-mail não cadastrado.",
        )

    token = _generate_code()
    setattr(user, "reset_token", token)
    db.commit()
    db.refresh(user)

    return user


def verify_reset_token(
    db: Session,
    email: str,
    token: str,
) -> dict:
    user = user_service.get_user_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado.",
        )

    token_in_db: Any = getattr(user, "reset_token", None)

    if not isinstance(token_in_db, str) or not token_in_db or token_in_db != token:
        raise HTTPException(
            status_code=400,
            detail="Código inválido ou expirado.",
        )

    return {"message": "Código válido."}


def reset_password(
    db: Session,
    email: str,
    token: str,
    new_password: str,
) -> dict:
    user = user_service.get_user_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado.",
        )

    token_in_db: Any = getattr(user, "reset_token", None)
    if not isinstance(token_in_db, str) or token_in_db != token:
        raise HTTPException(
            status_code=400,
            detail="Token inválido. Reinicie o processo.",
        )

    hashed_password = get_password_hash(new_password)
    setattr(user, "senha", hashed_password)
    setattr(user, "reset_token", None)

    db.commit()

    return {"message": "Senha alterada com sucesso."}
