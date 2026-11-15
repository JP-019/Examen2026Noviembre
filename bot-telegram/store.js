// Persistencia simple de pedidos en orders.json
const fs = require("fs");
const path = require("path");

const FILE = path.join(__dirname, "orders.json");

function load() {
  try {
    const raw = fs.readFileSync(FILE, "utf8");
    const data = JSON.parse(raw);
    return Array.isArray(data) ? data : [];
  } catch (e) {
    return [];
  }
}

let orders = load();

function save() {
  fs.writeFileSync(FILE, JSON.stringify(orders, null, 2), "utf8");
}

function addOrder(order) {
  orders.push(order);
  save();
  return order;
}

function getAll() {
  return [...orders].sort((a, b) => b.createdAt - a.createdAt);
}

function getByNumber(number) {
  return orders.find((o) => String(o.number) === String(number));
}

function updateStatus(number, status) {
  const order = getByNumber(number);
  if (!order) return null;
  order.status = status;
  order.updatedAt = Date.now();
  save();
  return order;
}

function deleteOrder(number) {
  const index = orders.findIndex((o) => String(o.number) === String(number));
  if (index === -1) return null;
  const [removed] = orders.splice(index, 1);
  save();
  return removed;
}

module.exports = { addOrder, getAll, getByNumber, updateStatus, deleteOrder };
