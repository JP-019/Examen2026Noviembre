"""Genera INDEX.md a partir de catalog/platform.json.

Uso (desde la raiz de data-platform):
    python scripts/build_index.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "catalog" / "platform.json"
OUTPUT = ROOT / "INDEX.md"

SERVICE_TYPE_LABELS = {
    "batch": "proceso por lotes",
    "frontend": "interfaz web",
    "http": "HTTP",
}
STATUS_LABELS = {
    "done": "completada",
    "implemented": "implementado",
    "in_progress": "en curso",
    "partial": "parcial",
    "pending": "pendiente",
}


def table(headers: list[str], rows: list[dict[str, Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        cells = [str(row.get(header, "")).replace("|", "\\|") for header in headers]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build() -> str:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    services_rows = [
        {
            "id": s["id"],
            "servicio": s["name"],
            "carpeta": s["folder"],
            "tipo": SERVICE_TYPE_LABELS.get(s["type"], s["type"]),
            "estado": STATUS_LABELS.get(s["status"], s["status"]),
            "puerto": s.get("port") or "-",
            "tareas": ", ".join(s.get("tasks", [])),
        }
        for s in data["services"]
    ]

    folder_rows = [
        {"carpeta": f["path"], "proposito": f["purpose"], "contiene": ", ".join(f["contains"])}
        for f in data["folders"]
    ]

    route_rows = [
        {
            "servicio": s["id"],
            "metodo": endpoint["method"],
            "ruta": endpoint["path"],
            "descripcion": endpoint["description"],
            "estado": STATUS_LABELS.get(s["status"], s["status"]),
        }
        for s in data["services"]
        for endpoint in s.get("endpoints", [])
    ]

    task_rows = [
        {
            "tarea": key,
            "titulo": value["title"],
            "estado": STATUS_LABELS.get(value["status"], value["status"]),
            "artefactos": ", ".join(value["artifacts"]) or "-",
        }
        for key, value in data["tasks"].items()
    ]

    parts = [
        f"# {data['name']}",
        "",
        f"**Proceso de negocio:** {data['process']}  ",
        f"**Arquitectura:** {data['architecture']}  ",
        f"**Versión del índice:** {data['version']}  ",
        f"**Actualizado:** {data['updated']}",
        "",
        "> Este archivo se genera desde `catalog/platform.json`.",
        "> No editarlo a mano: ejecutar `python scripts/build_index.py`.",
        "",
        "## Como navegar este repositorio",
        "",
        "1. Para entender el sistema completo: este indice.",
        "2. Para ver el indice en vivo: `uvicorn app.main:app --port 8001` desde",
        "   `services/catalog` y abrir <http://localhost:8001/index.md>.",
        "3. Para los detalles tecnicos: `documentation/`.",
        "4. Para el codigo: `services/<nombre>/README.md`.",
        "",
        "Flujo de datos:",
        "",
        "```",
        "Venta (SQL Server)",
        "  -> raw -> clean -> ready            (services/etl)",
        "  -> dw (estrella)                    (services/etl)",
        "  -> core-api -> dashboard            (Sprint 2)",
        "  -> ml / genai / alerting            (Sprint 2)",
        "```",
        "",
        "## Servicios",
        "",
        table(["id", "servicio", "carpeta", "tipo", "estado", "puerto", "tareas"], services_rows),
        "",
        "## Carpetas y proposito",
        "",
        table(["carpeta", "proposito", "contiene"], folder_rows),
        "",
        "## Rutas HTTP",
        "",
        table(["servicio", "metodo", "ruta", "descripcion", "estado"], route_rows)
        if route_rows
        else "Sin rutas declaradas.",
        "",
        "## Documentacion",
        "",
        table(
            ["documento", "titulo", "tarea"],
            [{"documento": d["path"], "titulo": d["title"], "tarea": d["task"]} for d in data["docs"]],
        ),
        "",
        "## Trazabilidad de tareas SCRUM",
        "",
        table(["tarea", "titulo", "estado", "artefactos"], task_rows),
        "",
        "## Arranque rapido",
        "",
        "```powershell",
        "# 1. Base de datos (una sola vez)",
        "sqlcmd -S localhost -E -C -i database/00_schemas.sql",
        "sqlcmd -S localhost -E -C -i database/01_staging.sql",
        "sqlcmd -S localhost -E -C -i database/02_dw.sql",
        "",
        "# 2. Pipeline ETL",
        "cd services/etl",
        "python -m pip install -r requirements.txt",
        "python -m app full",
        "",
        "# 3. Indice vivo",
        "cd ../catalog",
        "python -m pip install -r requirements.txt",
        "uvicorn app.main:app --port 8001",
        "```",
        "",
        "Puertos: catalog 8001, core-api 8000, ml 8002, genai 8003, alerting 8004, dashboard 8501.",
        "",
    ]
    return "\n".join(parts)


def main() -> int:
    content = build()
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"Indice generado en: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
