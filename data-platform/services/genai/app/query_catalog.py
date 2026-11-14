"""Definiciones publicadas de las consultas aprobadas del asistente."""

from __future__ import annotations

from typing import Any

QUERY_CATALOG: list[dict[str, Any]] = [
    {
        "intent": "ventas_totales",
        "descripcion": "Ventas, lineas y facturas del periodo.",
        "endpoint": "GET /api/v1/kpis",
        "ejemplo": "cuanto vendimos en total",
    },
    {
        "intent": "facturas",
        "descripcion": "Cantidad de facturas y ventas asociadas.",
        "endpoint": "GET /api/v1/kpis",
        "ejemplo": "cuantas facturas hay",
    },
    {
        "intent": "ticket_promedio",
        "descripcion": "Importe promedio por factura.",
        "endpoint": "GET /api/v1/kpis",
        "ejemplo": "cual es el ticket promedio",
    },
    {
        "intent": "unidades",
        "descripcion": "Unidades vendidas y productos distintos.",
        "endpoint": "GET /api/v1/kpis",
        "ejemplo": "cuantas unidades se vendieron",
    },
    {
        "intent": "top_productos",
        "descripcion": "Ranking de productos por ventas.",
        "endpoint": "GET /api/v1/agrupado?dimension=producto",
        "ejemplo": "ranking de productos mas vendidos",
    },
    {
        "intent": "ventas_por_local",
        "descripcion": "Ventas agregadas por local.",
        "endpoint": "GET /api/v1/agrupado?dimension=local",
        "ejemplo": "ventas por local",
    },
    {
        "intent": "ventas_por_seccion",
        "descripcion": "Ventas agregadas por seccion.",
        "endpoint": "GET /api/v1/agrupado?dimension=seccion",
        "ejemplo": "ventas por seccion",
    },
    {
        "intent": "ventas_por_producto",
        "descripcion": "Ventas de un producto del catalogo.",
        "endpoint": "GET /api/v1/kpis?producto=...",
        "ejemplo": "cuanto vendio Mini Lorito",
    },
    {
        "intent": "tendencia",
        "descripcion": "Serie mensual de ventas.",
        "endpoint": "GET /api/v1/tendencias?granularidad=mes",
        "ejemplo": "tendencia mensual de ventas",
    },
    {
        "intent": "comparacion",
        "descripcion": "Comparacion de ventas entre dos anios.",
        "endpoint": "GET /api/v1/kpis (dos periodos)",
        "ejemplo": "comparar 2007 vs 2008",
    },
    {
        "intent": "no_data",
        "descripcion": "Rechazo explicito de preguntas fuera de alcance o sin datos.",
        "endpoint": "(ninguno)",
        "ejemplo": "como va el clima",
    },
]
