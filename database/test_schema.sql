-- SQL Server 2016+ (compatibilidad 130). No elimina datos existentes.
USE master;
GO
IF DB_ID(N'InventarioFinalTests') IS NULL CREATE DATABASE InventarioFinalTests;
GO
USE InventarioFinalTests;
GO
IF OBJECT_ID(N'dbo.Regiones', N'U') IS NOT NULL
    THROW 51000, 'Base ya inicializada: no se modifica. Use otra base para una instalacion nueva.', 1;
GO
SET XACT_ABORT ON;
BEGIN TRANSACTION;

CREATE TABLE dbo.Regiones (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, nombre NVARCHAR(80) NOT NULL UNIQUE);

CREATE TABLE dbo.Municipios (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, region_id INT NOT NULL REFERENCES Regiones(id), nombre NVARCHAR(80) NOT NULL, UNIQUE(region_id,nombre));

CREATE TABLE dbo.Sucursales (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, municipio_id INT NOT NULL REFERENCES Municipios(id), nombre NVARCHAR(100) NOT NULL UNIQUE, direccion NVARCHAR(200) NOT NULL);

CREATE TABLE dbo.Almacenes (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, sucursal_id INT NOT NULL REFERENCES Sucursales(id), nombre NVARCHAR(80) NOT NULL, UNIQUE(sucursal_id,nombre));

CREATE TABLE dbo.Roles (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, nombre NVARCHAR(80) NOT NULL UNIQUE);

CREATE TABLE dbo.Empleados (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, sucursal_id INT NOT NULL REFERENCES Sucursales(id), nombre NVARCHAR(100) NOT NULL, email NVARCHAR(160) NOT NULL UNIQUE, activo BIT NOT NULL DEFAULT 1);

CREATE TABLE dbo.PerfilesEmpleado (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, empleado_id INT NOT NULL UNIQUE REFERENCES Empleados(id), telefono NVARCHAR(20) NOT NULL, fecha_ingreso DATE NOT NULL);

CREATE TABLE dbo.EmpleadoRoles (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, empleado_id INT NOT NULL REFERENCES Empleados(id), rol_id INT NOT NULL REFERENCES Roles(id), UNIQUE(empleado_id,rol_id));

CREATE TABLE dbo.Clientes (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, nombre NVARCHAR(100) NOT NULL, nit NVARCHAR(20) NOT NULL UNIQUE, email NVARCHAR(160) NOT NULL);

CREATE TABLE dbo.DireccionesCliente (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, cliente_id INT NOT NULL REFERENCES Clientes(id), municipio_id INT NOT NULL REFERENCES Municipios(id), direccion NVARCHAR(200) NOT NULL);

CREATE TABLE dbo.Proveedores (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, nombre NVARCHAR(100) NOT NULL, nit NVARCHAR(20) NOT NULL UNIQUE, email NVARCHAR(160) NOT NULL);

CREATE TABLE dbo.Categorias (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, nombre NVARCHAR(80) NOT NULL UNIQUE);

CREATE TABLE dbo.Marcas (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, nombre NVARCHAR(80) NOT NULL UNIQUE);

CREATE TABLE dbo.Unidades (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, nombre NVARCHAR(40) NOT NULL UNIQUE);

CREATE TABLE dbo.Productos (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, categoria_id INT NOT NULL REFERENCES Categorias(id), marca_id INT NOT NULL REFERENCES Marcas(id), unidad_id INT NOT NULL REFERENCES Unidades(id), sku NVARCHAR(40) NOT NULL UNIQUE, nombre NVARCHAR(100) NOT NULL, precio DECIMAL(12,2) NOT NULL CHECK(precio>0), activo BIT NOT NULL DEFAULT 1);

CREATE TABLE dbo.ProductoProveedores (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, producto_id INT NOT NULL REFERENCES Productos(id), proveedor_id INT NOT NULL REFERENCES Proveedores(id), costo DECIMAL(12,2) NOT NULL CHECK(costo>0), UNIQUE(producto_id,proveedor_id));

CREATE TABLE dbo.Existencias (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, almacen_id INT NOT NULL REFERENCES Almacenes(id), producto_id INT NOT NULL REFERENCES Productos(id), cantidad INT NOT NULL DEFAULT 0 CHECK(cantidad>=0), minimo INT NOT NULL DEFAULT 5 CHECK(minimo>=0), UNIQUE(almacen_id,producto_id));

