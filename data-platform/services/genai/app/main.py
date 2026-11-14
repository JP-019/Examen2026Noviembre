"""Asistente GenAI restringido a consultas aprobadas (T12).

No genera SQL ni cifras: interpreta la pregunta con reglas deterministas, ejecuta
una consulta del catalogo contra core-api y devuelve la respuesta con su fuente.

Ejecucion (desde services/genai):
    uvicorn app.main:app --port 8003
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from ipaddress import ip_address
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from . import checks, queries
from .api_client import ApiError, CoreApi
from .intents import interpretar
from .query_catalog import QUERY_CATALOG

logger = logging.getLogger("genai_service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Asistente GenAI - ventas",
    version="1.0.0",
    description=(
        "Asistente en lenguaje natural limitado a un catalogo de consultas aprobadas. "
        "No ejecuta SQL libre, no inventa cifras y toda respuesta declara su fuente."
    ),
)


@app.middleware("http")
async def local_access_only(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    client = request.client
    try:
        is_local = client is not None and ip_address(client.host).is_loopback
    except ValueError:
        is_local = False
    if not is_local:
        return JSONResponse(
            status_code=403,
            content={"detail": "Acceso permitido solo desde localhost."},
        )
    return await call_next(request)


api = CoreApi()


class AskRequest(BaseModel):
    pregunta: str = Field(min_length=3, max_length=500, description="Pregunta en lenguaje natural")


class Fuente(BaseModel):
    servicio: str
    endpoint: str
    data_updated_at: str | None = None


class AskResponse(BaseModel):
    pregunta: str
    intent: str
    respuesta: str
    datos: dict[str, Any]
    fuentes: list[Fuente]
    grounded: bool
    interpretacion: str


class TestResult(BaseModel):
    id: str
    pregunta: str
    intent_esperado: str
    intent_obtenido: str
    grounded: bool
    passed: bool
    detalle: str


class TestsResponse(BaseModel):
    total: int
    passed: int
    failed: int
    results: list[TestResult]


@app.get("/", include_in_schema=False)
def root() -> dict[str, Any]:
    return {
        "service": "genai",
        "docs": "/docs",
        "reglas": "catalogo de consultas aprobadas; sin SQL libre ni cifras inventadas",
        "endpoints": ["/ask", "/queries", "/tests", "/tests/run", "/health"],
        "consultas_aprobadas": len(QUERY_CATALOG),
    }


@app.get("/health", summary="Estado del asistente y de core-api")
def health() -> dict[str, Any]:
    try:
        payload = api.health()
    except ApiError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "status": "ok",
        "service": "genai",
        "core_api": payload.get("status"),
        "data_updated_at": payload.get("data_updated_at"),
        "fact_rows": payload.get("fact_rows"),
    }


@app.get("/queries", summary="Catalogo de consultas aprobadas")
def catalogo() -> dict[str, Any]:
    return {"total": len(QUERY_CATALOG), "queries": QUERY_CATALOG}


@app.post("/ask", response_model=AskResponse, summary="Pregunta en lenguaje natural")
def ask(body: AskRequest) -> AskResponse:
    interpretacion = interpretar(body.pregunta, api)
    respuesta = queries.responder(api, interpretacion)
    logger.info(
        "pregunta=%r intent=%s grounded=%s",
        body.pregunta,
        interpretacion.intent,
        respuesta.grounded,
    )
    return AskResponse(**respuesta.as_dict(body.pregunta, interpretacion))


@app.get("/tests", summary="Las 10 pruebas documentadas")
def tests() -> dict[str, Any]:
    return {
        "total": len(checks.CASES),
        "casos": [
            {
                "id": c.id,
                "pregunta": c.pregunta,
                "intent_esperado": c.intent,
                "grounded_esperado": c.grounded,
            }
            for c in checks.CASES
        ],
    }


@app.post("/tests/run", response_model=TestsResponse, summary="Ejecuta las 10 pruebas")
def tests_run() -> TestsResponse:
    resultados = checks.run(api)
    passed = sum(1 for r in resultados if r["passed"])
    return TestsResponse(
        total=len(resultados),
        passed=passed,
        failed=len(resultados) - passed,
        results=[TestResult(**r) for r in resultados],
    )
