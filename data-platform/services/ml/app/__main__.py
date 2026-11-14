"""CLI del servicio de Machine Learning.

Uso (desde services/ml):
    python -m app train
    python -m app status
    python -m app series
    python -m app predict --periodos 3
"""

from __future__ import annotations

import argparse
import json
import sys

from . import dataset, models


def command_train() -> int:
    puntos = dataset.load_series()
    training = models.train(puntos)
    print(training.message)
    print(f"  estado          : {training.status}")
    print(f"  periodos train  : {training.train_periods}")
    print(f"  periodos test   : {training.test_periods}")
    print(f"  MAE modelo      : {training.metrics.mae}")
    print(f"  RMSE modelo     : {training.metrics.rmse}")
    print(f"  MAE baseline    : {training.baseline.mae}")
    print(f"  RMSE baseline   : {training.baseline.rmse}")

    if training.trained:
        models.save(training)
        experiment_id = dataset.save_experiment(
            version=training.version or "sin-version",
            model_name=models.MODEL_NAME,
            train_periods=training.train_periods,
            test_periods=training.test_periods,
            metrics=training.metrics.as_dict(),
            baseline=training.baseline.as_dict(),
            parameters=str(training.parameters),
            notes=training.message,
        )
        print(f"  version         : {training.version}")
        print(f"  experimento     : {experiment_id}")
        print(f"  artefacto       : guardado")
    return 0 if training.trained else 2


def command_status() -> int:
    model, metadata = models.load()
    if metadata is None:
        training = models.train(dataset.load_series())
        metadata = training.as_dict()
        print("No hay artefacto guardado; diagnostico con los datos actuales.")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    print("")
    print("Modelo cargado:", "si" if model is not None else "no")
    return 0


def command_series() -> int:
    for punto in dataset.load_series():
        print(f"{punto.etiqueta}  {punto.ventas:>12,.2f}")
    return 0


def command_predict(periodos: int) -> int:
    model, metadata = models.load()
    puntos = dataset.load_series()
    if model is None or metadata is None:
        print("No hay modelo entrenado. Ejecutar: python -m app train")
        return 2
    for fila in models.forecast(puntos, model, periodos):
        print(f"{fila['periodo']}  {fila['prediccion']:>12,.2f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ml", description="Modelo de ventas mensuales")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("train", help="Entrena, evalua y guarda el modelo")
    sub.add_parser("status", help="Estado y metricas del modelo")
    sub.add_parser("series", help="Serie mensual observada")
    predict = sub.add_parser("predict", help="Predice los proximos meses")
    predict.add_argument("--periodos", type=int, default=3)

    args = parser.parse_args(argv)
    if args.command == "train":
        return command_train()
    if args.command == "status":
        return command_status()
    if args.command == "series":
        return command_series()
    if args.command == "predict":
        return command_predict(args.periodos)
    return 1


if __name__ == "__main__":
    sys.exit(main())
