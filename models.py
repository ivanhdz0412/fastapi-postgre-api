from pydantic import BaseModel
from datetime import datetime

#Modelos usados en la API
class InvoiceRequest(BaseModel):
    client_id: int
    month: int

class calcule(BaseModel):
    client_id: int
    month: int
    concepto: str
    valor: float

class InvoiceResponse(BaseModel):    
    consumption: float #EA - Energia activa
    injection: float   #EC - Comercialización de Excedentes de Energía
    excedente_1: float #EE1 - Excedentes de Energía tipo 1
    excedente_2: float #EE2 - Excedentes de Energía tipo 2
    total: float

class estadisticasCliente(BaseModel):
    client_id: int
    total_consumption: float
    total_injection: float

class CargaSistema(BaseModel):
    hour: datetime
    total_consumption: float

class CalculoConcepto(BaseModel):
    client_id: int
    month: int
    concepto: str