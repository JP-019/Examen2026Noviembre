/*
=====================================================================
 PROYECTO : Plataforma Integral de Ingenieria de Datos y Analitica
 TAREA    : T01 / T04 - Ambiente y separacion de capas
 ARCHIVO  : 00_schemas.sql
 OBJETIVO : Crear la base DataPlatform y los esquemas de cada capa.
 NOTA     : Idempotente. Se puede ejecutar varias veces sin error.
=====================================================================
*/

IF DB_ID(N'DataPlatform') IS NULL
BEGIN
    PRINT 'Creando base DataPlatform...';
    CREATE DATABASE DataPlatform;
END
ELSE
    PRINT 'La base DataPlatform ya existe.';
GO

USE DataPlatform;
GO

IF SCHEMA_ID(N'raw') IS NULL EXEC(N'CREATE SCHEMA raw AUTHORIZATION dbo;');
IF SCHEMA_ID(N'clean') IS NULL EXEC(N'CREATE SCHEMA clean AUTHORIZATION dbo;');
IF SCHEMA_ID(N'ready') IS NULL EXEC(N'CREATE SCHEMA ready AUTHORIZATION dbo;');
IF SCHEMA_ID(N'dw') IS NULL EXEC(N'CREATE SCHEMA dw AUTHORIZATION dbo;');
IF SCHEMA_ID(N'audit') IS NULL EXEC(N'CREATE SCHEMA audit AUTHORIZATION dbo;');
IF SCHEMA_ID(N'quarantine') IS NULL EXEC(N'CREATE SCHEMA quarantine AUTHORIZATION dbo;');
GO

PRINT 'Esquemas disponibles:';
SELECT name AS esquema
FROM sys.schemas
WHERE name IN ('raw','clean','ready','dw','audit','quarantine')
ORDER BY name;
GO
