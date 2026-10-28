from decimal import Decimal
from typing import Annotated
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
CatalogName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Nit = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
Email = Annotated[str, StringConstraints(strip_whitespace=True, max_length=160, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')]
PositiveId = Annotated[int, Field(gt=0)]
Money = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class CategoriaIn(Input):
    nombre: CatalogName
class CategoriaOut(CategoriaIn):
    id: int
class MarcaIn(Input):
    nombre: CatalogName
class MarcaOut(MarcaIn):
    id: int
class ClienteIn(Input):
    nombre: Name
    nit: Nit
    email: Email
class ClienteOut(ClienteIn):
    id: int
class ProveedorIn(ClienteIn):
    pass
class ProveedorOut(ProveedorIn):
    id: int
class ProductoIn(Input):
    categoria_id: PositiveId
    marca_id: PositiveId
    unidad_id: PositiveId
    sku: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
    nombre: Name
    precio: Money
    activo: bool = True
class ProductoOut(ProductoIn):
    id: int
class LineaVenta(Input):
    producto_id: PositiveId
    cantidad: Annotated[int, Field(gt=0, le=100000)]
class VentaIn(Input):
    cliente_id: PositiveId
    almacen_id: PositiveId
    empleado_id: PositiveId
    metodo_pago_id: PositiveId
    referencia: UUID
    items: list[LineaVenta] = Field(min_length=1, max_length=100)
    @model_validator(mode='after')
    def unique_products(self):
        ids=[item.producto_id for item in self.items]
        if len(set(ids))!=len(ids):
            raise ValueError('No repita productos en la venta')
        return self
class VentaOut(BaseModel):
    id: int
    total: Decimal
    estado: str
class RecepcionOut(BaseModel):
    id: int
    estado: str
class VentasReporte(BaseModel):
    sucursal: str
    anio: int
    mes: int
    ventas: int
    total: Decimal
    promedio: Decimal
    minimo: Decimal
    maximo: Decimal
class StockReporte(BaseModel):
    categoria: str
    productos: int
    unidades: int
    promedio: Decimal
    minimo: int
    maximo: int
class ErrorDetail(BaseModel):
    codigo: str
    mensaje: str
class ErrorResponse(BaseModel):
    error: ErrorDetail