CREATE TABLE dbo.Compras (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, proveedor_id INT NOT NULL REFERENCES Proveedores(id), almacen_id INT NOT NULL REFERENCES Almacenes(id), empleado_id INT NOT NULL REFERENCES Empleados(id), fecha DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(), estado NVARCHAR(12) NOT NULL DEFAULT 'PENDIENTE' CHECK(estado IN ('PENDIENTE','RECIBIDA')));

CREATE TABLE dbo.DetalleCompra (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, compra_id INT NOT NULL REFERENCES Compras(id), producto_id INT NOT NULL REFERENCES Productos(id), cantidad INT NOT NULL CHECK(cantidad>0), costo DECIMAL(12,2) NOT NULL CHECK(costo>0), UNIQUE(compra_id,producto_id));

CREATE TABLE dbo.Ventas (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, cliente_id INT NOT NULL REFERENCES Clientes(id), almacen_id INT NOT NULL REFERENCES Almacenes(id), empleado_id INT NOT NULL REFERENCES Empleados(id), fecha DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(), referencia UNIQUEIDENTIFIER NOT NULL UNIQUE);

CREATE TABLE dbo.DetalleVenta (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, venta_id INT NOT NULL REFERENCES Ventas(id), producto_id INT NOT NULL REFERENCES Productos(id), cantidad INT NOT NULL CHECK(cantidad>0), precio_unitario DECIMAL(12,2) NOT NULL CHECK(precio_unitario>0), UNIQUE(venta_id,producto_id));

CREATE TABLE dbo.MetodosPago (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, nombre NVARCHAR(60) NOT NULL UNIQUE);

CREATE TABLE dbo.Pagos (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, venta_id INT NOT NULL REFERENCES Ventas(id), metodo_pago_id INT NOT NULL REFERENCES MetodosPago(id), monto DECIMAL(14,2) NOT NULL CHECK(monto>0), fecha DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME());

CREATE TABLE dbo.MovimientosInventario (id INT IDENTITY(1,1) NOT NULL PRIMARY KEY, almacen_id INT NOT NULL REFERENCES Almacenes(id), producto_id INT NOT NULL REFERENCES Productos(id), venta_id INT NULL REFERENCES Ventas(id), compra_id INT NULL REFERENCES Compras(id), cantidad INT NOT NULL CHECK(cantidad<>0), fecha DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(), CHECK((venta_id IS NOT NULL AND compra_id IS NULL AND cantidad<0) OR (venta_id IS NULL AND compra_id IS NOT NULL AND cantidad>0)));

CREATE INDEX IX_Municipios_region_id ON dbo.Municipios(region_id);

CREATE INDEX IX_Sucursales_municipio_id ON dbo.Sucursales(municipio_id);

CREATE INDEX IX_Almacenes_sucursal_id ON dbo.Almacenes(sucursal_id);

CREATE INDEX IX_Empleados_sucursal_id ON dbo.Empleados(sucursal_id);

CREATE INDEX IX_PerfilesEmpleado_empleado_id ON dbo.PerfilesEmpleado(empleado_id);

CREATE INDEX IX_EmpleadoRoles_empleado_id ON dbo.EmpleadoRoles(empleado_id);

CREATE INDEX IX_EmpleadoRoles_rol_id ON dbo.EmpleadoRoles(rol_id);

CREATE INDEX IX_DireccionesCliente_cliente_id ON dbo.DireccionesCliente(cliente_id);

CREATE INDEX IX_DireccionesCliente_municipio_id ON dbo.DireccionesCliente(municipio_id);

CREATE INDEX IX_Productos_categoria_id ON dbo.Productos(categoria_id);

CREATE INDEX IX_Productos_marca_id ON dbo.Productos(marca_id);

CREATE INDEX IX_Productos_unidad_id ON dbo.Productos(unidad_id);

CREATE INDEX IX_ProductoProveedores_producto_id ON dbo.ProductoProveedores(producto_id);

CREATE INDEX IX_ProductoProveedores_proveedor_id ON dbo.ProductoProveedores(proveedor_id);

CREATE INDEX IX_Existencias_almacen_id ON dbo.Existencias(almacen_id);

CREATE INDEX IX_Existencias_producto_id ON dbo.Existencias(producto_id);

CREATE INDEX IX_Compras_proveedor_id ON dbo.Compras(proveedor_id);

CREATE INDEX IX_Compras_almacen_id ON dbo.Compras(almacen_id);

