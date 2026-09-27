from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from model.base import Base
from model.regras import (ATIVO, CAUCAO, DEVOLVIDO, DISPONIVEL, PRAZO_HORAS, VENDIDO,
                          calcular_valor, minutos_entre)


class Aluguel(Base):
    """A rental: taken from one station, returned to any station within 24h.

    A R$ 150 deposit is held at pickup. On return, only the usage is charged and
    the difference is refunded. If the deadline passes, the deposit is kept and
    the power bank is considered sold to the customer.
    """

    __tablename__ = "aluguel"

    id = Column(Integer, primary_key=True)
    cliente_nome = Column(String(80), nullable=False)
    cliente_telefone = Column(String(20), nullable=False)
    powerbank_id = Column(Integer, ForeignKey("powerbank.id", ondelete="SET NULL"), nullable=True)
    estacao_retirada_id = Column(Integer, ForeignKey("estacao.id", ondelete="SET NULL"), nullable=True)
    estacao_devolucao_id = Column(Integer, ForeignKey("estacao.id", ondelete="SET NULL"), nullable=True)
    situacao = Column(String(20), nullable=False, default=ATIVO)
    inicio = Column(DateTime, nullable=False, default=datetime.now)
    prazo = Column(DateTime, nullable=False)
    fim = Column(DateTime, nullable=True)
    caucao = Column(Float, nullable=False, default=CAUCAO)
    valor = Column(Float, nullable=True)     # amount actually charged
    estorno = Column(Float, nullable=True)   # deposit refunded to the customer
    # Snapshots keep the history readable even if a station/power bank is deleted later
    powerbank_codigo = Column(String(20), nullable=False)
    retirada_nome = Column(String(80), nullable=False)
    devolucao_nome = Column(String(80), nullable=True)

    powerbank = relationship("PowerBank", back_populates="alugueis")
    estacao_retirada = relationship("Estacao", foreign_keys=[estacao_retirada_id])
    estacao_devolucao = relationship("Estacao", foreign_keys=[estacao_devolucao_id])

    def __init__(self, cliente_nome, cliente_telefone, powerbank, estacao_retirada, inicio=None):
        self.cliente_nome = cliente_nome
        self.cliente_telefone = cliente_telefone
        self.powerbank = powerbank
        self.powerbank_codigo = powerbank.codigo
        self.estacao_retirada = estacao_retirada
        self.retirada_nome = estacao_retirada.nome
        self.inicio = inicio or datetime.now()
        self.prazo = self.inicio + timedelta(hours=PRAZO_HORAS)
        self.situacao = ATIVO
        self.caucao = CAUCAO

    @property
    def ativo(self) -> bool:
        return self.situacao == ATIVO

    @property
    def duracao_minutos(self) -> int:
        return minutos_entre(self.inicio, self.fim or datetime.now())

    @property
    def minutos_restantes(self):
        """Minutes left before the deposit turns into a sale (only while active)."""
        if not self.ativo:
            return None
        return minutos_entre(datetime.now(), self.prazo)

    @property
    def valor_atual(self) -> float:
        """Final charge if closed, otherwise the usage accrued so far."""
        if self.valor is not None:
            return self.valor
        return calcular_valor(self.inicio, datetime.now())

    def finalizar(self, estacao_devolucao, momento: datetime = None):
        """Return in time: charge usage only and refund the rest of the deposit."""
        self.fim = momento or datetime.now()
        self.situacao = DEVOLVIDO
        self.estacao_devolucao = estacao_devolucao
        self.devolucao_nome = estacao_devolucao.nome
        self.valor = calcular_valor(self.inicio, self.fim)
        self.estorno = round(self.caucao - self.valor, 2)
        if self.powerbank:
            self.powerbank.mudar_status(DISPONIVEL, self.fim)
            self.powerbank.estacao = estacao_devolucao

    def converter_em_venda(self):
        """Deadline expired: keep the whole deposit and mark the power bank as sold."""
        self.fim = self.prazo
        self.situacao = VENDIDO
        self.valor = self.caucao
        self.estorno = 0.0
        if self.powerbank:
            self.powerbank.mudar_status(VENDIDO, self.prazo)
            self.powerbank.estacao = None


def converter_alugueis_vencidos(session, agora: datetime = None) -> int:
    """Turn every active rental past its deadline into a sale. Returns how many changed."""
    agora = agora or datetime.now()
    vencidos = session.query(Aluguel).filter(Aluguel.situacao == ATIVO, Aluguel.prazo <= agora).all()
    for aluguel in vencidos:
        aluguel.converter_em_venda()
    if vencidos:
        session.commit()
    return len(vencidos)
