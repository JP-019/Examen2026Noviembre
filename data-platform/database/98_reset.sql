/*
=====================================================================
 PROYECTO : Plataforma Integral de Ingenieria de Datos y Analitica
 ARCHIVO  : 98_reset.sql
 OBJETIVO : Reiniciar el ambiente local desde cero (solo desarrollo).
 ADVERTENCIA: BORRA la base DataPlatform completa. No usar en demo
              sin volver a ejecutar 00, 01 y 02.
=====================================================================
*/

USE master;
GO

IF DB_ID(N'DataPlatform') IS NOT NULL
BEGIN
    PRINT 'Eliminando base DataPlatform...';
    ALTER DATABASE DataPlatform SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE DataPlatform;
    PRINT 'Base eliminada. Ejecutar 00_schemas.sql, 01_staging.sql y 02_dw.sql.';
END
ELSE
    PRINT 'La base DataPlatform no existe. Nada que eliminar.';
GO
