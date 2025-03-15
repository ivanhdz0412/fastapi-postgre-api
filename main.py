from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

# Importar configuración de la base de datos desde config.py
from config import SessionLocal, Base

# Dependencias de otros archivos
from models import *
from funciones import *

#conexion activa a base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Inicializar la aplicación FastAPI
app = FastAPI()

#Endpoint principal
@app.get("/")
def root():
    return {"message": "API para consultar datos de consumo e información de clientes"}

#Endpoint que calcula la factura para un cliente y un mes específico
@app.post("/calculate-invoice", response_model=InvoiceResponse)
def calculate_invoice(request: InvoiceRequest,db: Session = Depends(get_db)):
  
    year = 2023 #unico año usado en base de datos
    cliente = request.client_id
    month = request.month

    if not(month>0 and month<=12):        
        raise HTTPException(
            status_code=400,  # Bad Request
            detail="Fecha inválida. El mes debe estar entre 1 y 12"
        )

    try:
        consumo = calculo_consumo(db,cliente,year,month)
        inyeccion = calculo_inyeccion(db,cliente,year,month)
        energia_e1 = energia_excedente_1(db,cliente,year,month)
        energia_e2 = energia_excedente_2(db,cliente,year,month)
        #energia_e2=0
        
        return InvoiceResponse( 
            consumption = consumo,
            injection = inyeccion,
            excedente_1 = energia_e1,
            excedente_2 = energia_e2,
            total = consumo+inyeccion+energia_e1+energia_e2
        )
    except HTTPException as e:
        print(f"Error: {e}")  # Log del error
        raise e

#Endpoint que proporciona estadísticas de consumo e inyección para un cliente
@app.get("/client-statistics/{client_id}", response_model=estadisticasCliente)
def get_client_statistics(client_id: int, db: Session = Depends(get_db)):

    total_consumo, total_inyeccion = consumo_inyeccion(db,client_id)
    
    return estadisticasCliente( 
        client_id=client_id,
        total_consumption=total_consumo,
        total_injection=total_inyeccion
    )

#Endpoint que muestra la carga del sistema por hora basada en los datos de consumo
@app.get("/system-load", response_model=list[CargaSistema])
def get_system_load(db: Session = Depends(get_db)):
    hourly_load = sistema_carga(db)
    return [CargaSistema(hour=hour, total_consumption=total) for hour, total in hourly_load.items()]

#Endpoint para el cálculo independiente de cada concepto
@app.post("/calculate-concept", response_model=calcule)
def calculate_concept(request: CalculoConcepto,db: Session = Depends(get_db)):
    
    year = 2023 #unico año usado en base de datos
    cliente = request.client_id
    month = request.month
    concepto = request.concepto

    # Diccionario que mapea las entradas a las funciones
    funciones = {
        "ea": calculo_consumo,
        "ec": calculo_inyeccion,
        "ee1": energia_excedente_1,
        "ee2": energia_excedente_2,
    }

    definiciones = {
        "ea": "Energía activa o cantidad de consumption",
        "ec": "Energía comercializada por excedentes o cantidad de injection",
        "ee1": "Excedentes de Energía tipo 1",
        "ee2": "Excedentes de Energía tipo 2",
    }
    if not(month>0 and month<=12):        
        raise HTTPException(
            status_code=400,  # Bad Request
            detail="Fecha inválida. El mes debe estar entre 1 y 12"
    )

    entrada = concepto.lower()
    # Verificar si el concepto es válido
    if entrada in funciones:
        try:
            valor = funciones[entrada](db,cliente,year,month)            

            return calcule( 
                client_id = cliente,
                month = month,
                concepto= definiciones[entrada],
                valor = valor
            )

        except HTTPException as e:
            print(f"Error: {e}")  
            raise e        
    else:
        print(f"Entrada no válida: {entrada}. Prueba con entradas como: {list(funciones.keys())}")
        
        raise HTTPException(
            status_code=400,  # Bad Request
            detail=f"Concepto no válido: {entrada}. Prueba con: {list(funciones.keys())}"
        )
