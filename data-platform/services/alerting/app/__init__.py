"""Motor de alertas y monitoreo (T13).

Modulos:
    clients  -> clientes HTTP a core-api y al servicio ML (unico acceso a datos)
    rules    -> reglas puras y contexto medido
    store    -> registro de alertas y entregas en SQLite (anti-duplicado)
    monitor  -> snapshot de pipeline, calidad, modelo y notificaciones
    views    -> render HTML de la vista de monitoreo
"""

__version__ = "1.0.0"
