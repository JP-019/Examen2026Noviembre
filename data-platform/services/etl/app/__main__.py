"""Punto de entrada del servicio ETL.

Uso (desde services/etl):
    python -m app full
    python -m app incremental
    python -m app status
    python -m app quality-report
    python -m app idempotency-check
    python -m app list-rules
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

import pyodbc

from . import db, dw as dw_load, quality, report, staging
from .config import DW, OVERLAP_DAYS, SOURCE

KEY_TABLES = (
    "clean.Factura",
    "clean.FacturaDetalle",
    "clean.Producto",
    "ready.Ventas",
    "dw.FactVentas",
)

APPEND_ONLY_TABLES = (
    "raw.Factura",
    "raw.FacturaDetalle",
)


def _connect() -> tuple[pyodbc.Connection, pyodbc.Connection]:
    return db.connect(SOURCE), db.connect(DW)


def run_pipeline(mode: str = "full", overlap_days: int = OVERLAP_DAYS) -> dict:
    """Ejecuta el pipeline completo y devuelve un resumen de conteos."""
    source, target = _connect()
    try:
        print(f"[1/4] Extrayendo ({mode}) desde {SOURCE.database} -> {DW.database} ...")
        extracted = staging.extract(source, target, mode=mode, overlap_days=overlap_days)
        print(f"      tablas extraidas: {len(extracted)}")

        print("[2/4] Limpiando y validando (clean) ...")
        clean_summary = staging.clean(target, extracted)
        rejected = sum(item["rejected"] for item in clean_summary.values())

        print("[3/4] Integrando (ready) ...")
        ready = staging.build_ready(target)

        print("[4/4] Cargando Data Warehouse (dimensiones + hechos) ...")
        warehouse = dw_load.load(target)

        orphans = dw_load.orphan_facts(target)

        print("")
        print("Resumen")
        print(f"  filas rechazadas : {rejected}")
        print(f"  ready.Ventas     : insertadas={ready['inserted']} actualizadas={ready['updated']}")
        for name, values in warehouse.items():
            print(f"  dw.{name:<12} : insertadas={values['inserted']} actualizadas={values['updated']}")
        print(f"  huerfanos en hecho: {orphans}")

        return {
            "mode": mode,
            "rejected": rejected,
            "ready": ready,
            "warehouse": warehouse,
            "orphans": orphans,
        }
    finally:
        source.close()
        target.close()


def command_status() -> int:
    conn = db.connect(DW)
    try:
        runs = db.fetch_all(
            conn,
            """
            SELECT TOP 12 execution_id, pipeline_name, source_object, target_object, status,
                   rows_read, rows_inserted, rows_updated, rows_rejected, start_time
            FROM audit.etl_execution
            ORDER BY execution_id DESC
            """,
        )
        counts = db.fetch_all(conn, report.COUNTS_SQL)
    finally:
        conn.close()

    print("Ultimas ejecuciones")
    print(f"{'id':>5}  {'pipeline':<22} {'estado':<8} {'leidas':>7} {'ins':>5} {'upd':>5} {'rech':>5}  destino")
    for row in runs:
        print(
            f"{row['execution_id']:>5}  {row['pipeline_name']:<22} {row['status']:<8} "
            f"{row['rows_read']:>7} {row['rows_inserted']:>5} {row['rows_updated']:>5} "
            f"{row['rows_rejected']:>5}  {row['target_object']}"
        )

    print("")
    print("Volumen por capa")
    for row in counts:
        print(f"  {row['capa']:<18} {row['filas']:>8}")
    return 0


def _snapshot(conn: pyodbc.Connection) -> dict[str, int]:
    snapshot = db.table_counts(conn, KEY_TABLES + APPEND_ONLY_TABLES)
    total = db.fetch_scalar(conn, "SELECT COALESCE(SUM(ImporteLinea), 0) FROM dw.FactVentas") or 0
    snapshot["importe_dw_centavos"] = int(Decimal(total) * 100)
    return snapshot


def command_idempotency() -> int:
    """Ejecuta el pipeline dos veces y compara conteos finales."""
    first_conn = db.connect(DW)
    try:
        before = _snapshot(first_conn)
    finally:
        first_conn.close()

    print("== Primera ejecucion ==")
    run_pipeline("full")
    conn = db.connect(DW)
    try:
        first = _snapshot(conn)
    finally:
        conn.close()

    print("== Segunda ejecucion (mismo lote) ==")
    run_pipeline("full")
    conn = db.connect(DW)
    try:
        second = _snapshot(conn)
    finally:
        conn.close()

    keys = sorted(second)
    print("")
    print(f"{'tabla (capas estables)':<28} {'antes':>10} {'1ra':>10} {'2da':>10} {'estado':>8}")
    ok = True
    for key in keys:
        if key in APPEND_ONLY_TABLES:
            continue
        stable = first[key] == second[key]
        ok = ok and stable
        print(f"{key:<28} {before[key]:>10} {first[key]:>10} {second[key]:>10} {'OK' if stable else 'CAMBIO':>8}")

    print("")
    print("Capas append-only (crecimiento esperado, no afectan idempotencia):")
    for key in APPEND_ONLY_TABLES:
        print(f"  {key:<26} {before.get(key, 0):>8} -> {second.get(key, 0):>8}")

    print("")
    print("RESULTADO:", "IDEMPOTENTE (los conteos de las capas estables no cambian)" if ok else "FALLO (los conteos cambiaron)")
    return 0 if ok else 1


def command_quality_report(output: str | None) -> int:
    conn = db.connect(DW)
    try:
        path = report.build(conn, Path(output) if output else report.DEFAULT_OUTPUT)
    finally:
        conn.close()
    print(f"Reporte generado en: {path}")
    return 0


def command_list_rules() -> int:
    print("Catalogo de reglas de calidad")
    for code, description in quality.RULES.items():
        print(f"  {code}  {description}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="etl",
        description="Pipeline de ventas: fuente -> raw -> clean -> ready -> dw",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    full = subparsers.add_parser("full", help="Carga inicial completa")
    full.add_argument("--overlap-days", type=int, default=OVERLAP_DAYS)

    incremental = subparsers.add_parser("incremental", help="Carga incremental por watermark")
    incremental.add_argument("--overlap-days", type=int, default=OVERLAP_DAYS)

    subparsers.add_parser("status", help="Ultimas ejecuciones y volumen por capa")
    subparsers.add_parser("idempotency-check", help="Prueba de reejecucion sin duplicados")
    subparsers.add_parser("list-rules", help="Catalogo de reglas de calidad")

    quality_report = subparsers.add_parser("quality-report", help="Reporte de calidad y reconciliacion")
    quality_report.add_argument("--out", default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "full":
        run_pipeline("full", args.overlap_days)
        return 0
    if args.command == "incremental":
        run_pipeline("incremental", args.overlap_days)
        return 0
    if args.command == "status":
        return command_status()
    if args.command == "idempotency-check":
        return command_idempotency()
    if args.command == "quality-report":
        return command_quality_report(args.out)
    if args.command == "list-rules":
        return command_list_rules()

    return 1


if __name__ == "__main__":
    sys.exit(main())
