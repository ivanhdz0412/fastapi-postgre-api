from sqlalchemy import and_
from sqlalchemy.orm import Session
from fastapi import HTTPException
from collections import defaultdict
from datetime import datetime, timedelta
#Dependencias de otros archivos
from database import CLASES_TABLAS, SERVICIOS, TIEMPOS, REGISTROS, CONSUMOS, INYECCION, TARIFAS

#Funcion usada para estadísticas de consumo e inyección para un cliente
def consumo_inyeccion(db: Session, ID_service: int) -> float:

    #Obtener los registros asociados al id_service (id de cliente)
    registros = db.query(REGISTROS)\
        .filter(REGISTROS.id_service == ID_service)\
        .all()
    
    # Validación: Si no hay registros, lanzar una excepción 404
    if not registros:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron registros para el cliente con ID {ID_service}"
        )
    
    #Inicializo variables
    total_consumo = 0.0
    total_inyeccion = 0.0
    
    # Calcular el consumo y la inyección
    for registro in registros:        
        consumo = db.query(CONSUMOS)\
            .filter(CONSUMOS.id_record == registro.id_record)\
            .first()
        if consumo:
            total_consumo += consumo.value  # Sumar el consumo al total

        inyeccion = db.query(INYECCION)\
            .filter(INYECCION.id_record == registro.id_record)\
            .first()
        if inyeccion:
            total_inyeccion += inyeccion.value  # Sumar la inyección al total
            
    return total_consumo, total_inyeccion

#Funcion usada para mostrar la carga del sistema por horas
def sistema_carga(db: Session):
    #Defino variables para almacenar datos
    carga =  defaultdict(float)

    # Consulta con JOIN entre REGISTROS y CONSUMOS
    query = db.query(
        REGISTROS.record_timestamp,        
        CONSUMOS.value
    )\
    .join(CONSUMOS, REGISTROS.id_record == CONSUMOS.id_record)\
    .yield_per(1000)  # Carga los registros en lotes

    # Procesamiento de datos
    for timestamp, value in query:
        # Sumar el valor al timestamp correspondiente
        if value is not None:
            carga[timestamp] += value

    return carga

#Funcion usada para calculo ya sea de consumo o inyeccion
def suma_valores(db: Session,ID_service: int, year: int, month: int, TABLA: str ):

    tabla = CLASES_TABLAS.get(TABLA)
    if not tabla:
        raise ValueError(f"Clase '{TABLA}' no encontrada")
    
    cliente_existe = db.query(REGISTROS.id_service)\
    .filter(REGISTROS.id_service == ID_service)\
    .first()
    #Verificar el cliente
    if not cliente_existe:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el cliente con ID {ID_service}"
        )

    #Inicializacion de variables
    batch_size = 1000
    registros =  defaultdict(float)

    # Convertir el año y mes a fechas
    fecha_inicio = datetime(year, month, 1)  # Primer día del mes a las 00:00:00
    if month == 12:
        siguiente_mes = datetime(year + 1, 1, 1)  # Primer día del siguiente año
    else:
        siguiente_mes = datetime(year, month + 1, 1)  # Primer día del siguiente mes

    # Último día del mes actual
    fecha_fin = siguiente_mes - timedelta(hours=1)
    
    # Ejecutar la consulta 
    registros = db.query(
        REGISTROS.id_service,
        REGISTROS.record_timestamp,
        tabla.value
    )\
    .filter(REGISTROS.id_service == ID_service)\
    .filter(REGISTROS.record_timestamp.between(fecha_inicio, fecha_fin))\
    .join(tabla, REGISTROS.id_record == tabla.id_record)\
    .yield_per(batch_size)

    # Verificar si hay registros
    datos = registros.first()
    if not datos:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron registros para el mes {month}"
        )
    
    sumatoria = 0.0
    # Procesar cada lote
    for valores in registros:
        # Sumar el valor al timestamp correspondiente
        if valores is not None:
            sumatoria += valores.value

    return sumatoria

