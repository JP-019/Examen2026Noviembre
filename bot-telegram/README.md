# 🍴 Mi Restaurante Bot

Bot de Telegram para un restaurante. Permite a los clientes ver el menú, armar un
carrito, hacer pedidos (delivery o retiro), reservar mesa y recibir avisos del
estado de su pedido. El administrador recibe cada pedido en tiempo real y puede
gestionarlo desde el propio chat.

> Documento vivo: aquí se va dejando el contexto del proyecto, el mapa de carpetas
> y las mejoras futuras (refactor, código limpio y microservicios).

---

## 1. ¿Qué hace la aplicación?

### Lado cliente
- `/start` — mensaje de bienvenida con menú principal.
- Ver el **menú** por categorías (Entradas, Clásicas, Especiales, Mamalonas, Bebidas, Promociones, etc.).
- **Carrito**: agregar, sumar, restar, quitar y vaciar productos.
- **Finalizar pedido**: nombre → delivery/retiro → (GPS si es delivery) → teléfono → confirmación.
- **Reservas**: fecha → hora → personas → nombre → confirmación.
- **Compartir el bot**: desde *Contacto* o `/compartir`, con el selector de chats de
  Telegram para reenviarlo a contactos y grupos.
- Recibe **avisos automáticos** cuando el restaurante cambia el estado de su pedido.

### Lado administrador
- Recibe cada **pedido nuevo** en su chat con botones de acción.
- `/pedidos` — panel con todos los pedidos y filtros por estado.
- `/pendientes` — solo los pedidos pendientes.
- Cambiar estado: `👨‍🍳 En preparación`, `✅ Entregado`, `❌ Cancelado`.
- `/miid` — obtiene el ID de Telegram para configurarlo como admin.
- **Panel web (dashboard)** en `http://localhost:3000/?token=...` para ver y
  gestionar pedidos desde el navegador, con auto-refresco.
- **Exportar a Excel/CSV** el cierre del día (con totales) desde el panel.

### Estados de un pedido
`pendiente` → `en_preparacion` → `entregado` (o `cancelado`).

---

## 2. Cómo funciona (flujo técnico)

```
Cliente (Telegram)
      │  comandos / botones
      ▼
   bot.js  ──►  menu.js      (catálogo de platos y precios)
      │    ──►  store.js     (guarda pedidos en orders.json)
      │
      ▼
Telegram API ──► chat del administrador (notificación + botones)
```

- **Carritos y sesiones** viven en memoria (`Map`) mientras el bot está encendido.
- **Pedidos** se persisten en `data`/`orders.json` (hoy en la raíz: `orders.json`).
- El administrador se configura con `ADMIN_CHAT_ID` (admite varios IDs separados por coma).

---

## 3. Puesta en marcha

```bash
npm install
npm start
```

Variables en `.env`:

| Variable        | Descripción                                             |
|-----------------|---------------------------------------------------------|
| `BOT_TOKEN`     | Token que entrega @BotFather. **Nunca lo compartas.**   |
| `ADMIN_CHAT_ID` | Uno o varios IDs de admin separados por coma.           |
| `BOT_USERNAME`  | (Opcional) usuario del bot sin `@`, para el enlace de compartir. Si falta, se obtiene con `getMe()`. |
| `DASHBOARD_PORT`| Puerto del panel web (por defecto `3000`).              |
| `DASHBOARD_TOKEN`| Token de acceso al panel (`?token=...` en la URL).     |

Para obtener tu ID: escribe `/miid` al bot y pégalo en `ADMIN_CHAT_ID`.

---

## 4. Estructura del proyecto (índice)

La raíz contiene el **monolito actual** (funciona ya). Las carpetas describen la
**arquitectura objetivo** y sirven de guía para el refactor a microservicios.

