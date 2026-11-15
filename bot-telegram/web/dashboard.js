// Panel web (dashboard) de pedidos.
// Se monta dentro del mismo proceso del bot para compartir el estado de `store`
// y poder avisar al cliente cuando cambia un estado.
const express = require("express");
const path = require("path");
const ExcelJS = require("exceljs");
const { restaurant } = require("../menu");

const VALID_STATUSES = ["pendiente", "en_preparacion", "entregado", "cancelado"];

const STATUS_LABELS = {
  pendiente: "Pendiente",
  en_preparacion: "En preparación",
  entregado: "Entregado",
  cancelado: "Cancelado",
};

function dateKey(ts) {
  const d = new Date(ts);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function filterOrders(orders, { status, date }) {
  return orders.filter((o) => {
    if (status && status !== "todos" && o.status !== status) return false;
    if (date && dateKey(o.createdAt) !== date) return false;
    return true;
  });
}

function itemsToString(order) {
  return (order.items || []).map((it) => `${it.qty}x ${it.name}`).join(" | ");
}

function csvEscape(value) {
  const s = String(value == null ? "" : value);
  return /[",\n;]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function startDashboard({ port, store, token, onStatusChange }) {
  const app = express();
  app.use(express.json());

  function auth(req, res, next) {
    if (!token) return next();
    const provided = req.query.token || req.headers["x-dashboard-token"];
    if (String(provided) === String(token)) return next();
    return res.status(401).json({ error: "No autorizado" });
  }

  app.get("/api/health", (req, res) => res.json({ ok: true }));

  app.get("/api/config", auth, (req, res) => {
    res.json({
      restaurantName: restaurant.name,
      currency: restaurant.currency,
    });
  });

  app.get("/api/orders", auth, (req, res) => {
    const orders = filterOrders(store.getAll(), {
      status: req.query.status,
      date: req.query.date,
    });
    res.json(orders);
  });

  app.get("/api/stats", auth, (req, res) => {
    const orders = filterOrders(store.getAll(), {
      status: req.query.status,
      date: req.query.date,
    });
    const stats = {
      total: orders.length,
      pendiente: 0,
      en_preparacion: 0,
      entregado: 0,
      cancelado: 0,
      ventas: 0,
    };
    for (const o of orders) {
      if (stats[o.status] !== undefined) stats[o.status] += 1;
      if (o.status !== "cancelado") stats.ventas += Number(o.total) || 0;
    }
    res.json(stats);
  });

  app.patch("/api/orders/:number/status", auth, (req, res) => {
    const { number } = req.params;
    const { status } = req.body || {};
    if (!VALID_STATUSES.includes(status)) {
      return res.status(400).json({ error: "Estado inválido" });
    }
    const order = store.updateStatus(number, status);
    if (!order) {
      return res.status(404).json({ error: "Pedido no encontrado" });
    }
    try {
      if (onStatusChange) onStatusChange(order);
    } catch (err) {
      console.error("No se pudo avisar al cliente:", err.message);
    }
    res.json(order);
  });

  app.delete("/api/orders/:number", auth, (req, res) => {
    const order = store.deleteOrder(req.params.number);
    if (!order) {
      return res.status(404).json({ error: "Pedido no encontrado" });
    }
    res.json({ ok: true, number: order.number });
  });

  // ---------- Exportaciones ----------

  app.get("/api/export/csv", auth, (req, res) => {
    const orders = filterOrders(store.getAll(), {
      status: req.query.status,
      date: req.query.date,
    });

    const headers = [
      "N° Pedido",
      "Fecha",
      "Cliente",
      "Teléfono",
      "Tipo",
      "Ubicación",
      "Productos",
      "Subtotal",
      "Envío",
      "Total",
      "Estado",
    ];

    const lines = [headers.join(",")];
    for (const o of orders) {
      lines.push(
        [
          o.number,
          new Date(o.createdAt).toLocaleString("es-ES"),
          o.customerName,
          o.phone,
          o.type === "delivery" ? "Delivery" : "Retiro en local",
          o.address || "",
          itemsToString(o),
          o.subtotal,
          o.delivery,
          o.total,
          STATUS_LABELS[o.status] || o.status,
        ]
          .map(csvEscape)
          .join(",")
      );
    }

    // BOM para que Excel respete los acentos.
    const csv = "\uFEFF" + lines.join("\r\n");
    const name = `pedidos${req.query.date ? "-" + req.query.date : ""}.csv`;
    res.setHeader("Content-Type", "text/csv; charset=utf-8");
    res.setHeader("Content-Disposition", `attachment; filename="${name}"`);
    res.send(csv);
  });

  app.get("/api/export/xlsx", auth, async (req, res) => {
    try {
      const orders = filterOrders(store.getAll(), {
        status: req.query.status,
        date: req.query.date,
      });

      const wb = new ExcelJS.Workbook();
      wb.creator = restaurant.name;
      wb.created = new Date();
      const ws = wb.addWorksheet("Pedidos");

      ws.columns = [
        { header: "N° Pedido", key: "number", width: 12 },
        { header: "Fecha", key: "date", width: 20 },
        { header: "Cliente", key: "customer", width: 20 },
        { header: "Teléfono", key: "phone", width: 14 },
        { header: "Tipo", key: "type", width: 16 },
        { header: "Ubicación", key: "address", width: 28 },
        { header: "Productos", key: "items", width: 45 },
        { header: "Subtotal", key: "subtotal", width: 12 },
        { header: "Envío", key: "delivery", width: 10 },
        { header: "Total", key: "total", width: 12 },
        { header: "Estado", key: "status", width: 16 },
      ];

      for (const o of orders) {
        ws.addRow({
          number: o.number,
          date: new Date(o.createdAt).toLocaleString("es-ES"),
          customer: o.customerName,
          phone: o.phone,
          type: o.type === "delivery" ? "Delivery" : "Retiro en local",
          address: o.address || "",
          items: itemsToString(o),
          subtotal: o.subtotal,
          delivery: o.delivery,
          total: o.total,
          status: STATUS_LABELS[o.status] || o.status,
        });
      }

      const headerRow = ws.getRow(1);
      headerRow.font = { bold: true, color: { argb: "FFFFFFFF" } };
      headerRow.fill = {
        type: "pattern",
        pattern: "solid",
        fgColor: { argb: "FF1D2238" },
      };
      headerRow.alignment = { vertical: "middle" };
      headerRow.height = 20;

      ["H", "I", "J"].forEach((col) => {
        ws.getColumn(col).numFmt = `"${restaurant.currency}"#,##0.00`;
      });

      const total = orders.reduce((s, o) => s + (Number(o.total) || 0), 0);
      const totalRow = ws.addRow({ customer: "TOTAL", total });
      totalRow.font = { bold: true };
      totalRow.getCell("customer").alignment = { horizontal: "right" };

      ws.autoFilter = { from: "A1", to: "K1" };

      const name = `pedidos${req.query.date ? "-" + req.query.date : ""}.xlsx`;
      res.setHeader(
        "Content-Type",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      );
      res.setHeader("Content-Disposition", `attachment; filename="${name}"`);
      await wb.xlsx.write(res);
      res.end();
    } catch (err) {
      console.error("Error exportando Excel:", err);
      res.status(500).json({ error: "No se pudo generar el Excel" });
    }
  });

  app.use(express.static(path.join(__dirname, "public")));

  app.listen(port, () => {
    const suffix = token ? `?token=${token}` : "";
    console.log(`🌐 Dashboard de pedidos: http://localhost:${port}/${suffix}`);
  });

  return app;
}

module.exports = { startDashboard };
