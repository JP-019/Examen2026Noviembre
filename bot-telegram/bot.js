require("dotenv").config();
const fs = require("fs");
const path = require("path");
const TelegramBot = require("node-telegram-bot-api");
const {
  restaurant,
  categories,
  findItem,
  findCategory,
} = require("./menu");
const store = require("./store");
const { startDashboard } = require("./web/dashboard");

const token = process.env.BOT_TOKEN;
const ADMIN_CHAT_ID = process.env.ADMIN_CHAT_ID || null;
const admins = ADMIN_CHAT_ID
  ? String(ADMIN_CHAT_ID)
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
  : [];
const isAdmin = (chatId) => admins.includes(String(chatId));

const STATUS_LABELS = {
  pendiente: "🕒 Pendiente",
  en_preparacion: "👨‍🍳 En preparación",
  entregado: "✅ Entregado",
  cancelado: "❌ Cancelado",
};

if (!token) {
  console.error("Falta BOT_TOKEN en el archivo .env");
  process.exit(1);
}

// ---------- Instancia única ----------
// Telegram admite un solo getUpdates por token: si el bot se abre dos veces
// responde "409 Conflict". Un archivo con el PID lo detecta antes de arrancar.
const LOCK_FILE = path.join(__dirname, ".bot.pid");

function pidAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (_) {
    return false;
  }
}

function acquireLock() {
  try {
    const pid = Number(fs.readFileSync(LOCK_FILE, "utf8").trim());
    if (pid && pid !== process.pid && pidAlive(pid)) {
      console.error(
        `Ya hay otra instancia del bot en ejecución (PID ${pid}).\n` +
          "Ciérrala con Ctrl+C antes de iniciar otra, o borra .bot.pid si quedó bloqueado."
      );
      process.exit(1);
    }
  } catch (_) {
    // Sin archivo de bloqueo (o ilegible): es la primera ejecución.
  }
  fs.writeFileSync(LOCK_FILE, String(process.pid), "utf8");
}

function releaseLock() {
  try {
    if (fs.readFileSync(LOCK_FILE, "utf8").trim() === String(process.pid)) {
      fs.unlinkSync(LOCK_FILE);
    }
  } catch (_) {}
}

acquireLock();
process.on("exit", releaseLock);
process.on("SIGINT", () => {
  releaseLock();
  process.exit(0);
});
process.on("SIGTERM", () => {
  releaseLock();
  process.exit(0);
});

const bot = new TelegramBot(token, { polling: true });

// ---------- Enlace para compartir el bot ----------
// Se obtiene una sola vez con getMe(). BOT_USERNAME en .env sirve de respaldo
// si Telegram no responde al arrancar.
let botUsername = process.env.BOT_USERNAME
  ? String(process.env.BOT_USERNAME).replace(/^@/, "")
  : null;

async function getBotUsername() {
  if (botUsername) return botUsername;
  try {
    const me = await bot.getMe();
    botUsername = me.username || null;
  } catch (err) {
    console.error("No se pudo obtener el usuario del bot:", err.message);
  }
  return botUsername;
}

// Abre el selector de chats de Telegram para reenviar el bot a contactos/grupos.
async function shareBotUrl() {
  const username = await getBotUsername();
  if (!username) return null;
  const link = `https://t.me/${username}`;
  const text = `🍔 Pide en ${restaurant.name} desde Telegram: menú, delivery y reservas.`;
  return (
    "https://t.me/share/url" +
    `?url=${encodeURIComponent(link)}` +
    `&text=${encodeURIComponent(text)}`
  );
}

// carrito por usuario: Map<chatId, Map<itemId, cantidad>>
const carts = new Map();
// sesiones (checkout / reserva): Map<chatId, {type, step, data}>
const sessions = new Map();

// Última interacción por chat. Telegram no avisa cuando alguien abre la
// conversación, así que saludamos en el primer mensaje tras un rato sin actividad
// (por defecto 30 minutos, configurable con WELCOME_GAP_MIN en .env).
const WELCOME_GAP_MS = (Number(process.env.WELCOME_GAP_MIN) || 30) * 60 * 1000;
const lastSeen = new Map();

// Registra la actividad y devuelve true si el cliente "vuelve" al bot.
function noteActivity(chatId) {
  const now = Date.now();
  const previous = lastSeen.get(chatId) || 0;
  lastSeen.set(chatId, now);
  return !previous || now - previous > WELCOME_GAP_MS;
}

