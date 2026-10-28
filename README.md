# Inventario y ventas multisucursal

Proyecto final de Bases de Datos I: SQL Server + Python/FastAPI. Modelo de 24 tablas relacionadas en 3FN, cinco CRUD completos, dos procedimientos transaccionales y dos reportes de negocio.

Repositorio: https://github.com/BansheeUmg/Proyecto_Final_BD_API

## Requisitos

- Windows, Python 3.12 y SQL Server 2016 o posterior, compatibilidad 130 o superior (OPENJSON).
- Microsoft ODBC Driver 17 o 18 for SQL Server. Ajustar el nombre del controlador en `.env`.
- `sqlcmd` y una cuenta con permiso para crear una base nueva y sus objetos.
- La configuracion local utiliza `.\SQLEXPRESS` y autenticacion de Windows.

## Instalacion desde cero (PowerShell)

```powershell
git clone https://github.com/BansheeUmg/Proyecto_Final_BD_API.git
cd Proyecto_Final_BD_API
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
```

`requirements.txt` declara las dependencias directas. `requirements-lock.txt` fija las versiones verificadas, incluidas las herramientas de pruebas; puede instalarse con Python 3.12 en Windows. Para instalar solo la API: `pip install -r requirements.txt`.

Editar `.env` para la instancia elegida. Nunca subir ese archivo. La plantilla no contiene contrasenas: usa la identidad de Windows. Para autenticacion SQL se pueden especificar `UID` y `PWD` exclusivamente en el archivo local. `TrustServerCertificate=yes` permite el certificado local de SQL Express; en despliegues con certificado valido usar `TrustServerCertificate=no`.

## Crear la base y cargar datos

```powershell
sqlcmd -S '.\SQLEXPRESS' -E -C -b -f 65001 -i database\schema_and_data.sql
```

El script crea `InventarioFinal` si no existe, 24 tablas, indices, dos procedimientos y datos de demostracion en todas las tablas. Si ya contiene el modelo, se detiene sin borrar datos. **No volver a inicializar una base instalada.** `-b` es obligatorio para detener la ejecucion ante errores. La creacion de tablas y los INSERT de catalogos se ejecutan en una transaccion; los procedimientos y sus ventas semilla se crean despues, separados por GO.

`database/procedures.sql` contiene los mismos procedimientos para lectura o actualizacion independiente. Para aplicarlos:

```powershell
sqlcmd -S '.\SQLEXPRESS' -E -C -d InventarioFinal -b -f 65001 -i database\procedures.sql
```

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- Swagger: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json
- Estado del proceso: http://127.0.0.1:8000/health (no comprueba la conexion SQL).

`iniciar.ps1` inicia el servidor desde esta carpeta. El servicio se limita a la maquina local. El alcance academico no incluye autenticacion, autorizacion ni una interfaz grafica; antes de publicarlo en Internet se requieren esos controles.

## Endpoints

| Recurso | Operaciones |
|---|---|
| `/categorias`, `/marcas`, `/clientes`, `/proveedores`, `/productos` | POST, GET listado; GET, PUT, DELETE en `/{record_id}` |
| `/operaciones/ventas` | POST: venta, detalle, pago, descuento y movimientos atomicos |
| `/operaciones/compras/{compra_id}/recepcion` | POST: recibe compra y actualiza inventario |
| `/reportes/ventas-mensuales?min_total=0` | GET: ingresos y estadisticas por sucursal y mes |
| `/reportes/inventario-categorias?min_unidades=0` | GET: stock por categoria, sin duplicar productos |

Listados: `offset=0&limit=20`, limite 100. PUT reemplaza todos los campos. Respuestas: 200 consulta/edicion/recepcion, 201 creacion, 204 borrado, 400 validacion/integridad/regla de negocio, 404 inexistente, 500 error interno. Errores: `{"error":{"codigo":"...","mensaje":"..."}}`. No se exponen mensajes internos del controlador ni credenciales.

### Venta de ejemplo

Generar una referencia UUID nueva por venta. Una referencia reutilizada se rechaza para evitar dobles cargos (no se reenvia el resultado anterior).

```powershell
$venta = @{
  cliente_id=1; almacen_id=1; empleado_id=1; metodo_pago_id=1
  referencia=[guid]::NewGuid().ToString()
  items=@(@{producto_id=2; cantidad=1},@{producto_id=4; cantidad=2})
} | ConvertTo-Json -Depth 4
Invoke-RestMethod http://127.0.0.1:8000/operaciones/ventas -Method Post -ContentType 'application/json' -Body $venta
Invoke-RestMethod http://127.0.0.1:8000/operaciones/compras/2/recepcion -Method Post
```

La compra 1 ya esta recibida en los datos iniciales; la compra 2 esta pendiente. Recibirla dos veces devuelve 400.

## Pruebas reales

La base `InventarioFinalTests` es exclusiva de pruebas. Crear una sola vez con `database/test_schema.sql`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
sqlcmd -S '.\SQLEXPRESS' -E -C -b -f 65001 -i database\test_schema.sql
$env:TEST_ODBC_CONNECTION_STRING='DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\SQLEXPRESS;DATABASE=InventarioFinalTests;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes'
.\.venv\Scripts\python.exe -m pytest -q
```

Sin esa variable, las pruebas se omiten explicitamente. La suite comprueba el nombre de la base antes de modificar datos. Verifica los cinco ciclos CRUD, restricciones, validacion, documentos Swagger, reportes, venta y recepcion, referencia duplicada, rollback por stock y rollback tras una falla tardia inyectada en el pago. Dos conexiones simultaneas compiten por una unidad: una sola venta confirma. Las pruebas revierten cambios y limpian el producto temporal; las secuencias IDENTITY pueden dejar saltos normales.

## Estructura y documentos

```text
app/                  API, schemas, routers y servicios
database/             DDL, SP y datos; base de pruebas separada
docs/                 analisis, normalizacion, ER, PDF y validacion
tests/                integracion real con SQL Server
scripts/              generacion del PDF
build_project.py      catalogo fuente que regenera SQL y Mermaid
```

`docs/analisis.md` explica el dominio, alcance, reglas, DFs y normalizacion. `docs/diagrama_er.mmd` contiene todos los atributos y cardinalidades Mermaid; `docs/diagrama_er.md` permite verlo directamente en GitHub. `docs/Proyecto_Final.pdf` es el documento de entrega.

Los procedimientos validan las operaciones de negocio. El CRUD no permite editar existencias, ventas ni movimientos directamente. La cuenta de la aplicacion debe limitarse a los permisos necesarios; el usuario de Windows utilizado en esta demostracion tiene privilegios de desarrollo. Los roles modelados representan puestos del negocio, no un sistema de inicio de sesion.

## Referencias

- FastAPI: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Microsoft TRY/CATCH: https://learn.microsoft.com/en-us/sql/t-sql/language-elements/try-catch-transact-sql
- Microsoft XACT_ABORT: https://learn.microsoft.com/en-us/sql/t-sql/statements/set-xact-abort-transact-sql
- Bloqueos: https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide
