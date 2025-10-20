from sqlalchemy import Column, Integer, String, CHAR, Text, ForeignKey, DateTime, LargeBinary, func
from sqlalchemy.orm import relationship
from database.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha = Column(CHAR(60), nullable=False)
    role = Column(CHAR(1), nullable=False, default='U')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    transacoes = relationship("Transacao", back_populates="usuario")


class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    doc_entrada = Column(LargeBinary, nullable=False)
    doc_saida = Column(LargeBinary)
    data_upload = Column(DateTime(timezone=True), server_default=func.now())
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    usuario = relationship("Usuario", back_populates="transacoes")
    itens = relationship("Item", back_populates="transacao")
    fabricantes = relationship("Fabricante", back_populates="transacao")


class Item(Base):
    __tablename__ = "itens"

    partnumber = Column(String(25), primary_key=True, index=True)
    ncm = Column(String(8))
    descricao = Column(Text)
    transacao_id = Column(Integer, ForeignKey("transacoes.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    transacao = relationship("Transacao", back_populates="itens")
    fabricantes = relationship("Fabricante", back_populates="item")


class Fabricante(Base):
    __tablename__ = "fabricantes"

    id = Column(Integer, primary_key=True, index=True)
    razao_soc = Column(String(200), nullable=False)
    endereco = Column(String(100))
    pais_origem = Column(String(100))
    transacao_id = Column(Integer, ForeignKey("transacoes.id", ondelete="CASCADE"), nullable=False)
    item_partn = Column(String(25), ForeignKey("itens.partnumber", ondelete="CASCADE"), nullable=False)

    transacao = relationship("Transacao", back_populates="fabricantes")
    item = relationship("Item", back_populates="fabricantes")
