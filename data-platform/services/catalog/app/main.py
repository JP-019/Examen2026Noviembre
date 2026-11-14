"""Catalogo vivo de la plataforma.

Expone el manifiesto `catalog/platform.json` como JSON y Markdown para que
cualquier integrante (o el evaluador) entienda que hace cada carpeta, que
funciones contiene y que rutas existen.

Ejecucion (desde services/catalog):
    uvicorn app.main:app --port 8001 --reload
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

PLATFORM_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = PLATFORM_ROOT / "catalog" / "platform.json"

app = FastAPI(
    title="Catalogo de la plataforma",
    version="1.0.0",
    description="Indice vivo de microservicios, carpetas, funciones y rutas.",
)


def manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise HTTPException(status_code=500, detail=f"No se encontro {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _table(headers: list[str], rows: list[dict[str, Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(h, "")).replace("|", "\\|") for h in headers) + " |")
    return "\n".join(lines)


def _markdown(data: dict[str, Any]) -> str:
    services = data["services"]
    parts = [
        f"# Indice de la plataforma: {data['name']}",
        "",
        f"- Version: {data['version']}",
        f"- Proceso de negocio: {data['process']}",
        f"- Arquitectura: {data['architecture']}",
        f"- Actualizado: {data['updated']}",
        "",
        "## Servicios",
        "",
        _table(
            ["id", "servicio", "carpeta", "tipo", "estado", "puerto", "tareas"],
            [
                {
                    "id": s["id"],
                    "servicio": s["name"],
                    "carpeta": s["folder"],
                    "tipo": s["type"],
                    "estado": s["status"],
                    "puerto": s.get("port") or "-",
                    "tareas": ", ".join(s.get("tasks", [])),
                }
                for s in services
            ],
        ),
        "",
        "## Carpetas",
        "",
        _table(
            ["carpeta", "proposito", "contiene"],
            [
                {"carpeta": f["path"], "proposito": f["purpose"], "contiene": ", ".join(f["contains"])}
                for f in data["folders"]
            ],
        ),
        "",
        "## Rutas HTTP",
        "",
    ]
    route_rows = [
        {
            "servicio": s["id"],
            "metodo": e["method"],
            "ruta": e["path"],
            "descripcion": e["description"],
            "estado": s["status"],
        }
        for s in services
        for e in s.get("endpoints", [])
    ]
    parts.append(_table(["servicio", "metodo", "ruta", "descripcion", "estado"], route_rows) if route_rows else "Sin rutas declaradas.")
    parts += ["", "## Documentacion", "", _table(["documento", "titulo", "tarea"], data["docs"]), ""]
    parts += ["", "## Tareas y artefactos", "", _table(
        ["tarea", "titulo", "estado", "artefactos"],
        [
            {"tarea": key, "titulo": value["title"], "estado": value["status"], "artefactos": ", ".join(value["artifacts"])}
            for key, value in data["tasks"].items()
        ],
    ), ""]
    return "\n".join(parts)


@app.get("/", summary="Resumen de la plataforma")
def root() -> dict[str, Any]:
    data = manifest()
    return {
        "name": data["name"],
        "version": data["version"],
        "process": data["process"],
        "architecture": data["architecture"],
        "services": len(data["services"]),
        "implemented": sum(1 for s in data["services"] if s["status"] == "implemented"),
        "links": {
            "index": "/index",
            "index_markdown": "/index.md",
            "map": "/map",
            "services": "/services",
            "routes": "/routes",
        },
    }


@app.get("/health", summary="Estado del catalogo")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "catalog", "manifest": str(MANIFEST_PATH.name)}


@app.get("/index", summary="Indice completo en JSON")
def index() -> dict[str, Any]:
    return manifest()


@app.get("/index.md", response_class=PlainTextResponse, summary="Indice completo en Markdown")
def index_markdown() -> str:
    return _markdown(manifest())


@app.get("/map", summary="Mapa de carpetas con su proposito")
def map_folders() -> dict[str, Any]:
    data = manifest()
    return {"folders": data["folders"], "flow": data["flow"]}


@app.get("/services", summary="Lista de microservicios")
def services() -> dict[str, Any]:
    data = manifest()
    return {
        "total": len(data["services"]),
        "services": [
            {
                "id": s["id"],
                "name": s["name"],
                "folder": s["folder"],
                "type": s["type"],
                "status": s["status"],
                "port": s.get("port"),
                "tasks": s.get("tasks", []),
                "endpoints": len(s.get("endpoints", [])),
                "functions": len(s.get("functions", [])),
            }
            for s in data["services"]
        ],
    }


@app.get("/services/{service_id}", summary="Detalle de un servicio")
def service_detail(service_id: str) -> dict[str, Any]:
    for service in manifest()["services"]:
        if service["id"] == service_id:
            return service
    raise HTTPException(status_code=404, detail=f"Servicio no encontrado: {service_id}")


@app.get("/routes", summary="Todas las rutas HTTP de la plataforma")
def routes() -> dict[str, Any]:
    data = manifest()
    flattened = [
        {"service": s["id"], "status": s["status"], **endpoint}
        for s in data["services"]
        for endpoint in s.get("endpoints", [])
    ]
    return {"total": len(flattened), "routes": flattened}
