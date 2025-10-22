from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import database, crud
from schemas import user_schemas

router = APIRouter()

@router.post("/users", response_model=user_schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: user_schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_data_dict = {"name": user.name, "email": user.email, "password": user.password}

    print("--- DADOS RECEBIDOS NA ROTA DE CADASTRO ---")
    print(f"Nome recebido: {user.name}")
    print(f"Email recebido: {user.email}")
    print(f"SENHA recebida: {user.password}")
    print(f"Tamanho da senha: {len(str(user.password))}")
    print("-----------------------------------------")
    
    return crud.create_user(db=db, user_data=user_data_dict)