const money = (n) => {
  const v = Number(n) || 0;
  return `${restaurant.currency}${Number.isInteger(v) ? v : v.toFixed(2)}`;
};
const esc = (s) => String(s == null ? "" : s).replace(/([_*`\[\]])/g, "\\$1");

function getCart(chatId) {
  if (!carts.has(chatId)) carts.set(chatId, new Map());
  return carts.get(chatId);
}

function cartSubtotal(cart) {
  let total = 0;
  for (const [itemId, qty] of cart) {
    const item = findItem(itemId);
    if (item) total += item.price * qty;
  }
  return total;
}

function cartCount(cart) {
  let n = 0;
  for (const qty of cart.values()) n += qty;
  return n;
}

// ---------- Teclados ----------

function mainKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "📖 Ver Menú", callback_data: "menu" }],
      [
        { text: "🛒 Mi Carrito", callback_data: "cart" },
        { text: "🍽️ Reservar", callback_data: "reserve" },
      ],
      [
        { text: "ℹ️ Información", callback_data: "info" },
        { text: "📞 Contacto", callback_data: "contact" },
      ],
    ],
  };
}

function categoriesKeyboard() {
  const rows = categories.map((c) => [
    { text: c.name, callback_data: `cat:${c.id}` },
  ]);
  rows.push([{ text: "⬅️ Volver", callback_data: "back:main" }]);
  return { inline_keyboard: rows };
}

function categoryKeyboard(category) {
  const rows = category.items.map((item) => [
    {
      text: `➕ ${item.name} — ${money(item.price)}`,
      callback_data: `add:${item.id}`,
    },
  ]);
  rows.push([
    { text: "🛒 Ver carrito", callback_data: "cart" },
    { text: "⬅️ Menú", callback_data: "menu" },
  ]);
  return { inline_keyboard: rows };
}

function cartKeyboard(cart) {
  const rows = [];
  for (const [itemId, qty] of cart) {
    const item = findItem(itemId);
    if (!item) continue;
    rows.push([
      { text: "➖", callback_data: `cart:dec:${itemId}` },
      { text: `${qty}`, callback_data: "noop" },
      { text: "➕", callback_data: `cart:inc:${itemId}` },
      { text: `🗑 ${item.name}`, callback_data: `cart:del:${itemId}` },
    ]);
  }
  rows.push([{ text: "🧹 Vaciar carrito", callback_data: "cart:clear" }]);
  rows.push([
    { text: "➕ Seguir pidiendo", callback_data: "menu" },
    { text: "✅ Finalizar pedido", callback_data: "checkout" },
  ]);
  rows.push([{ text: "⬅️ Volver", callback_data: "back:main" }]);
  return { inline_keyboard: rows };
}

function deliveryTypeKeyboard() {
  return {
    inline_keyboard: [
      [{ text: "🛵 Delivery", callback_data: "order:type:delivery" }],
      [{ text: "🏠 Retiro en local", callback_data: "order:type:pickup" }],
      [{ text: "❌ Cancelar", callback_data: "order:cancel" }],
    ],
  };
}

// Teclado para pedir la ubicación GPS por Telegram (abre Google Maps en el admin).
function locationKeyboard() {
  return {
    keyboard: [[{ text: "📍 Enviar mi ubicación", request_location: true }]],
    resize_keyboard: true,
    one_time_keyboard: true,
  };
}

function confirmKeyboard(prefix) {
  return {
    inline_keyboard: [
      [{ text: "✅ Confirmar", callback_data: `${prefix}:confirm` }],
      [{ text: "❌ Cancelar", callback_data: `${prefix}:cancel` }],
    ],
  };
}

// ---------- Vistas ----------

function welcomeText(firstName) {
  return (
    `¡Hola ${firstName || ""}! 👋\n\n` +
    `Bienvenido a *${restaurant.name}* 🍴\n\n` +
    `Aquí puedes ver nuestro menú, armar tu pedido y hacer reservas.\n\n` +
    `¿Qué deseas hacer?`
  );
}

function showMain(chatId, firstName) {
  bot.sendMessage(chatId, welcomeText(firstName), {
    parse_mode: "Markdown",
    reply_markup: mainKeyboard(),
  });
}

function categoryText(category) {
  let text = `*${category.name}*\n\n`;
  for (const item of category.items) {
    text += `• *${item.name}* — ${money(item.price)}\n`;
    if (item.description) text += `_${item.description}_\n`;
  }
  text += `\nToca un plato para agregarlo al carrito.`;
  return text;
}

function cartText(cart) {
  if (cart.size === 0) {
    return "🛒 Tu carrito está vacío.\n\nAgrega algo rico del menú 😋";
  }
  let text = "*🛒 Tu carrito*\n\n";
  for (const [itemId, qty] of cart) {
    const item = findItem(itemId);
    if (!item) continue;
    text += `• ${qty} x ${item.name} = ${money(item.price * qty)}\n`;
  }
  text += `\n*Subtotal: ${money(cartSubtotal(cart))}*`;
  return text;
}

// ---------- Helpers de edición ----------

async function editOrSend(query, text, keyboard) {
  const opts = { parse_mode: "Markdown" };
  if (keyboard) opts.reply_markup = keyboard;
  try {
    await bot.editMessageText(text, {
      chat_id: query.message.chat.id,
      message_id: query.message.message_id,
      ...opts,
    });
  } catch (e) {
    // Si el mensaje no cambió o no se puede editar, enviamos uno nuevo.
    await bot.sendMessage(query.message.chat.id, text, opts);
  }
}

// ---------- Comandos ----------

bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  sessions.delete(chatId);
  showMain(chatId, msg.from.first_name);
});

bot.onText(/\/menu/, (msg) => {
  bot.sendMessage(msg.chat.id, "*📖 Nuestro Menú*\n\nElige una categoría:", {
    parse_mode: "Markdown",
    reply_markup: categoriesKeyboard(),
  });
});

bot.onText(/\/carrito/, (msg) => {
  const chatId = msg.chat.id;
  const cart = getCart(chatId);
  bot.sendMessage(chatId, cartText(cart), {
    parse_mode: "Markdown",
    reply_markup: cart.size ? cartKeyboard(cart) : categoriesKeyboard(),
  });
});

bot.onText(/\/cancelar/, (msg) => {
  const chatId = msg.chat.id;
  if (sessions.delete(chatId)) {
    bot.sendMessage(chatId, "Operación cancelada. ✅", {
      reply_markup: mainKeyboard(),
    });
  } else {
    bot.sendMessage(chatId, "No hay ninguna operación en curso.");
  }
});

bot.onText(/\/compartir/, async (msg) => {
  const chatId = msg.chat.id;
  const username = await getBotUsername();
  const shareUrl = await shareBotUrl();
  if (!shareUrl) {
    return bot.sendMessage(
      chatId,
      "No pude generar el enlace para compartir. Intenta de nuevo en un momento."
    );
  }
  return bot.sendMessage(
    chatId,
    `📤 *Comparte ${restaurant.name}*\n\n` +
      (username ? `Enlace: \`https://t.me/${username}\`\n\n` : "") +
      `Toca el botón para reenviar el bot a un contacto o grupo.`,
    {
      parse_mode: "Markdown",
      reply_markup: {
        inline_keyboard: [[{ text: "📤 Compartir el bot", url: shareUrl }]],
      },
    }
  );
});

