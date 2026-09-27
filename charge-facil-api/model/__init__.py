import os

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from model.base import Base
from model.estacao import Estacao
from model.powerbank import PowerBank
from model.aluguel import Aluguel, converter_alugueis_vencidos
from model.seed import popular_dados_iniciais

# SQLite file lives in ./database (created on first run)
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_URL = f"sqlite:///{os.path.join(DB_DIR, 'charge_facil.sqlite3')}"


@event.listens_for(Engine, "connect")
def _ativar_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores FK constraints (and ON DELETE) unless this pragma is on."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

# Demo data so the front-end has something to show on the first run
with Session() as _session:
    popular_dados_iniciais(_session)