#Funcion usada para buscar la tarifa en tariffs
def buscar_tarifa(db: Session,ID_service: int) -> float:
    #tipo = CLASES_TABLAS.get(TIPO)
    #Buscar tarifa
    busqueda = db.query(SERVICIOS)\
    .filter(SERVICIOS.id_service == ID_service)\
    .first()

    # Paso 2: Obtener los valores de id_market, voltage_level y cdi
    id_market = busqueda.id_market
    voltage_level = busqueda.voltage_level
    cdi = busqueda.cdi

    if voltage_level > 1:
        #Ignorar cdi
        tarifa = db.query(TARIFAS)\
            .filter(
                and_(
                    TARIFAS.id_market == id_market,
                    TARIFAS.voltage_level == voltage_level
                )
            )\
            .first()
    else:
        #Incluir cdi en la búsqueda
        tarifa = db.query(TARIFAS)\
            .filter(
                and_(
                    TARIFAS.id_market == id_market,
                    TARIFAS.voltage_level == voltage_level,
                    TARIFAS.cdi == cdi
                )
            )\
            .first()
    #tarifa = tarifa.cu #tarifa: CU [tariffs]
    return tarifa

#Funcion que calcula EA - Energia activa (consumption)
def calculo_consumo(db: Session,ID_service: int, year: int, month: int):
    resultado = 0
    total = 0
    tabla = "consumos" #el nombre referenciado debe ser escrito en minuscula
    try:
        total = suma_valores(db,ID_service,year,month,tabla)
    except HTTPException as e:
        raise e

    #Se busca la tarifa
    tarifa = buscar_tarifa(db,ID_service) #tarifa: CU [tariffs]
    #Se hace la operacion
    resultado = tarifa.cu*total

    return resultado

#Funcion que calcula EC - Comercialización de Excedentes de Energía (injection)
def calculo_inyeccion(db: Session,ID_service: int, year: int, month: int):
    resultado = 0
    total = 0
    tabla = "inyeccion" #el nombre referenciado debe ser escrito en minuscula
    try:
        total = suma_valores(db,ID_service,year,month,tabla)
    except HTTPException as e:
        raise e

    #Se busca la tarifa
    tarifa = buscar_tarifa(db,ID_service) #tarifa: C [tariffs]
    #Se hace la operacion
    resultado = tarifa.c*total

    return resultado

#Funcion que calcula EE1 - Excedentes de Energía tipo 1
def energia_excedente_1(db: Session,ID_service: int, year: int, month: int):
    resultado = 0
    tabla_i = "inyeccion"
    tabla_c = "consumos"
    inyeccion = suma_valores(db,ID_service,year,month,tabla_i)
    consumo = suma_valores(db,ID_service,year,month,tabla_c)

    #validacion para estipular la cantidad
    if(  inyeccion <= consumo  ):
        cantidad_ee1 = inyeccion
    elif (  inyeccion > consumo  ):
        cantidad_ee1 = consumo
    
    #Se busca la tarifa
    tarifa = buscar_tarifa(db,ID_service) #tarifa: -CU [tariffs]
    #Se hace la operacion
    resultado = -tarifa.cu*cantidad_ee1

    return resultado

#Funcion que calcula EE2 - Excedentes de Energía tipo 2
def energia_excedente_2(db: Session,ID_service: int, year: int, month: int):
    resultado = 0.0
    tabla_i = "inyeccion"
    tabla_c = "consumos"
    #calculo de consumos e inyeccion
    inyeccion = suma_valores(db,ID_service,year,month,tabla_i)
    consumo = suma_valores(db,ID_service,year,month,tabla_c)

    #validacion para estipular la cantidad
    if(  inyeccion <= consumo  ):
        cantidad_ee2 = 0
    elif (  inyeccion > consumo  ):
        cantidad_ee2 = consumo - inyeccion

    # Convertir el año y mes a fechas
    fecha_inicio = datetime(year, month, 1)
    if month == 12:
        siguiente_mes = datetime(year + 1, 1, 1)
    else:
        siguiente_mes = datetime(year, month + 1, 1)
    fecha_fin = siguiente_mes - timedelta(hours=1)

    # Consulta para calcular con tarifas por hora
    query = db.query(
        REGISTROS.record_timestamp,        
        INYECCION.value,
        TIEMPOS.value
    )\
    .filter(REGISTROS.id_service == ID_service)\
    .filter(REGISTROS.record_timestamp.between(fecha_inicio, fecha_fin))\
    .join(INYECCION, REGISTROS.id_record == INYECCION.id_record)\
    .join(TIEMPOS, REGISTROS.record_timestamp == TIEMPOS.record_timestamp)\
    .order_by(REGISTROS.record_timestamp.asc())\
    .yield_per(1000)

    #variables auxiliares para el calculo final
    suma=0.0
    switch = False
    verificar=0.0

    #calculo final
    for timestamp, value, tarifa in query:
        suma += value
        if (suma >= consumo and switch == False):
            switch=True
            verificar = suma-consumo
            resultado += ((value-verificar) * tarifa)
        elif(switch == True):
            resultado += (value * tarifa)
            verificar += value

    return resultado