bot.onText(/\/miid/, (msg) => {
  bot.sendMessage(
    msg.chat.id,
    `Tu ID de Telegram es: \`${msg.chat.id}\`\n\n` +
      `Cópialo en ADMIN_CHAT_ID dentro del archivo .env para recibir los pedidos.`,
    { parse_mode: "Markdown" }
  );
});

// Panel de pedidos para el administrador
bot.onText(/\/pedidos/, (msg) => {
  const chatId = msg.chat.id;
  if (!isAdmin(chatId)) {
    return bot.sendMessage(
      chatId,
      "⛔ Este comando es solo para el administrador.\n\nTu ID es: " +
        `\`${chatId}\` (agrégalo a ADMIN_CHAT_ID en .env).`,
      { parse_mode: "Markdown" }
    );
  }
  sendAdminList(chatId, "todos");
});

bot.onText(/\/pendientes/, (msg) => {
  const chatId = msg.chat.id;
  if (!isAdmin(chatId)) return;
  sendAdminList(chatId, "pendiente");
});

// ---------- Callbacks (botones) ----------

bot.on("callback_query", async (query) => {
  const chatId = query.message.chat.id;
  const data = query.data;
  const cart = getCart(chatId);

  try {
    if (data === "noop") {
      return bot.answerCallbackQuery(query.id);
    }

    // ---------- Panel de pedidos (admin) ----------
    if (
      data === "admin:list" ||
      data.startsWith("admin:filter:") ||
      data.startsWith("admin:view:") ||
      data.startsWith("admin:status:")
    ) {
      if (!isAdmin(chatId)) {
        return bot.answerCallbackQuery(query.id, {
          text: "No autorizado",
          show_alert: true,
        });
      }

      if (data === "admin:list") {
        await bot.answerCallbackQuery(query.id);
        const { text, keyboard } = adminList("todos");
        return editOrSend(query, text, keyboard);
      }

      if (data.startsWith("admin:filter:")) {
        await bot.answerCallbackQuery(query.id);
        const filter = data.split(":")[2];
        const { text, keyboard } = adminList(filter);
        return editOrSend(query, text, keyboard);
      }

      if (data.startsWith("admin:view:")) {
        const number = data.split(":")[2];
        const order = store.getByNumber(number);
        await bot.answerCallbackQuery(query.id);
        if (!order) {
          return editOrSend(query, "Pedido no encontrado.", adminFilterKeyboard());
        }
        return editOrSend(
          query,
          orderDetailText(order),
          adminOrderKeyboard(order)
        );
      }

      if (data.startsWith("admin:status:")) {
        const parts = data.split(":");
        const number = parts[2];
        const status = parts[3];
        const order = store.updateStatus(number, status);
        if (!order) {
          return bot.answerCallbackQuery(query.id, {
            text: "Pedido no encontrado",
          });
        }
        await bot.answerCallbackQuery(query.id, {
          text: `Estado: ${STATUS_LABELS[status] || status}`,
        });
        notifyCustomerStatus(order);
        return editOrSend(
          query,
          orderDetailText(order),
          adminOrderKeyboard(order)
        );
      }
    }

    if (data === "back:main") {
      await bot.answerCallbackQuery(query.id);
      sessions.delete(chatId);
      return showMain(chatId, query.from.first_name);
    }

    if (data === "menu") {
      await bot.answerCallbackQuery(query.id);
      return editOrSend(
        query,
        "*📖 Nuestro Menú*\n\nElige una categoría:",
        categoriesKeyboard()
      );
    }

    if (data.startsWith("cat:")) {
      const category = findCategory(data.split(":")[1]);
      await bot.answerCallbackQuery(query.id);
      if (!category) return;
      return editOrSend(query, categoryText(category), categoryKeyboard(category));
    }

    if (data.startsWith("add:")) {
      const itemId = data.split(":")[1];
      const item = findItem(itemId);
      if (!item) return bot.answerCallbackQuery(query.id);
      cart.set(itemId, (cart.get(itemId) || 0) + 1);
      return bot.answerCallbackQuery(query.id, {
        text: `✅ ${item.name} agregado`,
      });
    }

    if (data === "cart") {
      await bot.answerCallbackQuery(query.id);
      return editOrSend(
        query,
        cartText(cart),
        cart.size ? cartKeyboard(cart) : categoriesKeyboard()
      );
    }

    if (data.startsWith("cart:inc:")) {
      const itemId = data.split(":")[2];
      cart.set(itemId, (cart.get(itemId) || 0) + 1);
      await bot.answerCallbackQuery(query.id);
      return editOrSend(query, cartText(cart), cartKeyboard(cart));
    }

    if (data.startsWith("cart:dec:")) {
      const itemId = data.split(":")[2];
      const qty = (cart.get(itemId) || 0) - 1;
      if (qty <= 0) cart.delete(itemId);
      else cart.set(itemId, qty);
      await bot.answerCallbackQuery(query.id);
      return editOrSend(
        query,
        cartText(cart),
        cart.size ? cartKeyboard(cart) : categoriesKeyboard()
      );
    }

    if (data.startsWith("cart:del:")) {
      const itemId = data.split(":")[2];
      cart.delete(itemId);
      await bot.answerCallbackQuery(query.id, { text: "Eliminado" });
      return editOrSend(
        query,
        cartText(cart),
        cart.size ? cartKeyboard(cart) : categoriesKeyboard()
      );
    }

    if (data === "cart:clear") {
      cart.clear();
      await bot.answerCallbackQuery(query.id, { text: "Carrito vaciado" });
      return editOrSend(query, cartText(cart), categoriesKeyboard());
    }

    if (data === "info") {
      await bot.answerCallbackQuery(query.id);
      return editOrSend(
        query,
        `*ℹ️ ${restaurant.name}*\n\n` +
          `🕒 Horario: ${restaurant.hours}\n` +
          `📍 Dirección: ${restaurant.address}\n` +
          `🛵 Delivery: ${restaurant.deliveryZones}\n` +
          `💵 Costo de envío: ${money(restaurant.deliveryFee)}`,
        {
          inline_keyboard: [
            [{ text: "📖 Ver menú", callback_data: "menu" }],
            [{ text: "⬅️ Volver", callback_data: "back:main" }],
          ],
        }
      );
    }

    if (data === "contact") {
      await bot.answerCallbackQuery(query.id);
      const username = await getBotUsername();
      const shareUrl = await shareBotUrl();
      const rows = [];
      if (shareUrl) {
        rows.push([{ text: "📤 Compartir el bot", url: shareUrl }]);
      }
      rows.push([{ text: "⬅️ Volver", callback_data: "back:main" }]);
      return editOrSend(
        query,
        `*📞 Contacto*\n\n` +
          `Teléfono: ${restaurant.phone}\n` +
          `Dirección: ${restaurant.address}\n\n` +
          (username
            ? `🔗 Enlace del bot: \`https://t.me/${username}\`\n\n`
            : "") +
          `¿Conoces a alguien que quiera pedir? Comparte el bot para que ` +
          `pueda escribirnos y hacer su pedido. 👇`,
        { inline_keyboard: rows }
      );
    }

    // ---------- Checkout ----------
    if (data === "checkout") {
      if (cart.size === 0) {
        await bot.answerCallbackQuery(query.id, {
          text: "Tu carrito está vacío",
          show_alert: true,
        });
        return;
      }
      await bot.answerCallbackQuery(query.id);
      sessions.set(chatId, { type: "checkout", step: "name", data: {} });
      return bot.sendMessage(
        chatId,
        "📝 Vamos a finalizar tu pedido.\n\n¿Cuál es tu *nombre*?",
        { parse_mode: "Markdown" }
      );
    }

    if (data.startsWith("order:type:")) {
      const session = sessions.get(chatId);
      if (!session || session.type !== "checkout") {
        return bot.answerCallbackQuery(query.id);
      }
      await bot.answerCallbackQuery(query.id);
      session.data.type = data.split(":")[2];
      if (session.data.type === "delivery") {
        session.step = "location";
        return bot.sendMessage(
          chatId,
          "📍 *Delivery*: comparte tu ubicación GPS para la entrega.\n\n" +
            "Toca el botón *Enviar mi ubicación* (o pega un enlace de Google Maps).",
          { parse_mode: "Markdown", reply_markup: locationKeyboard() }
        );
      }
      session.step = "phone";
      return bot.sendMessage(
        chatId,
        "🏠 *Retiro en local*.\n\n📞 ¿Cuál es tu *teléfono* de contacto?",
        { parse_mode: "Markdown", reply_markup: { remove_keyboard: true } }
      );
    }

    if (data === "order:confirm") {
      const session = sessions.get(chatId);
      if (!session || session.type !== "checkout") {
        return bot.answerCallbackQuery(query.id);
      }
      await bot.answerCallbackQuery(query.id);
      const order = buildOrder(chatId, session);
      store.addOrder(order);
      await notifyAdmins(
        `🔔 *NUEVO PEDIDO*\n\n` + orderDetailText(order),
        adminOrderKeyboard(order)
      );
      cart.clear();
      sessions.delete(chatId);
      return bot.sendMessage(
        chatId,
        `✅ *¡Pedido recibido!*\n\nTu número de pedido es *#${order.number}*.\n` +
          `En breve nos comunicamos contigo para confirmar. ¡Gracias! 🙌`,
        { parse_mode: "Markdown", reply_markup: mainKeyboard() }
      );
    }

    if (data === "order:cancel") {
      await bot.answerCallbackQuery(query.id);
      sessions.delete(chatId);
      return bot.sendMessage(chatId, "Pedido cancelado. ❌", {
        reply_markup: mainKeyboard(),
      });
    }

    // ---------- Reservas ----------
    if (data === "reserve") {
      await bot.answerCallbackQuery(query.id);
      sessions.set(chatId, { type: "reservation", step: "date", data: {} });
      return bot.sendMessage(
        chatId,
        "🍽️ *Nueva reserva*\n\n¿Para qué *fecha*? (ej: 2026-11-20 o \"viernes 20\")",
        { parse_mode: "Markdown" }
      );
    }

    if (data === "res:confirm") {
      const session = sessions.get(chatId);
      if (!session || session.type !== "reservation") {
        return bot.answerCallbackQuery(query.id);
      }
      await bot.answerCallbackQuery(query.id);
      const d = session.data;
      const adminText =
        `🍽️ *NUEVA RESERVA*\n\n` +
        `👤 Nombre: ${esc(d.name)}\n` +
        `📅 Fecha: ${esc(d.date)}\n` +
        `🕒 Hora: ${esc(d.time)}\n` +
        `👥 Personas: ${esc(d.people)}\n` +
        `🆔 Chat: ${chatId}`;
      await notifyAdmins(adminText);
      sessions.delete(chatId);
      return bot.sendMessage(
        chatId,
        "✅ *Reserva recibida.* Te confirmaremos en breve. ¡Gracias!",
        { parse_mode: "Markdown", reply_markup: mainKeyboard() }
      );
    }

    if (data === "res:cancel") {
      await bot.answerCallbackQuery(query.id);
      sessions.delete(chatId);
      return bot.sendMessage(chatId, "Reserva cancelada. ❌", {
        reply_markup: mainKeyboard(),
      });
    }

    return bot.answerCallbackQuery(query.id);
  } catch (err) {
    console.error("Error en callback:", err);
    try {
      await bot.answerCallbackQuery(query.id);
    } catch (_) {}
  }
});

