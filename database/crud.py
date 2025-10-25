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

def get_or_create_fabricante(db: Session, nome: str, localizacao: str):
    db_fabricante = db.query(models.Fabricante).filter(models.Fabricante.razao_soc == nome).first()
    if db_fabricante:
        if not db_fabricante.endereco and localizacao:
            db_fabricante.endereco = localizacao 
            db.commit()
            db.refresh(db_fabricante)
        return db_fabricante
    
    db_fabricante = models.Fabricante(
        razao_soc=nome,
        endereco=localizacao,
        pais_origem=localizacao 
    )
    db.add(db_fabricante)
    db.commit()
    db.refresh(db_fabricante)
    return db_fabricante

def upsert_item(db: Session, item_data: dict, fabricante_id: int):
    partnumber = item_data['partnumber']
    
    db_item = db.query(models.Item).filter(models.Item.partnumber == partnumber).first()
    
    if db_item:
        db_item.ncm = item_data['ncm']
        db_item.descricao = item_data['descricao']
        db_item.descricao_curta = item_data['descricao_raw']
        db_item.fabricante_id = fabricante_id
    else:
        db_item = models.Item(
            partnumber=partnumber,
            ncm=item_data['ncm'],
            descricao=item_data['descricao'],
            fabricante_id=fabricante_id
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_item)
    return db_item

def create_transacao(db: Session, usuario_id: int):
    db_transacao = models.Transacao(
        usuario_id=usuario_id,
        doc_entrada=None, 
        doc_saida=None
    )
    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)
    return db_transacao

def link_item_to_transacao(db: Session, transacao_id: int, item_partnumber: str):
    db_link = models.TransacaoItem(
        transacao_id=transacao_id,
        item_partnumber=item_partnumber,
        quantidade=1 
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link