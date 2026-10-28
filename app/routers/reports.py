from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from app.database import get_db, rows
from app.schemas import VentasReporte,StockReporte,ErrorResponse

router=APIRouter(prefix='/reportes',tags=['Reportes'],responses={500:{'model':ErrorResponse}})

@router.get('/ventas-mensuales',response_model=list[VentasReporte],summary='Ingresos mensuales por sucursal',description='Cuenta ventas y calcula SUM, AVG, MIN y MAX de los totales individuales; HAVING aplica el umbral de ingresos. No duplica pagos ni detalles.')
def monthly(min_total: Decimal=Query(Decimal('0'),ge=0,max_digits=14,decimal_places=2),db=Depends(get_db)):
    return rows(db.cursor().execute('''
    WITH totales AS (SELECT venta_id,SUM(CONVERT(DECIMAL(14,2),cantidad)*precio_unitario) total FROM DetalleVenta GROUP BY venta_id)
    SELECT s.nombre sucursal,YEAR(v.fecha) anio,MONTH(v.fecha) mes,COUNT(*) ventas,
      SUM(t.total) total,AVG(t.total) promedio,MIN(t.total) minimo,MAX(t.total) maximo
    FROM Ventas v JOIN totales t ON t.venta_id=v.id JOIN Almacenes a ON a.id=v.almacen_id JOIN Sucursales s ON s.id=a.sucursal_id
    GROUP BY s.id,s.nombre,YEAR(v.fecha),MONTH(v.fecha) HAVING SUM(t.total)>=?
    ORDER BY anio,mes,sucursal''',min_total))

@router.get('/inventario-categorias',response_model=list[StockReporte],summary='Disponibilidad por categoria',description='Agrega primero el stock de cada producto en todos los almacenes. Incluye productos sin existencias con cero. Filtra categorias mediante HAVING.')
def inventory(min_unidades: int=Query(0,ge=0),db=Depends(get_db)):
    return rows(db.cursor().execute('''
    WITH stock AS (SELECT p.id,p.categoria_id,COALESCE(SUM(e.cantidad),0) cantidad FROM Productos p
      LEFT JOIN Existencias e ON e.producto_id=p.id GROUP BY p.id,p.categoria_id)
    SELECT c.nombre categoria,COUNT(*) productos,SUM(s.cantidad) unidades,
      AVG(CONVERT(DECIMAL(14,2),s.cantidad)) promedio,MIN(s.cantidad) minimo,MAX(s.cantidad) maximo
    FROM Categorias c JOIN stock s ON s.categoria_id=c.id
    GROUP BY c.id,c.nombre HAVING SUM(s.cantidad)>=? ORDER BY categoria''',min_unidades))
