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
