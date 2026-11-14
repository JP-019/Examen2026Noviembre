"""Dashboard web de ventas.

Consume `core-api` por HTTP. No importa pyodbc ni conoce SQL Server.

Ejecucion (desde services/dashboard):
    streamlit run app.py --server.port 8501
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from api_client import ApiError, CoreApi

st.set_page_config(
    page_title="Ventas - Plataforma de datos",
    page_icon=":bar_chart:",
    layout="wide",
)

api = CoreApi()

st.markdown(
    """
    <style>
    .stApp { background: #10141f; }
    [data-testid="stHeader"] { background: rgba(16, 20, 31, 0.96); }
    [data-testid="stSidebar"] {
        background: #171d29;
        border-right: 1px solid #283244;
    }
    .block-container { max-width: 1560px; padding-top: 1.6rem; padding-bottom: 3rem; }
    [data-testid="stMetric"] {
        background: #1b2432;
        border: 1px solid #2a3547;
        border-top: 3px solid #4f80e8;
        border-radius: 12px;
        padding: 14px 16px;
        min-height: 105px;
    }
    [data-testid="stMetricLabel"] p { color: #aebbd0; font-size: 0.84rem; }
    [data-testid="stMetricValue"] { color: #f3f6fc; }
    .st-key-primary-kpi-0 [data-testid="stMetric"] {
        border-top-color: #58c878;
        background: linear-gradient(135deg, #1d312c, #1b2432);
    }
    .st-key-primary-kpi-1 [data-testid="stMetric"] {
        border-top-color: #36c4b0;
        background: linear-gradient(135deg, #1b302f, #1b2432);
    }
    .st-key-primary-kpi-2 [data-testid="stMetric"] {
        border-top-color: #6d91ff;
        background: linear-gradient(135deg, #202c49, #1b2432);
    }
    .st-key-secondary-kpi-0 [data-testid="stMetric"],
    .st-key-secondary-kpi-1 [data-testid="stMetric"],
    .st-key-secondary-kpi-2 [data-testid="stMetric"] {
        background: #171f2c;
        border: 1px solid #283548;
        border-top: 1px solid #283548;
        min-height: 82px;
        padding: 10px 14px;
    }
    .st-key-secondary-kpi-0 [data-testid="stMetricValue"],
    .st-key-secondary-kpi-1 [data-testid="stMetricValue"],
    .st-key-secondary-kpi-2 [data-testid="stMetricValue"] { font-size: 1.2rem; }
    [data-testid="stMarkdownContainer"] h1 { letter-spacing: -0.035em; }
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 { color: #e7edf7; }
    div[data-testid="stPlotlyChart"] {
        background: #171f2c;
        border: 1px solid #283548;
        border-radius: 12px;
        padding: 8px;
    }
    hr { border-color: #293447; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _fmt_number(value: float, kind: str) -> str:
    if kind == "currency":
        return f"S/ {value:,.2f}"
    return f"{value:,.0f}"


def _periodo_desde_filtros() -> dict[str, str | None]:
    rango = st.session_state.get("rango")
    return {
        "desde": rango[0].isoformat() if rango else None,
        "hasta": rango[1].isoformat() if rango else None,
        "local": st.session_state.get("local"),
        "seccion": st.session_state.get("seccion"),
        "producto": st.session_state.get("producto"),
    }


def _cargar_filtros() -> dict | None:
    try:
        return api.filtros()
    except ApiError as exc:
        st.error(str(exc))
        st.info(
            "Arrancar la API:\n\n"
            "```powershell\ncd services/core-api\nuvicorn app.main:app --port 8000\n```"
        )
        return None


def _sidebar(opciones: dict) -> dict[str, str | None]:
    st.sidebar.markdown("### VENTAS")
    st.sidebar.caption("Plataforma de analítica")
    st.sidebar.divider()
    st.sidebar.header("Filtros")

    minimo = date.fromisoformat(opciones["desde"]) if opciones.get("desde") else date(2000, 1, 1)
    maximo = date.fromisoformat(opciones["hasta"]) if opciones.get("hasta") else date.today()

    rango = st.sidebar.date_input(
        "Periodo",
        value=(minimo, maximo),
        min_value=minimo,
        max_value=maximo,
    )
    if isinstance(rango, tuple) and len(rango) == 2:
        st.session_state["rango"] = rango
    else:
        st.session_state["rango"] = None

    st.session_state["local"] = st.sidebar.selectbox(
        "Local", ["Todos"] + opciones["locales"], key="sel_local"
    )
    st.session_state["seccion"] = st.sidebar.selectbox(
        "Seccion", ["Todas"] + opciones["secciones"], key="sel_seccion"
    )
    st.session_state["producto"] = st.sidebar.selectbox(
        "Producto", ["Todos"] + opciones["productos"], key="sel_producto"
    )

    for key in ("local", "seccion", "producto"):
        if st.session_state[key] in ("Todos", "Todas"):
            st.session_state[key] = None

    if st.sidebar.button("Limpiar filtros"):
        for key in ("rango", "local", "seccion", "producto", "page"):
            st.session_state.pop(key, None)
        st.rerun()

    return _periodo_desde_filtros()


def _cabecera(health: dict) -> None:
    actualizado = health.get("data_updated_at")
    if actualizado:
        try:
            actualizado = datetime.fromisoformat(actualizado).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    col1, col2 = st.columns([3, 1])
    col1.markdown(
        '<p style="color:#81a8ff;font-size:.78rem;font-weight:700;'
        'letter-spacing:.13em;margin-bottom:0">ANALÍTICA COMERCIAL</p>',
        unsafe_allow_html=True,
    )
    col1.title("Rendimiento de ventas")
    col1.caption("Indicadores confiables del Data Warehouse")
    col2.metric("Filas en el DW", f"{health.get('fact_rows', 0):,}")
    col2.caption(f"Última actualización: {actualizado or 'sin dato'}")
    if health.get("last_etl_status") and health["last_etl_status"] != "SUCCESS":
        st.warning(f"La ultima ejecucion del ETL termino en estado {health['last_etl_status']}.")
    else:
        st.caption("● Pipeline operativo · Datos servidos por core-api; sin conexión directa a SQL Server.")


def _kpi_cards(kpis: dict) -> None:
    valores = kpis.get("kpis", [])
    prioridades = ("Ventas totales", "Facturas", "Ticket promedio")
    principales = [kpi for label in prioridades for kpi in valores if kpi["label"] == label]
    if len(principales) != len(prioridades):
        principales = valores[:3]
    secundarios = [kpi for kpi in valores if kpi not in principales]

    columnas = st.columns(len(principales)) if principales else []
    for indice, (columna, kpi) in enumerate(zip(columnas, principales)):
        with columna.container(key=f"primary-kpi-{indice}"):
            st.metric(kpi["label"], _fmt_number(kpi["value"], kpi["format"]))

    if secundarios:
        columnas_secundarias = st.columns(len(secundarios))
        for indice, (columna, kpi) in enumerate(zip(columnas_secundarias, secundarios)):
            with columna.container(key=f"secondary-kpi-{indice}"):
                st.metric(kpi["label"], _fmt_number(kpi["value"], kpi["format"]))


def _seccion_tendencias(filtros: dict[str, str | None]) -> dict[str, Any] | None:
    granularidad = st.radio(
        "Periodo del gráfico",
        ["dia", "mes"],
        format_func=lambda value: "Diario" if value == "dia" else "Mensual",
        horizontal=True,
        key="granularidad_tendencia",
    )

    try:
        datos = api.tendencias(filtros, granularidad)
    except ApiError as exc:
        st.error(str(exc))
        return None
    serie = datos.get("serie", [])
    if not serie:
        st.info("No hay ventas para los filtros seleccionados.")
        return datos.get("comparacion", {})

    frame = pd.DataFrame(serie)
    figura = px.line(
        frame,
        x="periodo",
        y="ventas",
        markers=True,
        labels={"periodo": "Periodo", "ventas": "Ventas (S/)"},
        title="Evolución de ventas",
    )
    figura.update_traces(
        line=dict(color="#6d91ff", width=3),
        marker=dict(color="#81d4fa", size=8),
        hovertemplate="%{x}<br>Ventas: S/ %{y:,.2f}<extra></extra>",
    )
    figura.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#dce5f3",
        yaxis_tickprefix="S/ ",
        yaxis_gridcolor="#2b3546",
        xaxis_gridcolor="#202a39",
        margin=dict(t=55, b=20, l=12, r=12),
        title_font_size=15,
        showlegend=False,
    )
    st.plotly_chart(figura, width="stretch", config={"displayModeBar": False})
    return datos.get("comparacion", {})


def _seccion_locales(filtros: dict[str, str | None]) -> None:
    st.subheader("Ventas por local")
    try:
        datos = api.agrupado(filtros, "local")
    except ApiError as exc:
        st.error(str(exc))
        return
    grupos = datos.get("grupos", [])
    if not grupos:
        st.info("No hay ventas por local para los filtros seleccionados.")
        return

    frame = pd.DataFrame(grupos)
    total = frame["ventas"].sum()
    figura = px.pie(
        frame,
        names="valor",
        values="ventas",
        hole=0.68,
        color_discrete_sequence=["#5b83f5", "#31b9a2", "#e7b85c", "#e47777"],
    )
    figura.update_traces(
        textposition="outside",
        textinfo="percent",
        hovertemplate="%{label}<br>Ventas: S/ %{value:,.2f}<extra></extra>",
    )
    figura.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#dce5f3",
        showlegend=True,
        legend=dict(orientation="h", y=-0.12),
        margin=dict(t=10, b=10, l=10, r=10),
        annotations=[
            dict(
                text=f"S/ {total:,.0f}",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=17, color="#f3f6fc"),
            )
        ],
    )
    st.plotly_chart(figura, width="stretch", config={"displayModeBar": False})


def _seccion_resumen(comparacion: dict[str, Any] | None) -> None:
    st.subheader("Resumen del periodo")
    if not comparacion:
        st.info("No hay una comparación disponible para este periodo.")
        return

    actual = comparacion.get("actual")
    anterior = comparacion.get("anterior")
    variacion = comparacion.get("variacion_pct")
    if actual is None or anterior is None:
        st.info("No hay una comparación disponible para este periodo.")
        return

    izquierda, derecha = st.columns(2)
    izquierda.metric("Periodo actual", _fmt_number(actual, "currency"))
    derecha.metric("Periodo anterior", _fmt_number(anterior, "currency"))
    st.metric("Variación", "sin base" if variacion is None else f"{variacion:+.2f}%")


def _seccion_detalle(filtros: dict[str, str | None]) -> None:
    st.subheader("Detalle de lineas de venta")
    tamano = st.selectbox("Filas por pagina", [10, 25, 50, 100], index=1)
    pagina = st.number_input("Pagina", min_value=1, step=1, value=1)

    datos = api.detalle(filtros, page=int(pagina), page_size=int(tamano))
    if not datos.get("rows"):
        st.info("La pagina no tiene filas para los filtros seleccionados.")
        return

    st.caption(f"{datos['total']} lineas - pagina {datos['page']} de {max(datos['total_pages'], 1)}")
    frame = pd.DataFrame(datos["rows"]).rename(
        columns={
            "id_factura_detalle": "Linea",
            "numero_factura": "Factura",
            "fecha": "Fecha",
            "producto": "Producto",
            "local": "Local",
            "version": "Version",
            "cantidad": "Cantidad",
            "precio_unitario": "Precio unit.",
            "importe_linea": "Importe",
        }
    )
    st.dataframe(
        frame,
        width="stretch",
        hide_index=True,
        column_config={
            "Precio unit.": st.column_config.NumberColumn(format="%.2f"),
            "Importe": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.download_button(
        "Descargar pagina (CSV)",
        frame.to_csv(index=False).encode("utf-8"),
        file_name=f"ventas_pagina_{datos['page']}.csv",
        mime="text/csv",
    )


def main() -> None:
    try:
        health = api.health()
    except ApiError as exc:
        st.error(str(exc))
        st.info(
            "Arrancar la API:\n\n"
            "```powershell\ncd services/core-api\nuvicorn app.main:app --port 8000\n```"
        )
        return

    _cabecera(health)

    opciones = _cargar_filtros()
    if opciones is None:
        return

    filtros = _sidebar(opciones)

    try:
        kpis = api.kpis(filtros)
    except ApiError as exc:
        st.error(str(exc))
        return

    if all(kpi["value"] == 0 for kpi in kpis.get("kpis", [])):
        st.info("No hay datos para el periodo y filtros seleccionados. Probar otro rango.")
        return

    _kpi_cards(kpis)
    st.divider()
    izquierda, derecha = st.columns([1.8, 1])
    with izquierda:
        st.subheader("Tendencia de ventas")
        comparacion = _seccion_tendencias(filtros)
    with derecha:
        _seccion_locales(filtros)
    st.divider()
    _seccion_resumen(comparacion)

    st.divider()
    _seccion_detalle(filtros)

    st.divider()
    st.caption(
        "Las cifras provienen de dw.FactVentas a traves de core-api. "
        "Este tablero no calcula ni estima valores por su cuenta."
    )


main()
