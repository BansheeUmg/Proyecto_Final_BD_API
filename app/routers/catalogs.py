from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, Response
from app.database import get_db
from app import schemas as s
from app.services import crud

router=APIRouter()
REGISTRY=[('categorias','Categorias',s.CategoriaIn,s.CategoriaOut),('marcas','Marcas',s.MarcaIn,s.MarcaOut),('clientes','Clientes',s.ClienteIn,s.ClienteOut),('proveedores','Proveedores',s.ProveedorIn,s.ProveedorOut),('productos','Productos',s.ProductoIn,s.ProductoOut)]

def entity_router(path,table,input_model,output_model):
    api=APIRouter(prefix='/'+path,tags=[table],responses={400:{'model':s.ErrorResponse,'description':'Restriccion de integridad'},404:{'model':s.ErrorResponse,'description':'Registro inexistente'},500:{'model':s.ErrorResponse,'description':'Error interno'}})
    @api.get('',response_model=list[output_model],summary=f'Listar {path}',description='Resultados paginados por id; limite maximo 100.')
    def listing(offset: int=Query(0,ge=0),limit: int=Query(20,ge=1,le=100),db=Depends(get_db)):
        return crud.list_records(db,table,offset,limit)
    @api.get('/{record_id}',response_model=output_model,summary=f'Consultar {path} por ID')
    def detail(record_id: Annotated[int,Path(gt=0)],db=Depends(get_db)):
        return crud.get_record(db,table,record_id)
    @api.post('',response_model=output_model,status_code=201,summary=f'Crear en {path}')
    def create(body: input_model,db=Depends(get_db)):
        return crud.create_record(db,table,body.model_dump())
    @api.put('/{record_id}',response_model=output_model,summary=f'Reemplazar en {path}',description='Reemplazo completo. Valida claves foraneas y campos unicos.')
    def update(record_id: Annotated[int,Path(gt=0)],body: input_model,db=Depends(get_db)):
        return crud.update_record(db,table,record_id,body.model_dump())
    @api.delete('/{record_id}',status_code=204,summary=f'Eliminar de {path}',description='Las relaciones existentes impiden eliminar un registro referenciado.')
    def delete(record_id: Annotated[int,Path(gt=0)],db=Depends(get_db)):
        crud.delete_record(db,table,record_id)
        return Response(status_code=204)
    return api

for spec in REGISTRY: router.include_router(entity_router(*spec))
