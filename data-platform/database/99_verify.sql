/*
=====================================================================
 PROYECTO : Plataforma Integral de Ingenieria de Datos y Analitica
 TAREA    : T04 + T07 - Verificacion del bloque fundacional
 ARCHIVO  : 99_verify.sql
 OBJETIVO : Evidencia reproducible de que el staging y el DW existen,
            estan poblados y sin huerfanos.
 USO      : sqlcmd -S localhost -E -C -i database/99_verify.sql
=====================================================================
*/

USE DataPlatform;
GO

PRINT '=== 1. Objetos por esquema ===';
SELECT s.name AS esquema, o.type_desc AS tipo, COUNT(*) AS cantidad
FROM sys.objects o
JOIN sys.schemas s ON s.schema_id = o.schema_id
WHERE s.name IN ('raw','clean','ready','dw','audit','quarantine')
  AND o.type IN ('U','V')
GROUP BY s.name, o.type_desc
ORDER BY s.name, o.type_desc;
GO

PRINT '=== 2. Columnas minimas de auditoria (T04) ===';
SELECT c.name AS columna, t.name AS tipo
FROM sys.columns c
JOIN sys.types t ON t.user_type_id = c.user_type_id
WHERE c.object_id = OBJECT_ID(N'audit.etl_execution')
ORDER BY c.column_id;
GO

PRINT '=== 3. Miembros desconocidos (clave 0) ===';
SELECT 'DimTiempo'   AS dimension, COUNT(*) AS miembros_0 FROM dw.DimTiempo   WHERE TiempoKey   = 0
UNION ALL SELECT 'DimProducto', COUNT(*) FROM dw.DimProducto WHERE ProductoKey = 0
UNION ALL SELECT 'DimLocal',    COUNT(*) FROM dw.DimLocal    WHERE LocalKey    = 0
UNION ALL SELECT 'DimVersion',  COUNT(*) FROM dw.DimVersion  WHERE VersionKey  = 0;
GO

PRINT '=== 4. Cobertura de DimTiempo ===';
SELECT MIN(Fecha) AS desde, MAX(Fecha) AS hasta, COUNT(*) AS dias
FROM dw.DimTiempo
WHERE TiempoKey <> 0;
GO

PRINT '=== 5. Huerfanos en el hecho (debe devolver 0 filas) ===';
SELECT COUNT(*) AS hechos_huerfanos
FROM dw.FactVentas f
LEFT JOIN dw.DimTiempo   t ON t.TiempoKey   = f.TiempoKey
LEFT JOIN dw.DimProducto p ON p.ProductoKey = f.ProductoKey
LEFT JOIN dw.DimLocal    l ON l.LocalKey    = f.LocalKey
LEFT JOIN dw.DimVersion  v ON v.VersionKey  = f.VersionKey
WHERE t.TiempoKey IS NULL OR p.ProductoKey IS NULL
   OR l.LocalKey IS NULL OR v.VersionKey IS NULL;
GO

PRINT '=== 6. Consulta de validacion sobre la vista de consumo ===';
SELECT TOP 10
    NumeroFactura,
    Fecha,
    NombreProducto,
    NombreLocal,
    Cantidad,
    PrecioUnitario,
    ImporteLinea
FROM dw.vw_Ventas
ORDER BY Fecha, NumeroFactura;
GO

PRINT '=== 7. Estado de la ultima ejecucion ETL registrada ===';
SELECT TOP 5 execution_id, pipeline_name, source_object, target_object,
       rows_read, rows_inserted, rows_rejected, status, start_time, end_time
FROM audit.etl_execution
ORDER BY execution_id DESC;
GO
