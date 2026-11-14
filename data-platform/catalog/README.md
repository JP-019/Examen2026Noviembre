# catalog

Manifiesto unico de la plataforma. Lo consume el servicio `services/catalog` y el
generador `scripts/build_index.py`.

## Archivo

`platform.json` declara:

| Clave | Contenido |
|---|---|
| `name`, `version`, `process`, `architecture` | Identidad de la plataforma |
| `flow` | Orden del flujo de datos |
| `ports` | Puertos por servicio |
| `services` | Servicio: carpeta, tipo, estado, tarea, responsabilidad, funciones y endpoints |
| `folders` | Carpeta, proposito y contenido |
| `docs` | Documento, titulo y tarea |
| `tasks` | Tarea SCRUM, estado y artefactos |

## Regla de mantenimiento

1. Todo cambio de servicio o ruta se declara aca primero.
2. Se regenera el indice raiz: `python scripts/build_index.py`.
3. El servicio de catalogo lo publica en `http://localhost:8001/index.md`.

`platform.json` es la unica fuente de verdad: el `INDEX.md` de la raiz y el endpoint
`/index` se derivan de el.
