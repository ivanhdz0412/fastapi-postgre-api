# Proyecto API con FastAPI y PostgreSQL

Este proyecto es una API desarrollada con **FastAPI** que utiliza **PostgreSQL** como base de datos. A continuación, se detallan los pasos para configurar y ejecutar el proyecto.

---

## Requisitos previos

Antes de comenzar, asegúrate de tener instalado lo siguiente:

- **Python 3.8 o superior**.
- **PostgreSQL** instalado y en ejecución.
- **pgAdmin** (opcional, pero recomendado para gestionar la base de datos).

---

## Configuración del proyecto

### 1. Clonar el repositorio

```bash
git clone https://github.com/ivanhdz0412/fastapi-postgre-api
cd <CARPETA_DEL_PROYECTO>
```

### 2. Instalar dependencias

    $ pip install -r requirements.txt

### 3. Ejecutar la API 

```bash
uvicorn main:app --reload
```

## Documentación de la API

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
