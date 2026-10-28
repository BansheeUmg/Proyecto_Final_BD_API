import logging
import re
import pyodbc
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.routers import catalogs,operations,reports

logger=logging.getLogger(__name__)
app=FastAPI(title='Inventario y Ventas - Proyecto Final BD',version='1.0.0',description='24 tablas en SQL Server; cinco CRUD, dos transacciones y dos reportes. Proyecto academico local.')

def error(status,code,message):
    return JSONResponse(status_code=status,content={'error':{'codigo':code,'mensaje':message}})

@app.exception_handler(HTTPException)
async def http_error(request:Request,exc:HTTPException):
    return error(exc.status_code,'HTTP_ERROR',str(exc.detail))

@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,exc:RequestValidationError):
    # Nunca devolver el cuerpo recibido: podria contener datos privados.
    return error(400,'VALIDACION','; '.join('.'.join(map(str,e['loc']))+': '+e['msg'] for e in exc.errors()))

@app.exception_handler(pyodbc.Error)
async def database_error(request:Request,exc:pyodbc.Error):
    text=str(exc)
    domain=re.search(r'\((5100[1-4])\)',text)
    if domain:
        code=domain.group(1)
        messages={'51001':'Datos de operacion invalidos. Verifique cliente, empleado, sucursal, metodo de pago y productos.','51002':'Operacion ya procesada: referencia repetida o compra recibida.','51003':'Producto inactivo, inexistente o existencias insuficientes.','51004':'Compra no encontrada.'}
        return error(404 if code=='51004' else 400,code,messages[code])
    if isinstance(exc,pyodbc.IntegrityError) or '23000' in text:
        return error(400,'INTEGRIDAD','Registro duplicado, referencia inexistente o registro relacionado que impide la operacion.')
    logger.exception('Error de base de datos')
    return error(500,'BASE_DATOS','No fue posible completar la operacion en la base de datos.')

@app.exception_handler(Exception)
async def unexpected_error(request:Request,exc:Exception):
    logger.exception('Error inesperado')
    return error(500,'INTERNO','Error interno del servidor.')

@app.get('/health',tags=['Estado'],summary='Estado del servicio')
def health(): return {'estado':'ok'}

app.include_router(catalogs.router)
app.include_router(operations.router)
app.include_router(reports.router)

# La validacion personalizada devuelve 400 en todas las rutas.
original_openapi=app.openapi
def custom_openapi():
    schema=original_openapi()
    for path in schema['paths'].values():
        for operation in path.values():
            if isinstance(operation,dict) and 'responses' in operation:
                operation['responses'].pop('422',None)
                operation['responses'].setdefault('400',{'description':'Datos invalidos','content':{'application/json':{'schema':{'$ref':'#/components/schemas/ErrorResponse'}}}})
    return schema
app.openapi=custom_openapi