CREATE INDEX IX_Compras_empleado_id ON dbo.Compras(empleado_id);

CREATE INDEX IX_DetalleCompra_compra_id ON dbo.DetalleCompra(compra_id);

CREATE INDEX IX_DetalleCompra_producto_id ON dbo.DetalleCompra(producto_id);

CREATE INDEX IX_Ventas_cliente_id ON dbo.Ventas(cliente_id);

CREATE INDEX IX_Ventas_almacen_id ON dbo.Ventas(almacen_id);

CREATE INDEX IX_Ventas_empleado_id ON dbo.Ventas(empleado_id);

CREATE INDEX IX_DetalleVenta_venta_id ON dbo.DetalleVenta(venta_id);

CREATE INDEX IX_DetalleVenta_producto_id ON dbo.DetalleVenta(producto_id);

CREATE INDEX IX_Pagos_venta_id ON dbo.Pagos(venta_id);

CREATE INDEX IX_Pagos_metodo_pago_id ON dbo.Pagos(metodo_pago_id);

CREATE INDEX IX_MovimientosInventario_almacen_id ON dbo.MovimientosInventario(almacen_id);

CREATE INDEX IX_MovimientosInventario_producto_id ON dbo.MovimientosInventario(producto_id);

CREATE INDEX IX_MovimientosInventario_venta_id ON dbo.MovimientosInventario(venta_id);

CREATE INDEX IX_MovimientosInventario_compra_id ON dbo.MovimientosInventario(compra_id);

INSERT INTO dbo.Regiones (nombre) VALUES
(N'Central'),
(N'Occidente');

INSERT INTO dbo.Municipios (region_id,nombre) VALUES
(1,N'Guatemala'),
(2,N'Quetzaltenango');

INSERT INTO dbo.Sucursales (municipio_id,nombre,direccion) VALUES
(1,N'Central',N'Zona 1'),
(2,N'Occidente',N'Zona 3');

INSERT INTO dbo.Almacenes (sucursal_id,nombre) VALUES
(1,N'Principal'),
(2,N'Principal');

INSERT INTO dbo.Roles (nombre) VALUES
(N'Administrador'),
(N'Vendedor'),
(N'Bodeguero');

INSERT INTO dbo.Empleados (sucursal_id,nombre,email,activo) VALUES
(1,N'Ana Lopez',N'ana@example.test',1),
(2,N'Luis Perez',N'luis@example.test',1);

INSERT INTO dbo.PerfilesEmpleado (empleado_id,telefono,fecha_ingreso) VALUES
(1,N'5555-0101',N'2025-01-01'),
(2,N'5555-0102',N'2025-02-01');

INSERT INTO dbo.EmpleadoRoles (empleado_id,rol_id) VALUES
(1,1),
(1,2),
(2,3);

INSERT INTO dbo.Clientes (nombre,nit,email) VALUES
(N'Cliente Demo',N'CF-001',N'cliente@example.test'),
(N'Comercial Sol',N'123456-7',N'sol@example.test');

INSERT INTO dbo.DireccionesCliente (cliente_id,municipio_id,direccion) VALUES
(1,1,N'Zona 5'),
(2,2,N'Zona 2');

INSERT INTO dbo.Proveedores (nombre,nit,email) VALUES
(N'Distribuidora Norte',N'PROV-01',N'norte@example.test'),
(N'Tecnologia Sur',N'PROV-02',N'sur@example.test');

INSERT INTO dbo.Categorias (nombre) VALUES
(N'Computacion'),
(N'Accesorios'),
(N'Oficina');

INSERT INTO dbo.Marcas (nombre) VALUES
(N'Marca Uno'),
(N'Marca Dos');

INSERT INTO dbo.Unidades (nombre) VALUES
(N'Unidad'),
(N'Caja');

INSERT INTO dbo.Productos (categoria_id,marca_id,unidad_id,sku,nombre,precio,activo) VALUES
(1,1,1,N'LAP-01',N'Laptop',4500,1),
(2,2,1,N'MOU-01',N'Mouse',90,1),
(3,1,2,N'PAP-01',N'Papel',40,1),
(2,1,1,N'TEC-01',N'Teclado',150,1),
(1,2,1,N'MON-01',N'Monitor',1200,1);

INSERT INTO dbo.ProductoProveedores (producto_id,proveedor_id,costo) VALUES
(1,1,3000),
(2,2,40),
(3,1,20),
(4,2,80),
(5,1,800);

