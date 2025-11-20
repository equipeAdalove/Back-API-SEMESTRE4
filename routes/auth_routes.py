from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta
import random
import string

# Imports do projeto
from database import database, crud
from services import auth_service
from schemas import user_schemas
from models import models

# Utilitários de senha e email
from services.password_utils import verify_password, get_password_hash 
from email_utils import send_recovery_email

router = APIRouter()

# --- SCHEMAS (Modelos de dados) ---

class EmailSchema(BaseModel):
    email: EmailStr

class VerifyTokenSchema(BaseModel):
    email: EmailStr
    token: str

class ResetPasswordSchema(BaseModel):
    email: EmailStr
    token: str
    new_password: str

class UserChangePassword(BaseModel):
    current_password: str
    new_password: str


# --- FUNÇÕES AUXILIARES ---

def gerar_codigo(length=6):
    """Gera um código numérico de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=length))


# --- ROTAS DE AUTENTICAÇÃO E PERFIL ---

@router.post("/auth/login", response_model=user_schemas.TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)

    if not user or not verify_password(form_data.password, user.senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail e/ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"data": {"access_token": access_token, "token_type": "bearer"}}


@router.get("/user/profile", response_model=user_schemas.UserProfile)
async def read_users_me(current_user: models.Usuario = Depends(auth_service.get_current_user)):
    return {"name": current_user.nome, "email": current_user.email}


# --- NOVA ROTA: ATUALIZAR SENHA (LOGADO) ---

@router.put("/user/update-password")
async def update_user_password(
    data: UserChangePassword, 
    current_user: models.Usuario = Depends(auth_service.get_current_user), 
    db: Session = Depends(database.get_db)
):
    # 1. Verifica se a senha ATUAL enviada bate com a do banco
    if not verify_password(data.current_password, current_user.senha):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="A senha atual está incorreta."
        )
    
    # 2. Verifica se a nova senha é igual à antiga (opcional, mas recomendado)
    if verify_password(data.new_password, current_user.senha):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="A nova senha não pode ser igual à atual."
        )

    # 3. Criptografa a NOVA senha
    hashed_new_password = get_password_hash(data.new_password)
    
    # 4. Salva no banco
    current_user.senha = hashed_new_password
    db.commit()
    
    return {"message": "Senha atualizada com sucesso!"}


# --- ROTAS DE RECUPERAÇÃO DE SENHA (ESQUECI A SENHA) ---

@router.post("/auth/password-recovery")
async def password_recovery(data: EmailSchema, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    # 1. Busca usuário real no banco
    user = crud.get_user_by_email(db, email=data.email)
    
    if not user:
        # Retorna 404 ou 200 genérico para segurança (aqui mantive 404 conforme seu código original)
        raise HTTPException(status_code=404, detail="E-mail não cadastrado.")

    # 2. Gera token e salva no banco
    token = gerar_codigo()
    user.reset_token = token
    db.commit()
    db.refresh(user)

    # 3. Envia email em background
    background_tasks.add_task(send_recovery_email, user.email, token)

    return {"message": "Código de verificação enviado para o seu e-mail."}


@router.post("/auth/verify-token")
async def verify_token_route(data: VerifyTokenSchema, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, email=data.email)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # 4. Verifica se o token do banco bate com o token enviado
    if not user.reset_token or user.reset_token != data.token:
        raise HTTPException(status_code=400, detail="Código inválido ou expirado.")
    
    return {"message": "Código válido."}


@router.post("/auth/reset-password")
async def reset_password_route(data: ResetPasswordSchema, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, email=data.email)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # 5. Verificação dupla de segurança
    if not user.reset_token or user.reset_token != data.token:
        raise HTTPException(status_code=400, detail="Token inválido. Reinicie o processo.")
    
    # 6. Criptografa a nova senha
    hashed_password = get_password_hash(data.new_password)
    
    # 7. Atualiza no banco e limpa o token
    user.senha = hashed_password
    user.reset_token = None 
    db.commit()
    
    return {"message": "Senha alterada com sucesso."}