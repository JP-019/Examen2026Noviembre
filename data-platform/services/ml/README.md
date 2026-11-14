# ml (T11)

## Responsabilidad

Predecir ventas mensuales con un **baseline** obligatorio y un modelo simple,
versionado y evaluado **solo** sobre un bloque de prueba temporal.

## Estado con la fuente actual

La fuente tiene ventas en **un solo mes** (2008-08, 696.40). Con ese volumen el
servicio responde `insufficient_data` y **no publica metricas**: no se inventan
cifras ni se evalua con los mismos datos del entrenamiento. El algoritmo queda
probado con una serie sintetica en `tests/test_ml_model.py`.

## Ejecucion

```powershell
cd services/ml
python -m pip install -r requirements.txt
uvicorn app.main:app --port 8002 --reload
```

| Recurso | URL |
|---|---|
| Swagger | <http://localhost:8002/docs> |
| Modelo | <http://localhost:8002/model> |
| Metricas | <http://localhost:8002/metrics> |
| Serie | <http://localhost:8002/series> |
| Prediccion | `POST /predict` con `{"periodos": 3}` |
| Entrenar | `POST /train` |

CLI:

```powershell
python -m app train
python -m app status
python -m app series
python -m app predict --periodos 3
```

## Indice de funciones

| Archivo | Funcion | Que hace |
|---|---|---|
| `app/config.py` | `DW`, `MIN_TRAIN_PERIODS` | Conexion, rutas de artefactos y minimos de evaluacion |
| `app/dataset.py` | `load_series` | Serie mensual desde `dw.vw_Ventas` |
| `app/dataset.py` | `save_experiment` | Registra la corrida en `audit.ml_experiment` |
| `app/models.py` | `train` | Corte temporal, baseline, ajuste y metricas |
| `app/models.py` | `forecast` | Proyecta los proximos meses |
| `app/models.py` | `save` / `load` | Versiona el modelo en `artifacts/` |
| `app/main.py` | `/model`, `/metrics` | Publica estado y metricas reales o el diagnostico |
| `app/main.py` | `/predict` | Prediccion con advertencia de que es una estimacion |
| `app/main.py` | `/train` | Entrena, guarda y registra el experimento |

## Reglas de modelado

1. **Division temporal**: nunca aleatoria; el bloque de prueba es el final de la serie.
2. **Evaluacion fuera de muestra**: MAE/RMSE/MAPE se calculan solo en prueba.
3. **Baseline obligatorio**: naive estacional con 12+ meses, naive simple si no.
4. **Sin data leakage**: features de tiempo (tendencia + seno/coseno del mes).
5. **Versionado**: `vAAAAMMDD-Np` + metadata JSON junto al artefacto.
6. **Honestidad**: sin periodos suficientes, `insufficient_data` y sin metricas.

## Definicion de terminado

- [x] Baseline comparado con el modelo.
- [x] Metricas en `audit.ml_experiment` (cuando hay entrenamiento).
- [x] Prediccion accesible por endpoint (409 explicado si no hay modelo).
- [x] Limitacion documentada: la fuente no alcanza el minimo de 8 meses.
- [ ] Reentrenar y publicar metricas reales cuando la fuente crezca.