// ---------- Checkout: resumen y construcción ----------

function checkoutSummary(chatId, session) {
  const cart = getCart(chatId);
  const d = session.data;
  const subtotal = cartSubtotal(cart);
  const delivery = d.type === "delivery" ? restaurant.deliveryFee : 0;

  let text = "*📝 Resumen de tu pedido*\n\n";
  for (const [itemId, qty] of cart) {
    const item = findItem(itemId);
    if (!item) continue;
    text += `• ${qty} x ${item.name} = ${money(item.price * qty)}\n`;
  }
  text += `\nSubtotal: ${money(subtotal)}\n`;
  if (delivery) text += `Envío: ${money(delivery)}\n`;
  text += `*Total: ${money(subtotal + delivery)}*\n\n`;
  text += `👤 Nombre: ${esc(d.name)}\n📞 Teléfono: ${esc(d.phone)}\n`;
  text += `🚚 Tipo: ${d.type === "delivery" ? "Delivery" : "Retiro en local"}\n`;
  if (d.type === "delivery") {
    text += `📍 Ubicación: ${d.mapLink || d.address || "No indicada"}\n`;
  }
  text += `\n¿Confirmas el pedido?`;
  return text;
}

function buildOrder(chatId, session) {
  const cart = getCart(chatId);
  const d = session.data;
  const subtotal = cartSubtotal(cart);
  const delivery = d.type === "delivery" ? restaurant.deliveryFee : 0;
  const number = String(Date.now()).slice(-6);

  const items = [];
  for (const [itemId, qty] of cart) {
    const item = findItem(itemId);
    if (item) items.push({ name: item.name, qty, price: item.price });
  }

  return {
    number,
    chatId: String(chatId),
    customerName: d.name,
    phone: d.phone,
    type: d.type,
    address: d.mapLink || d.address || null,
    location: d.location || null,
    mapLink: d.mapLink || null,
    items,
    subtotal,
    delivery,
    total: subtotal + delivery,
    status: "pendiente",
    createdAt: Date.now(),
  };
}

