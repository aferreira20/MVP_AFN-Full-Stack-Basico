from pydantic import BaseModel, Field


class ErroSchema(BaseModel):
    """Error payload returned by every route."""
    mensagem: str = Field(..., examples=["Estação não encontrada"])
