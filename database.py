from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, ForeignKeyConstraint, UniqueConstraint

# Conexion a la base de datos. Ajustar datos segun confguracion local o del servidor
DATABASE_URL = "postgresql://postgres:123456@localhost/prueba_energy"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Configuración para acceder a la base de datos
class SERVICIOS(Base):
    __tablename__ = "services"
    id_service = Column(Integer, primary_key=True)
    id_market = Column(Integer, nullable=False)
    cdi = Column(Integer, nullable=False)
    voltage_level = Column(Integer, nullable=False)

    # Relación con la tabla records
    records = relationship("REGISTROS", back_populates="service")

    # Relación con la tabla tariffs
    tariffs = relationship("TARIFAS", back_populates="service")

    # Restricción única
    __table_args__ = (
        UniqueConstraint('id_market', 'cdi', 'voltage_level', name='uq_service'),
    )

class TIEMPOS(Base):
    __tablename__ = "xm_data_hourly_per_agent" 
    record_timestamp = Column(TIMESTAMP, primary_key=True)
    value = Column(Float, nullable=False)

    # Relación con la tabla records
    records = relationship("REGISTROS", back_populates="xm_data")

class REGISTROS(Base):
    __tablename__ = "records" 
    id_record = Column(Integer, primary_key=True)
    id_service = Column(Integer, ForeignKey('services.id_service'), nullable=False)
    record_timestamp = Column(TIMESTAMP, ForeignKey('xm_data_hourly_per_agent.record_timestamp'), nullable=False)
    
    # Relación con la tabla services
    service = relationship("SERVICIOS", back_populates="records")

    # Relación con la tabla xm_data_hourly_per_agent
    xm_data = relationship("TIEMPOS", back_populates="records")

    # Relación con la tabla injection
    injection = relationship("INYECCION", uselist=False, back_populates="id_registro")

    # Relación con la tabla consumption
    consumption = relationship("CONSUMOS", uselist=False, back_populates="id_registro")

class CONSUMOS(Base):
    __tablename__ = "consumption"   
    id_record = Column(Integer, ForeignKey('records.id_record'), primary_key=True)
    value = Column(Float, nullable=False)

    # Relación con la tabla records
    id_registro = relationship("REGISTROS", back_populates="consumption")

class INYECCION(Base):
    __tablename__ = "injection" 
    id_record = Column(Integer, ForeignKey('records.id_record'), primary_key=True)
    value = Column(Float, nullable=False)

    # Relación con la tabla records
    id_registro = relationship("REGISTROS", back_populates="injection")

class TARIFAS(Base):
    __tablename__ = "tariffs" 
    id_market = Column(Integer, primary_key=True)
    voltage_level = Column(Integer, primary_key=True)
    cdi = Column(Integer, primary_key=True)
    g = Column(Float, nullable=False)
    t = Column(Float, nullable=False)
    d = Column(Float, nullable=False)
    r = Column(Float, nullable=False)
    c = Column(Float, nullable=False)
    p = Column(Float, nullable=False)
    cu = Column(Float, nullable=False)

    # Relación con la tabla services
    service = relationship("SERVICIOS", back_populates="tariffs")

    # Clave compuesta
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_market', 'voltage_level', 'cdi'],
            ['services.id_market', 'services.voltage_level', 'services.cdi']
        ),
    )

# Diccionario que mapea nombres de clases a las clases reales para usar en funciones
CLASES_TABLAS = {
    "servicios": SERVICIOS,
    "tiempos": TIEMPOS,
    "registros": REGISTROS,
    "consumos": CONSUMOS,
    "inyeccion": INYECCION,
    "tarifas": TARIFAS
}
