"""Esquemas Pydantic para validación de entrada/salida de la API."""
from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    text: str = Field(
        default="",
        description="Texto del mensaje (SMS/correo) a clasificar como spam o ham.",
        examples=["Felicidades, ganaste un premio, reclama en http://bit.ly/premio"],
    )


class PredictResponse(BaseModel):
    label: str = Field(description="Clase predicha: 'spam' o 'ham'.")
    spam_probability: float = Field(description="Probabilidad estimada de que el texto sea spam (0-1).")
    ham_probability: float = Field(description="Probabilidad estimada de que el texto sea ham (0-1).")
    text_length: int = Field(description="Longitud (en caracteres) del texto recibido.")


class HealthResponse(BaseModel):
    # protected_namespaces=() evita el warning de pydantic por usar el
    # prefijo "model_" en nombres de campo (aquí es intencional y claro).
    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_loaded: bool
    model_version: str | None = None