INSERT INTO dbo.Existencias (almacen_id,producto_id,cantidad,minimo) VALUES
(1,1,50,5),
(1,2,50,5),
(1,3,50,5),
(1,4,50,5),
(1,5,50,5),
(2,1,10,5),
(2,2,10,5),
(2,3,10,5),
(2,4,10,5),
(2,5,10,5);

INSERT INTO dbo.Compras (proveedor_id,almacen_id,empleado_id,fecha,estado) VALUES
(1,1,1,N'2026-10-01',N'PENDIENTE'),
(2,2,2,N'2026-10-02',N'PENDIENTE');

INSERT INTO dbo.DetalleCompra (compra_id,producto_id,cantidad,costo) VALUES
(1,1,5,3000),
(1,3,20,20),
(2,2,15,40),
(2,4,10,80);

INSERT INTO dbo.MetodosPago (nombre) VALUES
(N'Efectivo'),
(N'Tarjeta'),
(N'Transferencia');

COMMIT TRANSACTION;
GO

CREATE OR ALTER PROCEDURE dbo.RegistrarVenta
 @cliente_id INT, @almacen_id INT, @empleado_id INT, @metodo_pago_id INT,
 @referencia UNIQUEIDENTIFIER, @items NVARCHAR(MAX)
AS
BEGIN
 SET NOCOUNT ON;
 SET XACT_ABORT ON;
 BEGIN TRY
  BEGIN TRANSACTION;
  IF @referencia IS NULL THROW 51001,'Referencia obligatoria.',1;
  IF ISJSON(@items)<>1 OR LEFT(LTRIM(@items),1)<>'[' THROW 51001,'Se requiere un arreglo JSON.',1;
  DECLARE @lineas TABLE(producto_id INT PRIMARY KEY, cantidad INT NOT NULL CHECK(cantidad>0));
  IF EXISTS(SELECT 1 FROM OPENJSON(@items) WITH(producto_id INT, cantidad INT) WHERE producto_id IS NULL OR cantidad IS NULL OR cantidad<=0)
    THROW 51001,'Productos y cantidades invalidos.',1;
  IF EXISTS(SELECT producto_id FROM OPENJSON(@items) WITH(producto_id INT, cantidad INT) GROUP BY producto_id HAVING COUNT(*)>1)
    THROW 51001,'No se permiten productos repetidos.',1;
  INSERT @lineas SELECT producto_id,cantidad FROM OPENJSON(@items) WITH(producto_id INT, cantidad INT);
  IF NOT EXISTS(SELECT 1 FROM @lineas) THROW 51001,'Venta sin productos.',1;
  IF EXISTS(SELECT 1 FROM Ventas WITH(UPDLOCK,HOLDLOCK) WHERE referencia=@referencia)
    THROW 51002,'Referencia de venta ya utilizada.',1;
  IF NOT EXISTS(SELECT 1 FROM Clientes WHERE id=@cliente_id) THROW 51001,'Cliente inexistente.',1;
  IF NOT EXISTS(SELECT 1 FROM MetodosPago WHERE id=@metodo_pago_id) THROW 51001,'Metodo de pago inexistente.',1;
  IF NOT EXISTS(SELECT 1 FROM Empleados e JOIN Almacenes a ON a.sucursal_id=e.sucursal_id WHERE e.id=@empleado_id AND e.activo=1 AND a.id=@almacen_id)
    THROW 51001,'Empleado inactivo o de otra sucursal.',1;
  -- Bloqueos retenidos hasta COMMIT: otra venta no puede consumir el mismo saldo.
  IF EXISTS(SELECT 1 FROM @lineas l LEFT JOIN Productos p WITH(UPDLOCK,HOLDLOCK) ON p.id=l.producto_id
    LEFT JOIN Existencias e WITH(UPDLOCK,HOLDLOCK) ON e.producto_id=l.producto_id AND e.almacen_id=@almacen_id
    WHERE p.id IS NULL OR p.activo=0 OR e.id IS NULL OR e.cantidad<l.cantidad)
    THROW 51003,'Producto inactivo, inexistente o stock insuficiente.',1;
  INSERT Ventas(cliente_id,almacen_id,empleado_id,referencia) VALUES(@cliente_id,@almacen_id,@empleado_id,@referencia);
  DECLARE @id INT=CONVERT(INT,SCOPE_IDENTITY());
  INSERT DetalleVenta(venta_id,producto_id,cantidad,precio_unitario)
    SELECT @id,l.producto_id,l.cantidad,p.precio FROM @lineas l JOIN Productos p ON p.id=l.producto_id;
  UPDATE e SET cantidad=e.cantidad-l.cantidad FROM Existencias e JOIN @lineas l ON l.producto_id=e.producto_id WHERE e.almacen_id=@almacen_id;
  INSERT MovimientosInventario(almacen_id,producto_id,venta_id,cantidad) SELECT @almacen_id,producto_id,@id,-cantidad FROM @lineas;
  DECLARE @total DECIMAL(14,2)=(SELECT SUM(CONVERT(DECIMAL(14,2),cantidad)*precio_unitario) FROM DetalleVenta WHERE venta_id=@id);
  INSERT Pagos(venta_id,metodo_pago_id,monto) VALUES(@id,@metodo_pago_id,@total);
  COMMIT TRANSACTION;
  SELECT @id AS id,@total AS total,'CONFIRMADA' AS estado;
 END TRY
 BEGIN CATCH
  IF XACT_STATE()<>0 ROLLBACK TRANSACTION;
  THROW;
 END CATCH
