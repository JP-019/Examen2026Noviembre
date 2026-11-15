# 🧪 tests/ — Pruebas

**Propósito:** verificar que el bot y los futuros servicios funcionan sin romper
flujos existentes.

## Qué se probará
### Unitarias
- `menu.js`: `findItem`, `findCategory`, `allItems`.
- Totales: `cartSubtotal`, subtotal + envío = total.
- `store.js`: `addOrder`, `getByNumber`, `updateStatus`.
- Utilidades: `money`, `esc`.

### Integración
- Flujo de checkout completo (carrito → datos → confirmación → pedido guardado).
- Cambio de estado y aviso al cliente.
- Flujo de reserva.
- Panel admin: listar, filtrar, ver y cambiar estado.

## Estructura sugerida
```
tests/
├── unit/
│   ├── menu.test.js
│   ├── cart.test.js
│   └── store.test.js
└── integration/
    ├── checkout.test.js
    └── admin.test.js
```

## Herramientas sugeridas
- **Vitest** o **Jest** como runner.
- `supertest` cuando existan APIs de los microservicios.
- Datos de prueba en `data/seeds/` (nunca contra producción).

## Regla
Cada nueva ruta documentada en `routes/README.md` debería tener al menos una prueba.