// ---------- Panel de pedidos (admin) ----------

function orderDetailText(order) {
  let text = `🧾 *Pedido #${order.number}*\n`;
  text += `Estado: ${STATUS_LABELS[order.status] || order.status}\n`;
  text += `Fecha: ${new Date(order.createdAt).toLocaleString("es-ES")}\n\n`;
  for (const it of order.items) {
    text += `• ${it.qty} x ${it.name} = ${money(it.price * it.qty)}\n`;
  }
  text += `\nSubtotal: ${money(order.subtotal)}\n`;
  if (order.delivery) text += `Envío: ${money(order.delivery)}\n`;
  text += `*Total: ${money(order.total)}*\n\n`;
  text += `👤 ${esc(order.customerName)}\n📞 ${esc(order.phone)}\n`;
  text += `🚚 ${order.type === "delivery" ? "Delivery" : "Retiro en local"}\n`;
  if (order.type === "delivery") {
    const link = order.mapLink || order.address;
    if (link) text += `📍 ${link}\n`;
  }
  text += `🆔 Chat: ${order.chatId}`;
  return text;
}

function adminOrderKeyboard(order) {
  const rows = [];
  const closed = order.status === "entregado" || order.status === "cancelado";
  if (!closed && order.status !== "en_preparacion") {
    rows.push([
      {
        text: "👨‍🍳 En preparación",
        callback_data: `admin:status:${order.number}:en_preparacion`,
      },
    ]);
  }
  if (!closed) {
    rows.push([
      {
        text: "✅ Marcar entregado",
        callback_data: `admin:status:${order.number}:entregado`,
      },
    ]);
    rows.push([
      {
        text: "❌ Cancelar pedido",
        callback_data: `admin:status:${order.number}:cancelado`,
      },
    ]);
  }
  rows.push([{ text: "⬅️ Ver todos los pedidos", callback_data: "admin:filter:todos" }]);
  return { inline_keyboard: rows };
}

