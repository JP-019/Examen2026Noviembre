"""Render HTML de la vista de monitoreo (sin dependencias externas)."""

from __future__ import annotations

from html import escape
from typing import Any

CSS = """
body { font-family: Segoe UI, Arial, sans-serif; margin: 24px; color: #1f2933; background: #f7f9fb; }
h1 { margin: 0 0 4px; font-size: 24px; }
h2 { font-size: 16px; margin: 0 0 8px; }
p { margin: 4px 0; }
.meta { color: #52606d; font-size: 13px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin: 18px 0; }
.card { background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; padding: 14px; }
.kpi { font-size: 22px; font-weight: 600; }
.ok { color: #0b7a4b; }
.warn { color: #a15c00; }
.crit { color: #b42318; }
table { border-collapse: collapse; width: 100%; background: #fff; font-size: 13px; }
th, td { border: 1px solid #d9e2ec; padding: 6px 8px; text-align: left; }
th { background: #eef2f7; }
.badge { display: inline-block; padding: 1px 7px; border-radius: 10px; font-size: 11px; background: #e4e7eb; }
.sim { background: #fff3c4; }
ul { margin: 4px 0; padding-left: 18px; }
"""


def _v(value: Any, default: str = "sin dato") -> str:
    if value is None or value == "":
        return default
    return escape(str(value))


def _money(value: Any) -> str:
    if value is None:
        return "sin dato"
    return f"S/ {float(value):,.2f}"


def _severity_class(severity: str) -> str:
    return {"critical": "crit", "warning": "warn"}.get(severity, "")


def render(snap: dict[str, Any]) -> str:
    pipeline = snap["pipeline"]
    modelo = snap["modelo"]
    stats = snap["notificaciones"]
    alertas = snap["ultimas_alertas"]

    ultima = pipeline.get("ultima_carga") or {}
    por_severidad = stats.get("por_severidad", {})
    por_estado = stats.get("por_estado", {})

    filas = []
    for a in alertas:
        sim = ' <span class="badge sim">SIMULADA</span>' if a.get("simulated") else ""
        filas.append(
            "<tr>"
            f"<td>{_v(a.get('alert_id'))}</td>"
            f"<td>{_v(a.get('created_at'))}</td>"
            f"<td>{_v(a.get('rule_code'))}{sim}</td>"
            f"<td class='{_severity_class(str(a.get('severity')))}'>{_v(a.get('severity'))}</td>"
            f"<td>{_v(a.get('indicator'))}</td>"
            f"<td>{_money(a.get('observed_value'))}</td>"
            f"<td>{_v(a.get('threshold'))}</td>"
            f"<td>{_v(a.get('period'))}</td>"
            f"<td>{_v(a.get('status'))}</td>"
            "</tr>"
        )
    tabla = (
        "<table><thead><tr><th>ID</th><th>Fecha/hora</th><th>Regla</th><th>Severidad</th>"
        "<th>Indicador</th><th>Observado</th><th>Umbral</th><th>Periodo</th><th>Estado</th>"
        "</tr></thead><tbody>" + "".join(filas) + "</tbody></table>"
        if filas
        else "<p>Sin alertas registradas. Ejecutar <code>POST /alerts/evaluate</code>.</p>"
    )

    rechazos = pipeline.get("rechazos_por_regla") or []
    rechazos_txt = (
        "<ul>" + "".join(f"<li>{_v(r.get('rule_code'))}: {_v(r.get('total'))}</li>" for r in rechazos) + "</ul>"
        if rechazos
        else "<p class='meta'>Sin rechazos registrados.</p>"
    )

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="30">
<title>Monitoreo - Plataforma de ventas</title>
<style>{CSS}</style>
</head>
<body>
<h1>Monitoreo operativo</h1>
<p class="meta">Generado: {_v(snap.get("generado_en"))} &middot; se actualiza cada 30 s &middot;
<a href="/monitor.json">version JSON</a> &middot; <a href="/alerts">alertas</a></p>

<section class="grid">
  <div class="card">
    <h2>Ultima carga</h2>
    <p class="kpi {'ok' if ultima.get('estado') == 'SUCCESS' else 'crit'}">{_v(ultima.get("estado"))}</p>
    <p>Pipeline: {_v(ultima.get("pipeline"))} (ejecucion {_v(ultima.get("execution_id"))})</p>
    <p>Fin: {_v(ultima.get("fin"))}</p>
    <p>Filas leidas: {_v(ultima.get("filas_leidas"))} &middot; rechazadas: {_v(ultima.get("filas_rechazadas"))}</p>
    <p class="meta">Datos actualizados: {_v(pipeline.get("data_updated_at"))}</p>
  </div>
  <div class="card">
    <h2>Calidad y ejecuciones</h2>
    <p class="kpi {'ok' if not pipeline.get('fallas_24h') else 'crit'}">{_v(pipeline.get("fallas_24h"))} fallas / 24 h</p>
    <p>Ejecuciones 24 h: {_v(pipeline.get("ejecuciones_24h"))}</p>
    <p>Rechazos totales: {_v(pipeline.get("rechazos_total"))} &middot; abiertos: {_v(pipeline.get("rechazos_abiertos"))}</p>
    {rechazos_txt}
  </div>
  <div class="card">
    <h2>Modelo ML</h2>
    <p class="kpi {'ok' if modelo.get('estado') == 'trained' else 'warn'}">{_v(modelo.get("estado"))}</p>
    <p>Version: {_v(modelo.get("version"))}</p>
    <p>MAE modelo: {_v(modelo.get("mae"))} &middot; baseline: {_v(modelo.get("mae_baseline"))}</p>
    <p>Periodos train/test: {_v(modelo.get("periodos_train"))} / {_v(modelo.get("periodos_test"))}</p>
  </div>
  <div class="card">
    <h2>Notificaciones</h2>
    <p class="kpi">{_v(stats.get("total"))} alertas</p>
    <p>Entregadas: {_v(stats.get("entregadas"))} &middot; simuladas: {_v(stats.get("simuladas"))}</p>
    <p>Por severidad: info {_v(por_severidad.get("info", 0))} &middot;
       warning {_v(por_severidad.get("warning", 0))} &middot;
       critical {_v(por_severidad.get("critical", 0))}</p>
    <p>Por estado: abiertas {_v(por_estado.get("open", 0))} &middot;
       reconocidas {_v(por_estado.get("acknowledged", 0))}</p>
  </div>
</section>

<h2>Ultimas alertas</h2>
{tabla}
</body>
</html>"""
