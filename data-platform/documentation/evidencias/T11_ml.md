# Evidencia T11 - Modelo de Machine Learning

- **Servicio:** `services/ml`
- **Puerto:** 8002
- **Datos:** `dw.vw_Ventas` (serie mensual)
- **Recolectado:** 2026-11-13
- **Reproducible:** `python -m app train`, `python tests/test_ml_model.py`

## 1. Diagnostico con la fuente real

```
> python -m app train
Se necesitan al menos 8 meses con ventas para dividir en entrenamiento y prueba;
hay 1. No se publican metricas.
  estado          : insufficient_data
  periodos train  : 0
  periodos test   : 1
  MAE modelo      : None
  RMSE modelo     : None
  MAE baseline    : None
  RMSE baseline   : None
```

La serie real tiene **un unico mes** (2008-08 = 696.40). El servicio se niega a
publicar metricas: evaluar con los mismos datos del entrenamiento seria un error
metodologico y presentar un MAE sin muestra de prueba seria inventar evidencia.

## 2. Respuestas HTTP

```
GET /model
  status=insufficient_data  version=(ninguna)
  train=0  test=1
  "Se necesitan al menos 8 meses con ventas para dividir en entrenamiento y prueba; hay 1."

GET /metrics
  evaluado_en=test  resultados=2  mae=(null)

GET /series
  1 mes -> {"periodo":"2008-08","ventas":696.4}

POST /predict {"periodos":3}
  HTTP 409 -> "No hay modelo entrenado: ... Ejecutar POST /train cuando haya mas periodos."

POST /train
  status=insufficient_data  saved=false  experimento=(null)
```

Ninguna respuesta devuelve cifras proyectadas cuando no hay respaldo.

## 3. Prueba del algoritmo con serie sintetica (`tests/test_ml_model.py`)

```
Caso 1: serie con 24 meses (entrenamiento posible)
  estado        : trained
  train / test  : 18 / 6
  MAE modelo    : 38.9
  RMSE modelo   : 44.66
  MAE baseline  : 480.0
  predicciones  : 6 meses de prueba
  INFO: el modelo mejora al baseline en la serie sintetica
  proyeccion    : [{'periodo': '2025-01', 'prediccion': 2061.14},
                   {'periodo': '2025-02', 'prediccion': 2086.97},
                   {'periodo': '2025-03', 'prediccion': 2097.19}]

Caso 2: serie con 1 mes (datos insuficientes)
  estado        : insufficient_data
  mensaje       : Se necesitan al menos 8 meses ... hay 1.
  metricas      : {'mae': None, 'rmse': None, 'mape': None}

RESULTADO: OK
```

> Estas metricas son de una serie **sintetica de prueba**, no del negocio. Se
> usan solo para verificar que el pipeline entrena, corta y evalua bien.

## 4. Diseno de la evaluacion

| Decision | Implementacion |
|---|---|
| Division temporal | ultimos `max(2, 25%)` meses como prueba; nunca aleatoria |
| Baseline | naive estacional con 12+ meses; naive simple si no |
| Modelo | `LinearRegression` sobre `t`, `sin(2π·mes/12)`, `cos(2π·mes/12)` |
| Metricas | MAE, RMSE y MAPE **solo** sobre el bloque de prueba |
| Minimos | 6 meses de train + 2 de test; si no, `insufficient_data` |
| Version | `vAAAAMMDD-Np`, guardada en `services/ml/artifacts/` |
| Experimentos | `audit.ml_experiment` (version, corte, metricas, parametros) |

## 5. Tabla de experimentos

```sql
SELECT version, model_name, train_periods, test_periods,
       mae, rmse, baseline_mae, baseline_rmse, trained_at
FROM audit.ml_experiment
ORDER BY experiment_id DESC;
```

Estado actual: **0 filas**, coherente con `insufficient_data`. Se poblara en el
primer entrenamiento con 8+ meses.

## 6. Limitaciones y sesgos documentados

1. **Volumen**: 5 lineas de venta en un solo mes; no hay serie temporal real.
2. **Estacionalidad**: con menos de 12 meses no es estimable.
3. **Alcance**: el modelo predice ventas agregadas por mes, no por producto ni local.
4. **Interpretacion**: toda prediccion se devuelve con la advertencia de que es
   una estimacion, no un dato observado.
5. **Riesgo**: al reentrenar con datos nuevos, comparar siempre contra el baseline
   y revisar que el corte siga siendo temporal.