function adminList(filter) {
  let list = store.getAll();
  if (filter && filter !== "todos") {
    list = list.filter((o) => o.status === filter);
  }

  if (!list.length) {
    return {
      text: "No hay pedidos en esta lista.",
      keyboard: adminFilterKeyboard(),
    };
  }

  let text = `*📋 Pedidos (${list.length})*\n\n`;
  for (const o of list.slice(0, 20)) {
    text += `#${o.number} · ${STATUS_LABELS[o.status] || o.status} · ${money(
      o.total
    )} · ${esc(o.customerName)}\n`;
  }
  if (list.length > 20) text += `\n_Mostrando los 20 más recientes._`;

  const rows = list.slice(0, 20).map((o) => [
    {
      text: `#${o.number} ${o.customerName} · ${money(o.total)}`,
      callback_data: `admin:view:${o.number}`,
    },
  ]);
  rows.push(...adminFilterKeyboard().inline_keyboard);
  return { text, keyboard: { inline_keyboard: rows } };
}

function adminFilterKeyboard() {
  return {
    inline_keyboard: [
      [
        { text: "🕒 Pendientes", callback_data: "admin:filter:pendiente" },
        { text: "👨‍🍳 Preparación", callback_data: "admin:filter:en_preparacion" },
      ],
      [
        { text: "✅ Entregados", callback_data: "admin:filter:entregado" },
        { text: "📋 Todos", callback_data: "admin:filter:todos" },
      ],
    ],
  };
}

