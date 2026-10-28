"""Pruebas reales: requieren una base exclusiva InventarioFinalTests ya inicializada."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
import json
import pyodbc
import pytest
from fastapi.testclient import TestClient
from app.database import get_db
from app.main import app

CONNECTION=os.getenv('TEST_ODBC_CONNECTION_STRING')
pytestmark=pytest.mark.skipif(not CONNECTION,reason='Configure TEST_ODBC_CONNECTION_STRING con una base de pruebas')

@pytest.fixture
def db():
    connection=pyodbc.connect(CONNECTION,autocommit=True)
    assert connection.cursor().execute('SELECT DB_NAME()').fetchval()=='InventarioFinalTests', 'Nunca ejecutar contra produccion'
    connection.execute('BEGIN TRANSACTION')
    yield connection
    if connection.execute('SELECT @@TRANCOUNT').fetchval(): connection.execute('ROLLBACK TRANSACTION')
    connection.close()

@pytest.fixture
def client(db):
    def override(): yield db
    app.dependency_overrides[get_db]=override
    with TestClient(app) as instance: yield instance
    app.dependency_overrides.clear()

@pytest.mark.parametrize('path,payload',[
    ('categorias',{'nombre':'Temporal'}),('marcas',{'nombre':'Temporal'}),
    ('clientes',{'nombre':'Temporal','nit':'TEST-C','email':'t@example.test'}),
    ('proveedores',{'nombre':'Temporal','nit':'TEST-P','email':'t@example.test'}),
    ('productos',{'nombre':'Temporal','sku':'TEST-SKU','categoria_id':1,'marca_id':1,'unidad_id':1,'precio':'10.50','activo':True}),
])
def test_crud(client,path,payload):
    response=client.post('/'+path,json=payload)
    assert response.status_code==201,response.text
    ident=response.json()['id']
    assert client.get(f'/{path}/{ident}').json()['nombre']=='Temporal'
    assert client.get('/'+path).status_code==200
    payload['nombre']='Editado'
    assert client.put(f'/{path}/{ident}',json=payload).json()['nombre']=='Editado'
    assert client.delete(f'/{path}/{ident}').status_code==204
    assert client.get(f'/{path}/{ident}').status_code==404

def sale(**changes):
    body={'cliente_id':1,'almacen_id':1,'empleado_id':1,'metodo_pago_id':1,'referencia':str(uuid4()),'items':[{'producto_id':2,'cantidad':1}]}
    body.update(changes)
    return body

def test_integrity_and_validation(client):
    assert client.post('/categorias',json={'nombre':'Computacion'}).status_code==400
    assert client.delete('/categorias/1').status_code==400
    assert client.post('/productos',json={'nombre':'X','sku':'X','categoria_id':9999,'marca_id':1,'unidad_id':1,'precio':5}).status_code==400
    assert client.post('/categorias',json={'nombre':'  '}).status_code==400
    assert client.get('/clientes?limit=500').status_code==400
    assert client.get('/clientes/0').status_code==400
    assert client.post('/operaciones/ventas',json=sale(items=[])).status_code==400
    assert client.post('/operaciones/ventas',json=sale(items=[{'producto_id':2,'cantidad':1}]*2)).status_code==400

def test_sale_success(client,db):
    before=db.execute('SELECT cantidad FROM Existencias WHERE almacen_id=1 AND producto_id=2').fetchval()
    result=client.post('/operaciones/ventas',json=sale())
    assert result.status_code==201,result.text
    ident=result.json()['id']
    assert db.execute('SELECT cantidad FROM Existencias WHERE almacen_id=1 AND producto_id=2').fetchval()==before-1
    assert db.execute('SELECT COUNT(*) FROM Pagos WHERE venta_id=?',ident).fetchval()==1
    assert db.execute('SELECT cantidad FROM MovimientosInventario WHERE venta_id=?',ident).fetchval()==-1

def counts(db):
    return tuple(db.execute(f'SELECT COUNT(*) FROM {t}').fetchval() for t in ['Ventas','DetalleVenta','Pagos','MovimientosInventario'])

def test_sale_failure_is_atomic(client,db):
    before=counts(db)
    stock=db.execute('SELECT SUM(cantidad) FROM Existencias').fetchval()
    result=client.post('/operaciones/ventas',json=sale(items=[{'producto_id':1,'cantidad':1},{'producto_id':2,'cantidad':100000}]))
    assert result.status_code==400,result.text
    assert result.json()['error']['codigo']=='51003'
    assert counts(db)==before
    assert db.execute('SELECT SUM(cantidad) FROM Existencias').fetchval()==stock

def test_rollback_after_partial_writes(client,db):
    # Una falla tardia en el INSERT del pago ocurre despues del descuento y los movimientos.
    db.execute('''CREATE OR ALTER TRIGGER dbo.TestRejectPayment ON dbo.Pagos AFTER INSERT AS
      BEGIN THROW 51001,'Falla de prueba posterior a cambios',1; END''')
    before=counts(db)
    stock=db.execute('SELECT SUM(cantidad) FROM Existencias').fetchval()
    response=client.post('/operaciones/ventas',json=sale())
    assert response.status_code==400,response.text
    assert counts(db)==before
    assert db.execute('SELECT SUM(cantidad) FROM Existencias').fetchval()==stock
    assert db.execute("SELECT OBJECT_ID('dbo.TestRejectPayment')").fetchval() is None

def test_duplicate_reference(client,db):
    before=counts(db)
    response=client.post('/operaciones/ventas',json=sale(referencia='11111111-1111-1111-1111-111111111111'))
    assert response.status_code==400,response.text
    assert counts(db)==before

def test_receipt(client,db):
    before=db.execute('SELECT cantidad FROM Existencias WHERE almacen_id=2 AND producto_id=2').fetchval()
    assert client.post('/operaciones/compras/2/recepcion').status_code==200
    assert db.execute('SELECT cantidad FROM Existencias WHERE almacen_id=2 AND producto_id=2').fetchval()==before+15
    assert db.execute('SELECT estado FROM Compras WHERE id=2').fetchval()=='RECIBIDA'

def test_receipt_failure(client,db):
    before=counts(db)
    assert client.post('/operaciones/compras/1/recepcion').status_code==400
    assert counts(db)==before
    assert client.post('/operaciones/compras/9999/recepcion').status_code==404

def test_reports(client,db):
    report=client.get('/reportes/ventas-mensuales')
    assert report.status_code==200,report.text
    total=sum(float(x['total']) for x in report.json())
    assert total==9420
    assert client.get('/reportes/ventas-mensuales?min_total=100000').json()==[]
    stock=client.get('/reportes/inventario-categorias')
    assert stock.status_code==200,stock.text
    assert sum(x['unidades'] for x in stock.json())==db.execute('SELECT SUM(cantidad) FROM Existencias').fetchval()
    assert sum(x['productos'] for x in stock.json())==5

def test_swagger(client):
    assert client.get('/docs').status_code==200
    schema=client.get('/openapi.json').json()
    assert len(schema['paths'])==15
    assert '422' not in schema['paths']['/productos']['post']['responses']

def test_concurrent_last_unit():
    barrier=Barrier(2)
    with pyodbc.connect(CONNECTION,autocommit=True) as connection:
        assert connection.execute('SELECT DB_NAME()').fetchval()=='InventarioFinalTests'
        product=connection.execute("INSERT Productos(categoria_id,marca_id,unidad_id,sku,nombre,precio) OUTPUT INSERTED.id VALUES(1,1,1,?,'Concurrente',1)",str(uuid4())).fetchval()
        connection.execute('INSERT Existencias(almacen_id,producto_id,cantidad) VALUES(1,?,1)',product)
    def attempt():
        c=pyodbc.connect(CONNECTION,autocommit=True)
        try:
            barrier.wait(timeout=10)
            c.execute('EXEC RegistrarVenta 1,1,1,1,?,?',str(uuid4()),json.dumps([{'producto_id':product,'cantidad':1}])).fetchone()
            return 'ok'
        except pyodbc.Error as error:
            assert '51003' in str(error),str(error)
            return 'rechazada'
        finally: c.close()
    try:
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(lambda _:attempt(),range(2)))
        assert sorted(results)==['ok','rechazada']
        with pyodbc.connect(CONNECTION,autocommit=True) as c:
            assert c.execute('SELECT cantidad FROM Existencias WHERE producto_id=?',product).fetchval()==0
    finally:
        with pyodbc.connect(CONNECTION,autocommit=True) as c:
            c.execute('DELETE Pagos WHERE venta_id IN(SELECT venta_id FROM DetalleVenta WHERE producto_id=?)',product)
            c.execute('DELETE MovimientosInventario WHERE producto_id=?',product)
            ids=[row[0] for row in c.execute('SELECT venta_id FROM DetalleVenta WHERE producto_id=?',product)]
            c.execute('DELETE DetalleVenta WHERE producto_id=?',product)
            for ident in ids: c.execute('DELETE Ventas WHERE id=?',ident)
            c.execute('DELETE Existencias WHERE producto_id=?',product)
            c.execute('DELETE Productos WHERE id=?',product)
