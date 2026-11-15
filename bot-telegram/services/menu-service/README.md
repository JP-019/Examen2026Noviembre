# 📖 menu-service

**Propósito:** ser la fuente de verdad del catálogo: categorías, platos, precios y
datos del restaurante (horario, dirección, teléfono, costo de envío).

## Responsabilidad
- Exponer categorías y platos.
- Validar que un `itemId` exista y devolver su precio.
- Guardar datos del local (configuración comercial).

## Entradas / Salidas
- **Entrada:** `GET /menu`, `GET /menu/:categoryId`, `GET /menu/items/:itemId`.
- **Salida:** JSON con platos y precios.

## Datos que posee
- Categorías y platos (hoy en `menu.js`).
- Datos del restaurante (`restaurant`).

## Código actual
`menu.js` (`categories`, `restaurant`, `allItems`, `findItem`, `findCategory`).

## Por qué separarlo
Es de solo lectura y cambia poco: ideal como primer microservicio. Permite editar
el menú sin tocar el bot ni reiniciar los pedidos.

## Futuro
- Mover el menú a base de datos.
- Añadir panel para editar precios.
- Cachear respuestas (los precios cambian poco).
