# Validacion ejecutada

Fecha local: 27 de octubre de 2026. Entorno: Windows, Python 3.12, SQL Server SQLEXPRESS y ODBC Driver 17. Autenticacion integrada de Windows.

El script schema_and_data.sql se ejecuto satisfactoriamente con sqlcmd -b. Se instalaron la base InventarioFinal y una base independiente InventarioFinalTests con los mismos objetos. El modelo final contiene 24 tablas y dos procedimientos. Todas las tablas tienen datos iniciales; los datos de personas y empresas son ficticios.

Resultado de pytest: 15 passed. Se ejecutaron cinco ciclos CRUD completos, restricciones, validaciones, venta confirmada, recepcion confirmada, rechazo de reintentos y reportes con contraste de totales.

Rollback temprano: una venta con dos productos y stock insuficiente en una linea no altero cabecera, detalles, pagos, movimientos ni el saldo total.

Rollback tardio: un trigger temporal rechazo el pago despues del descuento de stock. La transaccion revirtio todos los cambios; se comprobaron conteos y saldos iguales al estado anterior.

Concurrencia: dos conexiones independientes intentaron vender la unica unidad de un producto temporal. Se confirmo una venta y se rechazo la otra por stock insuficiente. El saldo final fue cero y los registros temporales fueron eliminados.

Reportes sobre datos iniciales: ingresos totales Q 9,420.00, dos ventas; se verifico que el reporte de inventario no multiplica el numero de productos por los almacenes. El umbral de ingresos excluye grupos por HAVING.

Swagger /docs y /openapi.json devolvieron 200 durante las pruebas. Se verificaron 15 rutas y la respuesta personalizada 400 para validaciones. La suite usa conexiones reales a SQL Server, sin sustituir el motor por SQLite ni simular resultados SQL.

Se observo un aviso de deprecacion de la biblioteca de pruebas sobre httpx; no afecto las 15 comprobaciones. Las pruebas no se ejecutan si falta TEST_ODBC_CONNECTION_STRING y muestran explicitamente skipped en ese caso.

El esquema de roles no implementa autenticacion. La API se inicia en 127.0.0.1 para la demostracion local. No se realizo una publicacion del servicio en Internet.
