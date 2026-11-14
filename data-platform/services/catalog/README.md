# Servicio de catalogo

Microservicio de solo lectura que responde: **que hace cada carpeta, que funciones
tiene cada servicio y que rutas existen**. Su fuente es `catalog/platform.json`.

## Arranque

Desde `services/catalog`:

```powershell
python -m pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload
```

- Swagger: <http://localhost:8001/docs>
- Indice legible: <http://localhost:8001/index.md>
- Indice JSON: <http://localhost:8001/index>
- Mapa de carpetas: <http://localhost:8001/map>
- Rutas de toda la plataforma: <http://localhost:8001/routes>

## Por que existe

En una arquitectura de microservicios cada servicio vive en su carpeta. El catalogo
evita que el conocimiento quede disperso: un unico manifiesto declara el estado de
cada servicio, sus funciones y sus endpoints, y este servicio lo publica.

## Contrato

| Ruta API | Devuelve |
|---|---|
| `GET /` | Resumen: cantidad de servicios, implementados y enlaces |
| `GET /health` | Estado del servicio |
| `GET /index` | Manifiesto completo |
| `GET /index.md` | Indice en Markdown |
| `GET /map` | Carpetas con proposito y contenido |
| `GET /services` | Lista resumida de servicios |
| `GET /services/{id}` | Detalle con funciones y endpoints |
| `GET /routes` | Rutas HTTP aplanadas |

## Mantenimiento

1. Todo cambio de servicio se declara primero en `catalog/platform.json`.
2. Se regenera el indice raiz: `python scripts/build_index.py`.
3. El catalogo no accede a la base de datos ni contiene secretos.
