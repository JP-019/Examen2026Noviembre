# 💾 data/ — Persistencia

Aquí va todo lo relacionado con guardar datos.

## Estado actual
- Los pedidos se guardan en `orders.json` **en la raíz** (lo escribe `store.js`).
- Los carritos y sesiones viven en memoria (se pierden al reiniciar).

## Qué irá aquí (futuro)
```
data/
├── orders.json        # (mover desde la raíz)
├── migrations/        # cambios de esquema de la base de datos
└── seeds/             # datos de ejemplo (menú, pruebas)
```

## Por qué centralizarlo
Un solo lugar para saber dónde viven los datos. Facilita migrar de archivo JSON a
PostgreSQL/MongoDB sin buscar por todo el proyecto.

## Reglas
- `orders.json` **no** se versiona (ya está en `.gitignore`).
- Los datos de prueba van en `seeds/`, no mezclados con producción.
