"""Genera el DDL, datos reproducibles y diagrama a partir del catálogo del dominio."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
TABLES = {}
def table(name, fields, extra='', seeds=None):
    TABLES[name] = (fields, extra, seeds or [])

table('Regiones', 'nombre NVARCHAR(80) NOT NULL UNIQUE', seeds=[("Central",), ("Occidente",)])
table('Municipios', 'region_id INT NOT NULL REFERENCES Regiones(id), nombre NVARCHAR(80) NOT NULL', 'UNIQUE(region_id,nombre)', [(1,'Guatemala'),(2,'Quetzaltenango')])
table('Sucursales', 'municipio_id INT NOT NULL REFERENCES Municipios(id), nombre NVARCHAR(100) NOT NULL UNIQUE, direccion NVARCHAR(200) NOT NULL', seeds=[(1,'Central','Zona 1'),(2,'Occidente','Zona 3')])
table('Almacenes', 'sucursal_id INT NOT NULL REFERENCES Sucursales(id), nombre NVARCHAR(80) NOT NULL', 'UNIQUE(sucursal_id,nombre)', [(1,'Principal'),(2,'Principal')])
table('Roles', 'nombre NVARCHAR(80) NOT NULL UNIQUE', seeds=[('Administrador',),('Vendedor',),('Bodeguero',)])
table('Empleados', 'sucursal_id INT NOT NULL REFERENCES Sucursales(id), nombre NVARCHAR(100) NOT NULL, email NVARCHAR(160) NOT NULL UNIQUE, activo BIT NOT NULL DEFAULT 1', seeds=[(1,'Ana Lopez','ana@example.test',1),(2,'Luis Perez','luis@example.test',1)])
table('PerfilesEmpleado', 'empleado_id INT NOT NULL UNIQUE REFERENCES Empleados(id), telefono NVARCHAR(20) NOT NULL, fecha_ingreso DATE NOT NULL', seeds=[(1,'5555-0101','2025-01-01'),(2,'5555-0102','2025-02-01')])
table('EmpleadoRoles', 'empleado_id INT NOT NULL REFERENCES Empleados(id), rol_id INT NOT NULL REFERENCES Roles(id)', 'UNIQUE(empleado_id,rol_id)', [(1,1),(1,2),(2,3)])
table('Clientes', 'nombre NVARCHAR(100) NOT NULL, nit NVARCHAR(20) NOT NULL UNIQUE, email NVARCHAR(160) NOT NULL', seeds=[('Cliente Demo','CF-001','cliente@example.test'),('Comercial Sol','123456-7','sol@example.test')])
table('DireccionesCliente', 'cliente_id INT NOT NULL REFERENCES Clientes(id), municipio_id INT NOT NULL REFERENCES Municipios(id), direccion NVARCHAR(200) NOT NULL', seeds=[(1,1,'Zona 5'),(2,2,'Zona 2')])
table('Proveedores', 'nombre NVARCHAR(100) NOT NULL, nit NVARCHAR(20) NOT NULL UNIQUE, email NVARCHAR(160) NOT NULL', seeds=[('Distribuidora Norte','PROV-01','norte@example.test'),('Tecnologia Sur','PROV-02','sur@example.test')])
table('Categorias', 'nombre NVARCHAR(80) NOT NULL UNIQUE', seeds=[('Computacion',),('Accesorios',),('Oficina',)])
table('Marcas', 'nombre NVARCHAR(80) NOT NULL UNIQUE', seeds=[('Marca Uno',),('Marca Dos',)])
table('Unidades', 'nombre NVARCHAR(40) NOT NULL UNIQUE', seeds=[('Unidad',),('Caja',)])
table('Productos', 'categoria_id INT NOT NULL REFERENCES Categorias(id), marca_id INT NOT NULL REFERENCES Marcas(id), unidad_id INT NOT NULL REFERENCES Unidades(id), sku NVARCHAR(40) NOT NULL UNIQUE, nombre NVARCHAR(100) NOT NULL, precio DECIMAL(12,2) NOT NULL CHECK(precio>0), activo BIT NOT NULL DEFAULT 1', seeds=[(1,1,1,'LAP-01','Laptop',4500,1),(2,2,1,'MOU-01','Mouse',90,1),(3,1,2,'PAP-01','Papel',40,1),(2,1,1,'TEC-01','Teclado',150,1),(1,2,1,'MON-01','Monitor',1200,1)])
table('ProductoProveedores', 'producto_id INT NOT NULL REFERENCES Productos(id), proveedor_id INT NOT NULL REFERENCES Proveedores(id), costo DECIMAL(12,2) NOT NULL CHECK(costo>0)', 'UNIQUE(producto_id,proveedor_id)', [(1,1,3000),(2,2,40),(3,1,20),(4,2,80),(5,1,800)])
table('Existencias', 'almacen_id INT NOT NULL REFERENCES Almacenes(id), producto_id INT NOT NULL REFERENCES Productos(id), cantidad INT NOT NULL DEFAULT 0 CHECK(cantidad>=0), minimo INT NOT NULL DEFAULT 5 CHECK(minimo>=0)', 'UNIQUE(almacen_id,producto_id)', [(a,p,50 if a==1 else 10,5) for a in (1,2) for p in range(1,6)])
table('Compras', "proveedor_id INT NOT NULL REFERENCES Proveedores(id), almacen_id INT NOT NULL REFERENCES Almacenes(id), empleado_id INT NOT NULL REFERENCES Empleados(id), fecha DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(), estado NVARCHAR(12) NOT NULL DEFAULT 'PENDIENTE' CHECK(estado IN ('PENDIENTE','RECIBIDA'))", seeds=[(1,1,1,'2026-10-01','PENDIENTE'),(2,2,2,'2026-10-02','PENDIENTE')])
table('DetalleCompra', 'compra_id INT NOT NULL REFERENCES Compras(id), producto_id INT NOT NULL REFERENCES Productos(id), cantidad INT NOT NULL CHECK(cantidad>0), costo DECIMAL(12,2) NOT NULL CHECK(costo>0)', 'UNIQUE(compra_id,producto_id)', [(1,1,5,3000),(1,3,20,20),(2,2,15,40),(2,4,10,80)])
table('Ventas', 'cliente_id INT NOT NULL REFERENCES Clientes(id), almacen_id INT NOT NULL REFERENCES Almacenes(id), empleado_id INT NOT NULL REFERENCES Empleados(id), fecha DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(), referencia UNIQUEIDENTIFIER NOT NULL UNIQUE', seeds=[])
table('DetalleVenta', 'venta_id INT NOT NULL REFERENCES Ventas(id), producto_id INT NOT NULL REFERENCES Productos(id), cantidad INT NOT NULL CHECK(cantidad>0), precio_unitario DECIMAL(12,2) NOT NULL CHECK(precio_unitario>0)', 'UNIQUE(venta_id,producto_id)')
table('MetodosPago', 'nombre NVARCHAR(60) NOT NULL UNIQUE', seeds=[('Efectivo',),('Tarjeta',),('Transferencia',)])
table('Pagos', 'venta_id INT NOT NULL REFERENCES Ventas(id), metodo_pago_id INT NOT NULL REFERENCES MetodosPago(id), monto DECIMAL(14,2) NOT NULL CHECK(monto>0), fecha DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()')
table('MovimientosInventario', "almacen_id INT NOT NULL REFERENCES Almacenes(id), producto_id INT NOT NULL REFERENCES Productos(id), venta_id INT NULL REFERENCES Ventas(id), compra_id INT NULL REFERENCES Compras(id), cantidad INT NOT NULL CHECK(cantidad<>0), fecha DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()", 'CHECK((venta_id IS NOT NULL AND compra_id IS NULL AND cantidad<0) OR (venta_id IS NULL AND compra_id IS NOT NULL AND cantidad>0))')

def main():
    for d in ('database','docs','app/routers','app/services','tests','scripts'):
        (ROOT/d).mkdir(parents=True,exist_ok=True)
    sql = ["-- SQL Server 2016+ (compatibilidad 130). No elimina datos existentes.\nUSE master;\nGO\nIF DB_ID(N'InventarioFinal') IS NULL CREATE DATABASE InventarioFinal;\nGO\nUSE InventarioFinal;\nGO\nIF OBJECT_ID(N'dbo.Regiones', N'U') IS NOT NULL\n    THROW 51000, 'Base ya inicializada: no se modifica. Use otra base para una instalacion nueva.', 1;\nGO\nSET XACT_ABORT ON;\nBEGIN TRANSACTION;"]
    relationships=[]
    er=['erDiagram']
    import re
    for name,(fields,extra,seeds) in TABLES.items():
        sql.append(f'CREATE TABLE dbo.{name} (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, {fields}'+(', '+extra if extra else '')+');')
        er.append(f'    {name} {{\n        int id PK')
        # Split only at commas outside decimal/check parentheses.
        cols=re.split(r',\s*(?![^()]*\))',fields)
        for col in cols:
            parts=col.split(); key=parts[0]
            typ=parts[1].split('(')[0].lower()
            fk=re.search(r'REFERENCES (\w+)\(id\)',col)
            er.append(f'        {typ} {key}'+(' FK' if fk else (' UK' if 'UNIQUE' in col else '')))
            if fk: relationships.append((fk[1],name,key,'NULL' in col and 'NOT NULL' not in col,'UNIQUE' in col))
        er.append('    }')
    # Useful FK and reporting indexes, excluding indexes already covered by a leading unique key.
    for parent,child,key,nullable,unique in relationships:
        sql.append(f'CREATE INDEX IX_{child}_{key} ON dbo.{child}({key});')
        er.append(f'    {parent} '+('|o' if nullable else '||')+('--o|' if unique else '--o{')+f' {child} : {key}')
    def lit(x):
        if isinstance(x,str): return "N'"+x.replace("'","''")+"'"
        return str(x)
    for name,(fields,extra,seeds) in TABLES.items():
        if seeds:
            cols=[x.split()[0] for x in re.split(r',\s*(?![^()]*\))',fields)]
            sql.append(f"INSERT INTO dbo.{name} ({','.join(cols)}) VALUES\n"+',\n'.join('('+','.join(lit(x) for x in row)+')' for row in seeds)+';')
    sql.append('COMMIT TRANSACTION;\nGO')
    sql.append((ROOT/'database/procedures.sql').read_text(encoding='utf-8'))
    sql.append("\n-- Ventas y recepciones semilla usan la misma logica transaccional de la API.\nDECLARE @v UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111111';\nEXEC dbo.RegistrarVenta 1,1,1,1,@v,N'[{\"producto_id\":1,\"cantidad\":2},{\"producto_id\":2,\"cantidad\":3}]';\nDECLARE @v2 UNIQUEIDENTIFIER = '22222222-2222-2222-2222-222222222222';\nEXEC dbo.RegistrarVenta 2,2,2,2,@v2,N'[{\"producto_id\":4,\"cantidad\":1}]';\nEXEC dbo.RecibirCompra 1;\nGO\n")
    (ROOT/'database/schema_and_data.sql').write_text('\n\n'.join(sql),encoding='utf-8')
    (ROOT/'docs/diagrama_er.mmd').write_text('\n'.join(er)+'\n',encoding='utf-8')
    (ROOT/'docs/catalogo.json').write_text(json.dumps(TABLES,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__': main()
