from sqlalchemy.orm import Session, joinedload
from models import models
from services.password_utils import get_password_hash

# --- Funções de Usuário ---

def get_user_by_email(db: Session, email: str) -> models.Usuario | None:
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def create_user(db: Session, user_data: dict) -> models.Usuario:
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

# --- Funções de Fabricante e Item  ---

def get_or_create_fabricante(db: Session, nome: str, localizacao: str | None) -> models.Fabricante:
    safe_nome = nome if nome and nome.strip() else "Não identificado"
    db_fabricante = db.query(models.Fabricante).filter(models.Fabricante.razao_soc == safe_nome).first()

    if db_fabricante:
        if not db_fabricante.endereco and localizacao:
            db_fabricante.endereco = localizacao
            db.commit()
            db.refresh(db_fabricante)
        return db_fabricante

    db_fabricante = models.Fabricante(
        razao_soc=safe_nome,
        endereco=localizacao,
        pais_origem=localizacao 
    )
    db.add(db_fabricante)
    db.commit()
    db.refresh(db_fabricante)
    return db_fabricante

def upsert_item(db: Session, item_data: dict, fabricante_id: int | None) -> models.Item | None:
    partnumber = item_data.get('partnumber')
    if not partnumber or not partnumber.strip(): 
        print(f"Tentativa de upsert de item sem partnumber válido: {item_data}")
        return None 

    db_item = db.query(models.Item).filter(models.Item.partnumber == partnumber).first()
    ncm = item_data.get('ncm')
    descricao = item_data.get('descricao')
    descricao_raw = item_data.get('descricao_raw') 

    if db_item:
        print(f"Atualizando item: {partnumber}")
        db_item.ncm = ncm
        db_item.descricao = descricao
        db_item.descricao_curta = descricao_raw 
        db_item.fabricante_id = fabricante_id
    else:
        print(f"Criando novo item: {partnumber}")
        db_item = models.Item(
            partnumber=partnumber,
            ncm=ncm,
            descricao=descricao,
            descricao_curta=descricao_raw, 
            fabricante_id=fabricante_id
        )
        db.add(db_item)

    try:
        db.commit()
        db.refresh(db_item)
    except Exception as e:
        db.rollback() 
        print(f"Erro ao salvar/atualizar item {partnumber}: {e}") 
        raise 
    return db_item

def get_item_by_partnumber(db: Session, partnumber: str) -> models.Item | None:
    if not partnumber:
        return None
    return db.query(models.Item)\
            .options(joinedload(models.Item.fabricante))\
            .filter(models.Item.partnumber == partnumber)\
            .first()


# --- Funções de Transação  ---

def create_transacao(db: Session, usuario_id: int) -> models.Transacao:
    db_transacao = models.Transacao(
        usuario_id=usuario_id,
    )
    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)
    return db_transacao

def link_item_to_transacao(db: Session, transacao_id: int, item_partnumber: str, quantidade: float = 1.0, preco: float | None = None) -> models.TransacaoItem | None:
    if not item_partnumber: 
        print(f"Tentativa de linkar item sem partnumber à transação {transacao_id}")
        return None
    db_link = models.TransacaoItem(
        transacao_id=transacao_id,
        item_partnumber=item_partnumber,
        quantidade=quantidade,
        preco_extraido=preco
    )
    db.add(db_link)
    try:
        db.commit()
        db.refresh(db_link)
    except Exception as e:
        db.rollback()
        print(f"Erro ao linkar item {item_partnumber} à transação {transacao_id}: {e}")
        raise
    return db_link