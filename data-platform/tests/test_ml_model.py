"""Pruebas del modelo ML con una serie sintetica (T11).

La serie real de la fuente tiene un solo mes, por lo que el servicio informa
`insufficient_data` (correcto). Estas pruebas verifican el algoritmo con datos
controlados y **no** publican esas metricas como resultados del negocio.

Uso:
    python tests/test_ml_model.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "ml"))

from app.dataset import Punto  # noqa: E402
from app.models import forecast, train  # noqa: E402


def serie_sintetica(meses: int = 24) -> list[Punto]:
    puntos = []
    anio, mes = 2023, 1
    for i in range(meses):
        ventas = 1000 + 40 * i + 150 * ((i % 12) in (11, 0, 1))
        puntos.append(Punto(periodo=date(anio, mes, 1), ventas=float(ventas)))
        mes += 1
        if mes > 12:
            mes = 1
            anio += 1
    return puntos


def main() -> int:
    fallos = 0

    print("Caso 1: serie con 24 meses (entrenamiento posible)")
    datos = serie_sintetica(24)
    resultado = train(datos)
    print(f"  estado        : {resultado.status}")
    print(f"  train / test  : {resultado.train_periods} / {resultado.test_periods}")
    print(f"  MAE modelo    : {resultado.metrics.mae}")
    print(f"  RMSE modelo   : {resultado.metrics.rmse}")
    print(f"  MAE baseline  : {resultado.baseline.mae}")
    print(f"  predicciones  : {len(resultado.predictions)} meses de prueba")

    if not resultado.trained:
        fallos += 1
        print("  FALLO: el modelo deberia entrenar con 24 meses")
    if resultado.train_periods + resultado.test_periods != len(datos):
        fallos += 1
        print("  FALLO: el corte temporal no cubre toda la serie")
    if resultado.test_periods < 2:
        fallos += 1
        print("  FALLO: se esperaban al menos 2 meses de prueba")
    if resultado.metrics.mae is None or resultado.baseline.mae is None:
        fallos += 1
        print("  FALLO: faltan metricas del modelo o del baseline")
    if resultado.metrics.mae < resultado.baseline.mae:
        print("  INFO: el modelo mejora al baseline en la serie sintetica")
    else:
        print("  INFO: el baseline empata o mejora al modelo en la serie sintetica (valido)")

    # El corte es temporal: la ultima fecha de train es anterior a la primera de test.
    corte = resultado.train_periods
    if datos[corte - 1].periodo >= datos[corte].periodo:
        fallos += 1
        print("  FALLO: el corte no es temporal")

    proyeccion = forecast(datos, resultado.model, 3)
    print(f"  proyeccion    : {proyeccion}")
    if len(proyeccion) != 3:
        fallos += 1
        print("  FALLO: se esperaban 3 meses proyectados")
    if any(p["prediccion"] < 0 for p in proyeccion):
        fallos += 1
        print("  FALLO: predicciones negativas")

    print("")
    print("Caso 2: serie con 1 mes (datos insuficientes)")
    corta = train([Punto(periodo=date(2008, 8, 1), ventas=696.40)])
    print(f"  estado        : {corta.status}")
    print(f"  mensaje       : {corta.message}")
    print(f"  metricas      : {corta.metrics.as_dict()}")
    if corta.status != "insufficient_data":
        fallos += 1
        print("  FALLO: con 1 mes no se debe entrenar")
    if corta.metrics.mae is not None:
        fallos += 1
        print("  FALLO: no se deben publicar metricas con datos insuficientes")

    print("")
    print("RESULTADO:", "OK" if fallos == 0 else f"{fallos} FALLOS")
    return 0 if fallos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
