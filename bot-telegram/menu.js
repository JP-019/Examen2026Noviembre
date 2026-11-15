// ============================================================
//  CONFIGURACION DEL RESTAURANTE Y MENU
//  Menú real de "El Gordo". Edita este archivo para personalizar.
// ============================================================

const restaurant = {
  name: "El Gordo",
  phone: "8953-3602", // WhatsApp
  address: "Consultar por WhatsApp",
  hours: "Consultar horario por WhatsApp",
  currency: "L.",
  deliveryFee: 0,
  deliveryZones: "Consultar zona de entrega por WhatsApp",
};

// Cada categoria tiene un id unico, un nombre y una lista de platos.
// Cada plato necesita un id unico, nombre, descripcion y precio.
const categories = [
  {
    id: "entradas",
    name: "🍟 Entradas",
    items: [
      { id: "e1", name: "Mozzarella Sticks", description: "Dedos de queso empanizados", price: 150 },
      { id: "e2", name: "Aros de Cebolla", description: "Aros de cebolla crujientes", price: 150 },
      {
        id: "e3",
        name: "Sampler",
        description:
          "4 aros de cebolla, 4 mozzarella sticks, 6 alitas, 1 clásica y 1 orden de papas. Añade una clásica por L.140",
        price: 380,
      },
    ],
  },
  {
    id: "economicos",
    name: "💸 Económicos",
    items: [
      {
        id: "ec1",
        name: "Cheeseburger",
        description: "Hamburguesa de res y queso con 4 oz de papa",
        price: 150,
      },
      { id: "ec2", name: "Papa El Gordo", description: "Orden de papas de la casa", price: 150 },
    ],
  },
  {
    id: "clasicas",
    name: "🍔 Clásicas",
    items: [
      {
        id: "c1",
        name: "Clásica El Gordo",
        description: "Carne de res, queso cheddar y vegetales frescos",
        price: 185,
      },
      {
        id: "c2",
        name: "Crispy Chicken",
        description: "Pollo crispy, queso cheddar y vegetales frescos",
        price: 185,
      },
      {
        id: "c3",
        name: "Pulled Pork",
        description: "Cerdo desmechado en salsa BBQ, queso cheddar y vegetales frescos",
        price: 190,
      },
    ],
  },
  {
    id: "salsas",
    name: "🥫 Salsas",
    items: [
      { id: "s1", name: "BBQ", description: "Salsa barbacoa", price: 35 },
      { id: "s2", name: "Búfalo", description: "Salsa búfalo", price: 35 },
      { id: "s3", name: "Ranch", description: "Aderezo ranch", price: 35 },
      { id: "s4", name: "El Gordo", description: "Salsa de la casa", price: 35 },
    ],
  },
  {
    id: "especiales",
    name: "⭐ Especiales",
    items: [
      {
        id: "esp1",
        name: "Bacon & Cheese",
        description: "Carne de res, tocino, queso cheddar y cebolla caramelizada",
        price: 225,
      },
      {
        id: "esp2",
        name: "Jalapeño & Cheese",
        description: "Carne de res, queso mozzarella, jalapeños, tocino y cebolla caramelizada",
        price: 230,
      },
      {
        id: "esp3",
        name: "La Maradona",
        description: "Carne de res, queso mozzarella y chorizo argentino con chimichurri",
        price: 230,
      },
      {
        id: "esp4",
        name: "Satélite Deluxe",
        description:
          "Hamburguesa de res con aros de cebolla rebosados en cerveza, salsa BBQ y salsa El Gordo",
        price: 230,
      },
      {
        id: "esp5",
        name: "La Suiza",
        description: "Hamburguesa de res con hongos salteados, queso suizo y bacon",
        price: 235,
      },
      {
        id: "esp6",
        name: "Whisky Bacon Jam",
        description: "Pan brioche, carne de res, queso americano, mermelada de tocino y whisky",
        price: 250,
      },
    ],
  },
  {
    id: "alitas",
    name: "🍗 Alitas & Boneless",
    items: [
      {
        id: "a1",
        name: "6 Alitas",
        description:
          "Bañadas en la salsa de tu preferencia con papas fritas. Elige BBQ o Búfalo. Incluye salsa Ranch",
        price: 215,
      },
      {
        id: "a2",
        name: "12 Alitas",
        description:
          "Bañadas en la salsa de tu preferencia con papas fritas. Elige BBQ o Búfalo. Incluye salsa Ranch",
        price: 330,
      },
    ],
  },
  {
    id: "loaded_fries",
    name: "🍟 Loaded Fries",
    items: [
      {
        id: "lf1",
        name: "Papas con Cerdo",
        description: "Papas con queso cheddar, mozzarella, parmesano, aceitunas y jalapeños",
        price: 250,
      },
      {
        id: "lf2",
        name: "Papas con Pollo",
        description: "Papas con queso cheddar, mozzarella, parmesano, aceitunas y jalapeños",
        price: 235,
      },
      {
        id: "lf3",
        name: "Papas con Chorizo",
        description: "Papas con queso cheddar, mozzarella, parmesano, aceitunas y jalapeños",
        price: 220,
      },
      {
        id: "lf4",
        name: "Chicken Papa",
        description: "Papas con trozos de pollo en salsa BBQ, salsa cheddar y salsa El Gordo",
        price: 180,
      },
    ],
  },
  {
    id: "sandwiches",
    name: "🥪 Chicken Sandwich",
    items: [
      {
        id: "sw1",
        name: "Chicken BLT",
        description: "Pollo crispy, bacon, lechuga, tomate, queso suizo y aderezo ranch",
        price: 215,
      },
      {
        id: "sw2",
        name: "Chicken BBQ",
        description: "Pollo frito en salsa BBQ y aderezo ranch",
        price: 180,
      },
      {
        id: "sw3",
        name: "Chicken Búfalo",
        description: "Pollo frito en salsa búfalo y aderezo ranch",
        price: 180,
      },
    ],
  },
  {
    id: "combo",
    name: "👨‍👩‍👧 Combo Familiar",
    items: [
      {
        id: "combo1",
        name: "Combo Familiar",
        description: "4 hamburguesas clásicas de res + papas + refresco 2L",
        price: 700,
      },
    ],
  },
  {
    id: "mamalonas",
    name: "💪 Mamalonas",
    items: [
      {
        id: "m1",
        name: "Hamburguesa Doble",
        description: "Hamburguesa doble de res y queso",
        price: 240,
      },
      {
        id: "m2",
        name: "Hamburguesa Triple",
        description: "Triple carne de res, triple queso",
        price: 255,
      },
      {
        id: "m3",
        name: "Moab",
        description:
          "Doble carne, doble queso, tocino, aros de cebolla rebosados en cerveza con salsa BBQ",
        price: 285,
      },
      {
        id: "m4",
        name: "Olanchana",
        description: "Carne de res, queso suizo, chorizo, chuleta ahumada y chimichurri",
        price: 285,
      },
      {
        id: "m5",
        name: "Whisky Bacon Jam Doble",
        description:
          "Pan brioche, doble carne de res, doble queso americano, mermelada de tocino y whisky",
        price: 290,
      },
      {
        id: "m6",
        name: "Hot Cheese Triple",
        description:
          "Triple carne de res, tres tipos de queso, triple bacon y cebolla caramelizada",
        price: 300,
      },
    ],
  },
  {
    id: "bebidas",
    name: "🥤 Bebidas",
    items: [
      { id: "b1", name: "Té Frío", description: "Vaso de té frío", price: 35 },
      { id: "b2", name: "Limonada", description: "Limonada natural", price: 38 },
      { id: "b3", name: "Refresco Vidrio", description: "Botella de vidrio", price: 30 },
      { id: "b4", name: "Coca Cola", description: "Coca Cola", price: 38 },
      { id: "b5", name: "Canada Dry", description: "Canada Dry", price: 38 },
      { id: "b6", name: "Fresca", description: "Fresca", price: 38 },
      { id: "b7", name: "Agua", description: "Botella de agua", price: 22 },
    ],
  },
  {
    id: "promociones",
    name: "🔥 Promociones",
    items: [
      {
        id: "pr1",
        name: "Combo Diario",
        description: "Todos los días: 1 Cheeseburger + papas + 1 té frío",
        price: 170,
      },
      {
        id: "pr2",
        name: "Martes 2x1 Bacon",
        description: "Martes: 2x1 Hamburguesa con bacon",
        price: 260,
      },
      {
        id: "pr3",
        name: "Miércoles 2 Cheeseburgers",
        description:
          "Miércoles: 2 Cheeseburgers + 2 papas (2 refrescos de vidrio o té frío)",
        price: 300,
      },
      {
        id: "pr4",
        name: "Jueves Hongos",
        description: "Jueves: 2 Hamburguesas con hongos",
        price: 300,
      },
      {
        id: "pr5",
        name: "Combo Olanchana + Alitas",
        description:
          "Todos los días: 2 Olanchanas + 6 alitas + 2 refrescos naturales gratis",
        price: 570,
      },
    ],
  },
];

function allItems() {
  return categories.flatMap((c) => c.items);
}

function findItem(itemId) {
  return allItems().find((i) => i.id === itemId);
}

function findCategory(categoryId) {
  return categories.find((c) => c.id === categoryId);
}

module.exports = { restaurant, categories, allItems, findItem, findCategory };
