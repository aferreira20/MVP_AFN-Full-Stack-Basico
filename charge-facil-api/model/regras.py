"""Business rules shared by the models: pricing, deposit and battery simulation."""
import math
from datetime import datetime

# Status values (Portuguese, as exposed by the API)
DISPONIVEL = "disponível"
ALUGADO = "alugado"
MANUTENCAO = "manutenção"
VENDIDO = "vendido"
ESTOQUE = "em estoque"   # registered in the inventory, not allocated to any station

# Rental situations
ATIVO = "ativo"
DEVOLVIDO = "devolvido"

# Pricing table (BRL)
CARENCIA_MINUTOS = 5          # first minutes are free (grace period)
TARIFA_PRIMEIRA_HORA = 5.00   # first started hour
TARIFA_HORA_ADICIONAL = 3.00  # each additional started hour
TETO_DIARIO = 25.00           # max usage charge within the 24h window

# Deposit (franchise): held at pickup, becomes a sale if not returned in time
CAUCAO = 150.00
PRAZO_HORAS = 24

# Battery simulation (% per hour)
RECARGA_POR_HORA = 30         # while docked in a station
CONSUMO_POR_HORA = 20         # while rented (charging a phone)
NIVEL_MINIMO_ALUGUEL = 20     # below this a power bank cannot be rented


def minutos_entre(inicio: datetime, fim: datetime) -> int:
    """Whole minutes between two datetimes (never negative)."""
    return max(0, int((fim - inicio).total_seconds() // 60))


def calcular_valor(inicio: datetime, fim: datetime) -> float:
    """Usage price: grace period, per-started-hour rate, capped at TETO_DIARIO."""
    minutos = minutos_entre(inicio, fim)
    if minutos <= CARENCIA_MINUTOS:
        return 0.0
    horas = math.ceil(minutos / 60)
    return round(min(TETO_DIARIO, TARIFA_PRIMEIRA_HORA + TARIFA_HORA_ADICIONAL * (horas - 1)), 2)


def nivel_projetado(nivel: int, desde: datetime, status: str, agora: datetime = None) -> int:
    """Battery level now, based on the last stored level and the elapsed time."""
    agora = agora or datetime.now()
    horas = max(0.0, (agora - desde).total_seconds() / 3600)
    if status == DISPONIVEL:
        return min(100, int(nivel + horas * RECARGA_POR_HORA))
    if status == ALUGADO:
        return max(0, int(nivel - horas * CONSUMO_POR_HORA))
    return nivel  # maintenance, stock or sold: frozen
