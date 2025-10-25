# Back-API-SEMESTRE4/database/crud.py

from sqlalchemy.orm import Session, joinedload
from models import models
# Importa do novo utilitário de senha
from services.password_utils import get_password_hash

# --- Funções de Usuário ---

def get_user_by_email(db: Session, email: str) -> models.Usuario | None:
    """Busca um usuário pelo email."""
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def create_user(db: Session, user_data: dict) -> models.Usuario:
    """Cria um novo usuário no banco de dados."""
    hashed_password = get_password_hash(user_data['password']) # Usa a função importada
    db_user = models.Usuario(
        nome=user_data['name'],
        email=user_data['email'],
        senha=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Funções de Fabricante e Item (Fase 1) ---

def get_or_create_fabricante(db: Session, nome: str, localizacao: str | None) -> models.Fabricante:
    """Busca um fabricante pelo nome ou o cria se não existir."""
    # Garante que o nome não seja None ou vazio para evitar erro no BD
    safe_nome = nome if nome and nome.strip() else "Não identificado"
    db_fabricante = db.query(models.Fabricante).filter(models.Fabricante.razao_soc == safe_nome).first()

    if db_fabricante:
        # Atualiza o endereço apenas se estiver vazio e uma nova localização for fornecida
        if not db_fabricante.endereco and localizacao:
            db_fabricante.endereco = localizacao
            # Aqui você pode adicionar lógica para extrair o país da localização se necessário
            # db_fabricante.pais_origem = extrair_pais(localizacao)
            db.commit()
            db.refresh(db_fabricante)
        return db_fabricante

    # Se não existir, cria um novo
    db_fabricante = models.Fabricante(
        razao_soc=safe_nome,
        endereco=localizacao,
        pais_origem=localizacao # Ajustar esta lógica se 'localizacao' for apenas cidade/país
    )
    db.add(db_fabricante)
    db.commit()
    db.refresh(db_fabricante)
    return db_fabricante

def upsert_item(db: Session, item_data: dict, fabricante_id: int | None) -> models.Item | None:
    """Cria um novo item ou atualiza um existente (baseado no partnumber)."""
    partnumber = item_data.get('partnumber')
    if not partnumber or not partnumber.strip(): # Validação mais robusta
      print(f"Tentativa de upsert de item sem partnumber válido: {item_data}")
      return None # Não prosseguir se não houver partnumber

    db_item = db.query(models.Item).filter(models.Item.partnumber == partnumber).first()

    # Pega os dados do dicionário, tratando caso alguma chave não exista
    ncm = item_data.get('ncm')
    descricao = item_data.get('descricao')
    descricao_raw = item_data.get('descricao_raw') # Pega a descrição raw

    if db_item:
        # UPDATE (Atualiza)
        print(f"Atualizando item: {partnumber}")
        db_item.ncm = ncm
        db_item.descricao = descricao
        db_item.descricao_curta = descricao_raw # Atualiza sempre que disponível
        db_item.fabricante_id = fabricante_id
    else:
        # INSERT (Cria)
        print(f"Criando novo item: {partnumber}")
        db_item = models.Item(
            partnumber=partnumber,
            ncm=ncm,
            descricao=descricao,
            descricao_curta=descricao_raw, # Salva a descrição raw na criação
            fabricante_id=fabricante_id
        )
        db.add(db_item)

    try:
        db.commit()
        db.refresh(db_item)
    except Exception as e:
        db.rollback() # Desfaz em caso de erro no commit
        print(f"Erro ao salvar/atualizar item {partnumber}: {e}") # Log do erro
        raise # Re-levanta a exceção para a rota tratar
    return db_item

def get_item_by_partnumber(db: Session, partnumber: str) -> models.Item | None:
    """Busca um item e seu fabricante associado pelo partnumber."""
    if not partnumber:
        return None
    # Usamos 'joinedload' para buscar o item E seu fabricante
    # em uma única consulta (evita N+1 queries) - Útil para Fase 2
    return db.query(models.Item)\
             .options(joinedload(models.Item.fabricante))\
             .filter(models.Item.partnumber == partnumber)\
             .first()


# --- Funções de Transação (Fase 1) ---

def create_transacao(db: Session, usuario_id: int, doc_entrada_bytes: bytes | None = None) -> models.Transacao:
    """Cria um registro de transação para um usuário."""
    db_transacao = models.Transacao(
        usuario_id=usuario_id,
        doc_entrada=doc_entrada_bytes, # Salva os bytes do PDF se fornecido
        doc_saida=None
    )
    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)
    return db_transacao

def link_item_to_transacao(db: Session, transacao_id: int, item_partnumber: str, quantidade: float = 1.0, preco: float | None = None) -> models.TransacaoItem | None:
    """Vincula um item (pelo partnumber) a uma transação."""
    if not item_partnumber: # Não criar link sem partnumber válido
        print(f"Tentativa de linkar item sem partnumber à transação {transacao_id}")
        return None

    # Opcional: Verificar se o item realmente existe antes de criar o link
    # item_existe = db.query(models.Item.partnumber).filter(models.Item.partnumber == item_partnumber).first()
    # if not item_existe:
    #    print(f"Item {item_partnumber} não encontrado para linkar à transação {transacao_id}")
    #    return None

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