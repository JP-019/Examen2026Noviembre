"""Servicio ETL de ventas (T05 / T06).

Modulos:
    config   -> variables de entorno y conexiones
    db       -> helpers sobre pyodbc
    audit    -> ejecuciones, watermarks y linaje
    specs    -> definicion declarativa de tablas
    quality  -> catalogo de reglas y validadores
    staging  -> extraccion, clean y ready
    dw       -> carga de dimensiones y hechos
    report   -> calidad y reconciliacion
"""

__version__ = "1.0.0"