function sendAdminList(chatId, filter) {
  const { text, keyboard } = adminList(filter);
  return bot.sendMessage(chatId, text, {
    parse_mode: "Markdown",
    reply_markup: keyboard,
  });
}

function notifyCustomerStatus(order) {
  let msg;
  if (order.status === "en_preparacion") {
    msg = `👨‍🍳 ¡Buenas noticias! Tu pedido #${order.number} está en preparación.`;
  } else if (order.status === "entregado") {
    msg = `✅ Tu pedido #${order.number} fue entregado. ¡Gracias por tu compra! 🙌`;
  } else if (order.status === "cancelado") {
    msg = `❌ Tu pedido #${order.number} fue cancelado. Disculpa las molestias.`;
  } else {
    msg = `Tu pedido #${order.number} ahora está: ${STATUS_LABELS[order.status] || order.status}`;
  }
  bot.sendMessage(order.chatId, msg).catch(() => {});
}


async function notifyAdmins(text, keyboard) {
  if (!admins.length) {
    console.warn(
      "ADMIN_CHAT_ID no configurado: el pedido no se envió al encargado."
    );
    return;
  }
  for (const admin of admins) {
    try {
      const opts = { parse_mode: "Markdown" };
      if (keyboard) opts.reply_markup = keyboard;
      await bot.sendMessage(admin, text, opts);
    } catch (err) {
      console.error(`No se pudo notificar al admin ${admin}:`, err.message);
    }
  }
}

// ---------- Mensajes de texto (flujos) ----------

