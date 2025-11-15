from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks # 1. Adicionado BackgroundTasks aqui
from sqlalchemy.orm import Session
from database import database, crud
from schemas import user_schemas
from email_utils import send_welcome_email # 2. Importe a função de email que criamos antes

router = APIRouter()

@router.post("/users", response_model=user_schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
    user: user_schemas.UserCreate, 
    background_tasks: BackgroundTasks, # 3. Adicionado este parâmetro para gerenciar tarefas em segundo plano
    db: Session = Depends(database.get_db)
):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_data_dict = {"name": user.name, "email": user.email, "password": user.password}

    print("--- DADOS RECEBIDOS NA ROTA DE CADASTRO ---")
    print(f"Nome recebido: {user.name}")
    print(f"Email recebido: {user.email}")
    # print(f"SENHA recebida: {user.password}") # Dica de segurança: Evite printar a senha real nos logs
    print("-----------------------------------------")
    
    # 4. Guardamos o usuário criado em uma variável primeiro
    new_user = crud.create_user(db=db, user_data=user_data_dict)

    # 5. Agendamos o envio do email (Isso acontece 'por fora', sem travar o retorno)
    background_tasks.add_task(send_welcome_email, new_user.email, new_user.nome)

    # 6. Retornamos o usuário criado
    return new_user