END;
GO
CREATE OR ALTER PROCEDURE dbo.RecibirCompra @compra_id INT
AS
BEGIN
 SET NOCOUNT ON;
 SET XACT_ABORT ON;
 BEGIN TRY
  BEGIN TRANSACTION;
  DECLARE @estado NVARCHAR(12),@almacen INT,@empleado INT;
  SELECT @estado=estado,@almacen=almacen_id,@empleado=empleado_id FROM Compras WITH(UPDLOCK,HOLDLOCK) WHERE id=@compra_id;
  IF @estado IS NULL THROW 51004,'Compra inexistente.',1;
  IF @estado<>'PENDIENTE' THROW 51002,'Compra ya recibida.',1;
  IF NOT EXISTS(SELECT 1 FROM Empleados e JOIN Almacenes a ON a.sucursal_id=e.sucursal_id WHERE e.id=@empleado AND e.activo=1 AND a.id=@almacen)
    THROW 51001,'Empleado inactivo o de otra sucursal.',1;
  IF NOT EXISTS(SELECT 1 FROM DetalleCompra WITH(UPDLOCK,HOLDLOCK) WHERE compra_id=@compra_id) THROW 51001,'Compra sin detalle.',1;
  IF EXISTS(SELECT 1 FROM DetalleCompra d JOIN Productos p WITH(UPDLOCK,HOLDLOCK) ON p.id=d.producto_id WHERE d.compra_id=@compra_id AND p.activo=0)
    THROW 51001,'Compra con producto inactivo.',1;
  INSERT Existencias(almacen_id,producto_id,cantidad)
    SELECT @almacen,d.producto_id,0 FROM DetalleCompra d WHERE d.compra_id=@compra_id
    AND NOT EXISTS(SELECT 1 FROM Existencias e WITH(UPDLOCK,HOLDLOCK) WHERE e.almacen_id=@almacen AND e.producto_id=d.producto_id);
  UPDATE e SET cantidad=e.cantidad+d.cantidad FROM Existencias e
    JOIN DetalleCompra d ON d.producto_id=e.producto_id WHERE d.compra_id=@compra_id AND e.almacen_id=@almacen;
  INSERT MovimientosInventario(almacen_id,producto_id,compra_id,cantidad)
    SELECT @almacen,producto_id,@compra_id,cantidad FROM DetalleCompra WHERE compra_id=@compra_id;
  UPDATE Compras SET estado='RECIBIDA' WHERE id=@compra_id;
  COMMIT TRANSACTION;
  SELECT @compra_id AS id,'RECIBIDA' AS estado;
 END TRY
 BEGIN CATCH
  IF XACT_STATE()<>0 ROLLBACK TRANSACTION;
  THROW;
 END CATCH
END;
GO



-- Ventas y recepciones semilla usan la misma logica transaccional de la API.
DECLARE @v UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111111';
EXEC dbo.RegistrarVenta 1,1,1,1,@v,N'[{"producto_id":1,"cantidad":2},{"producto_id":2,"cantidad":3}]';
DECLARE @v2 UNIQUEIDENTIFIER = '22222222-2222-2222-2222-222222222222';
EXEC dbo.RegistrarVenta 2,2,2,2,@v2,N'[{"producto_id":4,"cantidad":1}]';
EXEC dbo.RecibirCompra 1;
GO
