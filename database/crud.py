from sqlalchemy.orm import Session
from models import models
from services.auth_service import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def create_user(db: Session, user_data: dict):
    hashed_password = get_password_hash(user_data['password'])
    db_user = models.Usuario(
        nome=user_data['name'],
        email=user_data['email'],
        senha=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user