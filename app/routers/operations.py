import json
from typing import Annotated
from fastapi import APIRouter, Depends, Path
from app.database import get_db, rows
from app.schemas import VentaIn, VentaOut, RecepcionOut, ErrorResponse

router=APIRouter(prefix='/operaciones',tags=['Transacciones'],responses={400:{'model':ErrorResponse},404:{'model':ErrorResponse},500:{'model':ErrorResponse}})

@router.post('/ventas',response_model=VentaOut,status_code=201,summary='Registrar venta y cobro atomicos',description='Crea venta, detalle, pago y movimientos y descuenta stock. La referencia UUID unica evita duplicaciones; una repeticion devuelve 400. Cualquier error revierte todos los cambios.')
def sell(body: VentaIn,db=Depends(get_db)):
    return rows(db.cursor().execute('EXEC dbo.RegistrarVenta ?,?,?,?,?,?',body.cliente_id,body.almacen_id,body.empleado_id,body.metodo_pago_id,str(body.referencia),json.dumps([x.model_dump() for x in body.items])))[0]

@router.post('/compras/{compra_id}/recepcion',response_model=RecepcionOut,summary='Recibir compra pendiente',description='Incrementa existencias, registra movimientos y cambia la compra a RECIBIDA dentro de una transaccion. Una segunda recepcion se rechaza.')
def receive(compra_id: Annotated[int,Path(gt=0)],db=Depends(get_db)):
    return rows(db.cursor().execute('EXEC dbo.RecibirCompra ?',compra_id))[0]
