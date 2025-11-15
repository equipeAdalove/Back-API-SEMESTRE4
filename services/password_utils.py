from passlib.context import CryptContext

# Define o contexto de criptografia
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verifica se a senha em texto plano bate com a senha 'hasheada' no banco."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Gera o hash de uma senha em texto plano."""
    return pwd_context.hash(password)