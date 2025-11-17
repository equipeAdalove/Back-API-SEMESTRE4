# routes/user_routes.py
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
)
from sqlalchemy.orm import Session

from database import database
from schemas import user_schemas
from services.UserServices import user_service
from email_utils import send_welcome_email
from models import models

router = APIRouter()


@router.post(
    "/users",
    response_model=user_schemas.User,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: user_schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    # Verifica se já existe usuário com esse e-mail
    db_user = user_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Delega criação para o service
    new_user: models.Usuario = user_service.create_user(
        db=db,
        user_data=user,
    )

    # Dispara e-mail de boas-vindas em background
    email_to = getattr(new_user, "email")
    nome_to = getattr(new_user, "nome")

    background_tasks.add_task(
        send_welcome_email,
        email_to,
        nome_to,
    )

    return new_user
