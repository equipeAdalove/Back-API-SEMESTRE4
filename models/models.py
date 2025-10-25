from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, LargeBinary, func, Float
from sqlalchemy.orm import relationship
from database.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    senha = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    transacoes = relationship(
        "Transacao",
        back_populates="usuario",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )



class Fabricante(Base):
    __tablename__ = "fabricantes"

    id = Column(Integer, primary_key=True, index=True)
    razao_soc = Column(String(200), nullable=False)
    endereco = Column(String(200), nullable=True)
    pais_origem = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    itens = relationship(
        "Item",
        back_populates="fabricante",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )

class Item(Base):
    __tablename__ = "itens"

    partnumber = Column(String(25), primary_key=True, index=True)
    ncm = Column(String(8), index=True)
    descricao = Column(Text)
    descricao_curta = Column(String(255))
    fabricante_id = Column(Integer, ForeignKey("fabricantes.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    fabricante = relationship("Fabricante", back_populates="itens", lazy="selectin")
    transacoes = relationship(
        "TransacaoItem",
        back_populates="item",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )


class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    doc_entrada = Column(LargeBinary, nullable=True)
    doc_saida = Column(LargeBinary, nullable=True)
    data_upload = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    usuario = relationship("Usuario", back_populates="transacoes", lazy="selectin")
    itens = relationship(
        "TransacaoItem",
        back_populates="transacao",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )


# -----------------------------
# Tabela intermediária (N:N)
# -----------------------------
class TransacaoItem(Base):
    __tablename__ = "transacao_itens"

    id = Column(Integer, primary_key=True, index=True)
    transacao_id = Column(Integer, ForeignKey("transacoes.id", ondelete="CASCADE"), nullable=False, index=True)
    item_partnumber = Column(String(25), ForeignKey("itens.partnumber", ondelete="CASCADE"), nullable=False, index=True)
    quantidade = Column(Float, default=1)
    preco_extraido = Column(Float)
    data_extracao = Column(DateTime(timezone=True), server_default=func.now())

    transacao = relationship("Transacao", back_populates="itens", lazy="selectin")
    item = relationship("Item", back_populates="transacoes", lazy="selectin")