| Ruta | Qué contiene / qué irá aquí | Por qué |
|------|-----------------------------|---------|
| `bot.js` | Punto de entrada actual: comandos, callbacks, flujos. | Hoy concentra todo; se irá dividiendo por módulos. |
| `menu.js` | Catálogo de platos, precios y datos del restaurante. | Fuente de verdad del menú. |
| `store.js` | Persistencia de pedidos en `orders.json`. | Aísla el acceso a datos para poder cambiar a BD. |
| `web/` | Panel web (dashboard) de pedidos: API + interfaz. | Ver/gestionar pedidos desde el navegador. → [`web/README.md`](web/README.md) |
| `routes/` | **Índice de puntos de entrada** (comandos, callbacks, mensajes). | Saber qué ruta va a qué servicio y por qué. → [`routes/README.md`](routes/README.md) |
| `services/` | Un microservicio por dominio (bot, menú, pedidos, reservas, notificaciones). | Separar responsabilidades y escalar por partes. → [`services/README.md`](services/README.md) |
| `packages/` | Código compartido (utilidades, modelos, configuración). | Evitar duplicación entre servicios. → [`packages/README.md`](packages/README.md) |
| `data/` | Persistencia local / migraciones / semillas. | Un solo lugar para los datos. → [`data/README.md`](data/README.md) |
| `config/` | Configuración central, validación de variables de entorno. | Evitar configuración dispersa. → [`config/README.md`](config/README.md) |
| `docs/` | Documentación: arquitectura, roadmap, API. | Contexto para humanos y futuros cambios. → [`docs/README.md`](docs/README.md) |
| `tests/` | Pruebas unitarias e integración. | Verificar sin romper el bot. → [`tests/README.md`](tests/README.md) |

---

## 5. Arquitectura objetivo (microservicios)

```
                 ┌───────────────────────┐
                 │  telegram-gateway      │  recibe updates de Telegram
                 │  (webhook / polling)   │  y responde al usuario
                 └───────────┬───────────┘
                             │ HTTP / cola
        ┌────────────────────┼─────────────────────┐
        ▼                    ▼                     ▼
┌───────────────┐   ┌────────────────┐   ┌────────────────────┐
│ menu-service  │   │ order-service  │   │ reservation-service│
│ catálogo      │   │ pedidos/estados│   │ reservas           │
└───────────────┘   └───────┬────────┘   └────────────────────┘
                            │ eventos
                            ▼
                 ┌───────────────────────┐
                 │ notification-service   │  avisa al admin y al cliente
                 └───────────────────────┘
```

Reglas de la arquitectura:
- Cada servicio es dueño de **un dominio** y de sus datos.
- La comunicación es por **HTTP** (REST) o por **eventos** (cola).
- El **gateway** no contiene reglas de negocio: solo traduce Telegram ↔ servicios.
- `packages/common` guarda contratos y utilidades compartidas.

Detalle completo en [`docs/arquitectura.md`](docs/arquitectura.md).

---

## 6. Mejoras futuras (roadmap)

Resumen; detalle en [`docs/roadmap.md`](docs/roadmap.md).

1. **Refactor del monolito** → separar en módulos (`handlers/`, `keyboards/`, `services/`).
2. **Código limpio** → ESLint + Prettier, funciones pequeñas, nombres claros, sin duplicación.
3. **Manejo de errores y logs** → logger estructurado, reintentos, validación de entrada.
4. **Base de datos** → reemplazar `orders.json` por PostgreSQL/MongoDB.
5. **Tests** → unitarios (menú, carrito, totales) + integración de flujos.
6. **Microservicios** → extraer menu/order/reservation/notification + gateway.
7. **Docker / CI** → contenedores, docker-compose, pipeline de pruebas.
8. **Seguridad** → rotar token, no versionar `.env`, autorización de admin robusta.

---

## 7. Convenciones

- Código y documentación en **español** para el negocio; nombres técnicos en inglés si conviene.
- Commits pequeños y descriptivos.
- Nunca subir `.env` ni `orders.json` (ya están en `.gitignore`).
- Cada carpeta nueva debe traer su `README.md` explicando **qué va ahí y por qué**.
