# deployment

Despliegue local y, opcionalmente, contenedores.

## Estado

| Via | Estado | Nota |
|---|---|---|
| Local (SQL Server + Python) | **funcionando** | Es la via usada en la demo |
| Docker Compose | pendiente (T01) | Docker no esta instalado en el equipo |

## Arranque local

```powershell
# 1. Base de datos
sqlcmd -S localhost -E -C -i database/00_schemas.sql
sqlcmd -S localhost -E -C -i database/01_staging.sql
sqlcmd -S localhost -E -C -i database/02_dw.sql

# 2. ETL
cd services/etl
python -m app full
python -m app quality-report

# 3. Servicios
cd ../catalog
uvicorn app.main:app --port 8001
```

## Puertos

| Servicio | Puerto |
|---|---|
| core-api | 8000 |
| catalog | 8001 |
| ml | 8002 |
| genai | 8003 |
| alerting | 8004 |
| dashboard | 8501 |

## Variables

Copiar `.env.example` a `.env`. Nunca versionar `.env`.

## Seguridad de red y base de datos

`core-api`, `ml`, `genai` y `alerting` rechazan con HTTP 403 las solicitudes cuyo
cliente no sea loopback. Mantener el despliegue local; no exponer los puertos a
la LAN ni a Internet. Para un despliegue remoto se requiere autenticacion y
autorizacion en un proxy confiable, TLS y limites de solicitudes. La proteccion
local no reemplaza esos controles. Un proxy local sin autenticacion puede
eludirla porque el servicio ve la conexion del proxy como local.

La validacion del certificado SQL Server se exige para servidores remotos. El
valor `auto` solo confia en un certificado autofirmado cuando el servidor es
`localhost`, `127.0.0.1` o `::1`. No usar
`DW_TRUST_SERVER_CERTIFICATE=yes` para una conexion remota.

## Docker Compose (pendiente)

Cuando haya Docker disponible, el compose debe levantar:

1. `mssql` con la base `DataPlatform`.
2. Un contenedor por microservicio.
3. Red interna: solo `core-api` expone puerto al host.

No se versiona un compose sin probar: se agrega en T01 cuando el equipo tenga Docker.
