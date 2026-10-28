"""Conexiones por solicitud. Los SP administran sus propias transacciones."""
import os
from pathlib import Path
import pyodbc
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

def get_db():
    value = os.getenv('ODBC_CONNECTION_STRING')
    if not value:
        raise RuntimeError('Configure ODBC_CONNECTION_STRING en .env')
    connection = pyodbc.connect(value, autocommit=True, timeout=5)
    try:
        yield connection
    finally:
        connection.close()

def rows(cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
