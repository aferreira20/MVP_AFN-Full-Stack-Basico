from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from model.base import Base
from model.regras import DISPONIVEL, ESTOQUE, NIVEL_MINIMO_ALUGUEL, VENDIDO, nivel_projetado


class PowerBank(Base):
    """A portable battery. In stock, rented or sold it has no station (estacao_id is NULL)."""

    __tablename__ = "powerbank"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    capacidade_mah = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default=DISPONIVEL)
    nivel_bateria = Column(Integer, nullable=False, default=100)
    nivel_atualizado_em = Column(DateTime, nullable=False, default=datetime.now)
    estacao_id = Column(Integer, ForeignKey("estacao.id"), nullable=True)
    cadastrado_em = Column(DateTime, nullable=False, default=datetime.now)

    estacao = relationship("Estacao", back_populates="powerbanks")
    alugueis = relationship("Aluguel", back_populates="powerbank")

    def __init__(self, codigo, capacidade_mah, estacao_id=None, nivel_bateria=100,
                 status=ESTOQUE, nivel_atualizado_em=None):
        self.codigo = codigo
        self.capacidade_mah = capacidade_mah
        self.estacao_id = estacao_id
        self.nivel_bateria = nivel_bateria
        self.status = status
        self.nivel_atualizado_em = nivel_atualizado_em or datetime.now()
        self.cadastrado_em = datetime.now()

    @property
    def nivel_atual(self) -> int:
        """Current battery level, simulating charge/discharge since last update."""
        return nivel_projetado(self.nivel_bateria, self.nivel_atualizado_em, self.status)

    @property
    def pronto_para_aluguel(self) -> bool:
        return self.status == DISPONIVEL and self.nivel_atual >= NIVEL_MINIMO_ALUGUEL

    @property
    def venda(self):
        """The rental that turned this power bank into a sale, if any."""
        if self.status != VENDIDO:
            return None
        return next((a for a in self.alugueis if a.situacao == VENDIDO), None)

    def mudar_status(self, novo_status: str, momento: datetime = None):
        """Freeze the simulated level before switching status, so the curve stays continuous."""
        momento = momento or datetime.now()
        self.nivel_bateria = nivel_projetado(self.nivel_bateria, self.nivel_atualizado_em,
                                             self.status, momento)
        self.nivel_atualizado_em = momento
        self.status = novo_status
