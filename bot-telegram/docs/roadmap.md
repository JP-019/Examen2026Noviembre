# 🗺️ Roadmap / Mejoras futuras

Lista viva de mejoras, ordenada por prioridad. Marca `[x]` al completar.

## Fase 1 — Refactor del monolito
- [ ] Separar `bot.js` en `handlers/` (comandos, callbacks, mensajes).
- [ ] Extraer teclados a `keyboards/`.
- [ ] Extraer lógica de negocio a `services/` internos (aún sin red).
- [ ] Extraer configuración a `config/`.
- [ ] Mover `orders.json` a `data/`.

## Fase 2 — Código limpio
- [ ] Añadir **ESLint** y **Prettier** con reglas del proyecto.
- [ ] Funciones pequeñas y con un solo propósito.
- [ ] Nombres claros y consistentes (español para negocio, inglés para técnico).
- [ ] Eliminar duplicación (formateo de precios, armado de textos).
- [ ] Usar `async/await` de forma consistente y centralizar errores.
- [ ] Comentarios solo donde aporten (el código debe explicarse solo).

## Fase 3 — Robustez
- [ ] Logger estructurado (niveles, contexto, sin datos sensibles).
- [ ] Manejo de errores por handler (que un fallo no tumbe el bot).
- [ ] Validación de entradas (teléfono, cantidades, fechas).
- [ ] Reintentos e idempotencia al crear pedidos.
- [ ] Persistir carritos/sesiones (Redis) para sobrevivir reinicios.
- [ ] Persistir **reservas** (hoy no se guardan).

## Fase 4 — Datos
- [ ] Migrar `orders.json` a PostgreSQL o MongoDB.
- [ ] Migraciones y semillas en `data/`.
- [ ] Índices por estado/fecha para el panel admin.
- [ ] Historial y auditoría de cambios de estado.

## Fase 5 — Microservicios
- [ ] Extraer `menu-service` (REST, solo lectura).
- [ ] Extraer `order-service` (REST + BD propia).
- [ ] Extraer `notification-service` (eventos/cola).
- [ ] Extraer `reservation-service`.
- [ ] Convertir el bot en `telegram-gateway`.
- [ ] Definir contratos en `packages/common`.
- [ ] Documentar cada ruta/endpoint en `routes/README.md`.

## Fase 6 — Calidad y despliegue
- [ ] Tests unitarios (menú, carrito, totales, estados).
- [ ] Tests de integración de flujos (checkout, reserva, panel admin).
- [ ] Docker + `docker-compose` para levantar todo.
- [ ] CI (lint + tests en cada push).
- [ ] Variables de entorno validadas al arrancar.

## Fase 7 — Seguridad
- [ ] Rotar el token de @BotFather si se expuso.
- [ ] Nunca versionar `.env` ni `orders.json`.
- [ ] Autorización de admin robusta (roles).
- [ ] Limitar tasa de mensajes por usuario.
- [ ] No registrar datos personales sensibles en logs.

## Ideas de producto (backlog)
- [ ] Pago en línea.
- [ ] Horarios de apertura/cierre automáticos.
- [ ] Seguimiento del pedido en tiempo real para el cliente.
- [ ] Cupones y promociones.
- [x] Panel web (dashboard) además de Telegram.
- [x] Exportar pedidos a Excel (.xlsx) y CSV con totales.
- [ ] Multi-sucursal.