bot.on("message", (msg) => {
  const chatId = msg.chat.id;
  const isReturning = noteActivity(chatId);
  const session = sessions.get(chatId);

  // Ubicación GPS compartida (flujo delivery)
  if (
    msg.location &&
    session &&
    session.type === "checkout" &&
    session.step === "location"
  ) {
    const lat = msg.location.latitude;
    const lng = msg.location.longitude;
    session.data.location = { lat, lng };
    session.data.mapLink = `https://maps.google.com/?q=${lat},${lng}`;
    session.step = "phone";
    return bot.sendMessage(
      chatId,
      "✅ Ubicación recibida.\n\n📞 ¿Cuál es tu *teléfono* de contacto?",
      { parse_mode: "Markdown", reply_markup: { remove_keyboard: true } }
    );
  }

  if (!msg.text || msg.text.startsWith("/")) return;

  if (!session) {
    // Si vuelve después de un rato (o es su primer mensaje), lo recibimos con el menú.
    if (isReturning) return showMain(chatId, msg.from && msg.from.first_name);
    return bot.sendMessage(
      chatId,
      "Usa el menú para navegar 👇",
      { reply_markup: mainKeyboard() }
    );
  }

  const text = msg.text.trim();

  if (session.type === "checkout") {
    if (session.step === "name") {
      session.data.name = text;
      session.step = "type";
      return bot.sendMessage(chatId, "🚚 ¿Cómo quieres recibir tu pedido?", {
        reply_markup: deliveryTypeKeyboard(),
      });
    }
    if (session.step === "location") {
      // El cliente pegó un enlace de Google Maps en vez de compartir GPS.
      session.data.mapLink = text;
      session.step = "phone";
      return bot.sendMessage(
        chatId,
        "✅ Ubicación guardada.\n\n📞 ¿Cuál es tu *teléfono* de contacto?",
        { parse_mode: "Markdown", reply_markup: { remove_keyboard: true } }
      );
    }
    if (session.step === "phone") {
      session.data.phone = text;
      session.step = "confirm";
      return bot.sendMessage(chatId, checkoutSummary(chatId, session), {
        parse_mode: "Markdown",
        reply_markup: confirmKeyboard("order"),
      });
    }
    return;
  }

  if (session.type === "reservation") {
    if (session.step === "date") {
      session.data.date = text;
      session.step = "time";
      return bot.sendMessage(chatId, "🕒 ¿A qué *hora*? (ej: 20:30)", {
        parse_mode: "Markdown",
      });
    }
    if (session.step === "time") {
      session.data.time = text;
      session.step = "people";
      return bot.sendMessage(chatId, "👥 ¿Para cuántas *personas*?", {
        parse_mode: "Markdown",
      });
    }
    if (session.step === "people") {
      session.data.people = text;
      session.step = "name";
      return bot.sendMessage(chatId, "👤 ¿A nombre de quién es la reserva?", {
        parse_mode: "Markdown",
      });
    }
    if (session.step === "name") {
      session.data.name = text;
      session.step = "confirm";
      const d = session.data;
      return bot.sendMessage(
        chatId,
        `*🍽️ Resumen de reserva*\n\n` +
          `👤 Nombre: ${esc(d.name)}\n📅 Fecha: ${esc(d.date)}\n` +
          `🕒 Hora: ${esc(d.time)}\n👥 Personas: ${esc(d.people)}\n\n¿Confirmas?`,
        { parse_mode: "Markdown", reply_markup: confirmKeyboard("res") }
      );
    }
  }
});

// ---------- Menú de comandos (☰) ----------
// Los comandos públicos los ve cualquier cliente; los de administración solo
// aparecen en el chat de cada admin (scope por chat).
const PUBLIC_COMMANDS = [
  { command: "start", description: "Volver al inicio" },
  { command: "menu", description: "Ver el menú y armar un pedido" },
  { command: "carrito", description: "Ver mi carrito" },
  { command: "cancelar", description: "Cancelar la operación en curso" },
  { command: "compartir", description: "Compartir el bot con un amigo" },
  { command: "miid", description: "Ver mi ID de Telegram" },
];

const ADMIN_COMMANDS = [
  { command: "pedidos", description: "Ver todos los pedidos" },
  { command: "pendientes", description: "Ver los pedidos pendientes" },
];

async function registerCommands() {
  try {
    await bot.setMyCommands(PUBLIC_COMMANDS);
    for (const admin of admins) {
      const chatId = Number(admin);
      if (!Number.isFinite(chatId)) continue;
      await bot.setMyCommands([...PUBLIC_COMMANDS, ...ADMIN_COMMANDS], {
        scope: { type: "chat", chat_id: chatId },
      });
    }
    console.log("☰ Comandos del bot actualizados.");
  } catch (err) {
    console.error("No se pudieron registrar los comandos:", err.message);
  }
}

// ---------- Arranque ----------

let lastPollingError = "";
let lastPollingErrorAt = 0;

bot.on("polling_error", (err) => {
  const message = err.message || String(err);
  const conflict = /409/.test(message) && /getUpdates/i.test(message);
  const now = Date.now();

  // node-telegram-bot-api reintenta solo: no repetimos el mismo error en cada intento.
  if (message === lastPollingError && now - lastPollingErrorAt < 60000) return;
  lastPollingError = message;
  lastPollingErrorAt = now;

  if (conflict) {
    console.error(
      "Conflicto de conexión:",
      message,
      "\nHay otro proceso usando el mismo BOT_TOKEN. Cierra las demás instancias del bot."
    );
    return;
  }
  console.error("Error de conexión:", message);
});

const dashboardPort = Number(process.env.DASHBOARD_PORT) || 3000;
startDashboard({
  port: dashboardPort,
  store,
  token: process.env.DASHBOARD_TOKEN || null,
  onStatusChange: (order) => notifyCustomerStatus(order),
});

registerCommands();

console.log(`🤖 Bot de ${restaurant.name} iniciado. Presiona Ctrl+C para detener.`);
