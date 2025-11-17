# routes/auth_routes.py
from fastapi import (
    APIRouter,
    Depends,
    status,
    BackgroundTasks,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import database
from schemas import user_schemas
from schemas.auth_schemas import (
    EmailSchema,
    VerifyTokenSchema,
    ResetPasswordSchema,
)
from services.AuthServices import auth_workflow_service
from models import models
from email_utils import send_recovery_email
from services.AuthServices import auth_service

router = APIRouter()


@router.post(
    "/auth/login",
    response_model=user_schemas.TokenResponse,
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    return auth_workflow_service.login(
        db=db,
        username=form_data.username,
        password=form_data.password,
    )


@router.get(
    "/user/profile",
    response_model=user_schemas.UserProfile,
)
async def read_users_me(
    current_user: models.Usuario = Depends(auth_service.get_current_user),
):
    return {"name": current_user.nome, "email": current_user.email}


@router.post("/auth/password-recovery")
async def password_recovery(
    data: EmailSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
):
    user = auth_workflow_service.init_password_recovery(
        db=db,
        email=data.email,
    )

    email_to = getattr(user, "email")
    code = getattr(user, "reset_token")

    background_tasks.add_task(
        send_recovery_email,
        email_to,
        code,
    )

    return {
        "message": "Código de verificação enviado para o seu e-mail.",
    }


@router.post("/auth/verify-token")
async def verify_token_route(
    data: VerifyTokenSchema,
    db: Session = Depends(database.get_db),
):
    return auth_workflow_service.verify_reset_token(
        db=db,
        email=data.email,
        token=data.token,
    )


@router.post("/auth/reset-password")
async def reset_password_route(
    data: ResetPasswordSchema,
    db: Session = Depends(database.get_db),
):
    return auth_workflow_service.reset_password(
        db=db,
        email=data.email,
        token=data.token,
        new_password=data.new_password,
    )
