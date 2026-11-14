/*
=====================================================================
 PROYECTO : Plataforma Integral de Ingenieria de Datos y Analitica
 TAREA    : T07 - Modelo dimensional (hechos, dimensiones, SCD)
 ARCHIVO  : 02_dw.sql
 OBJETIVO : Esquema estrella de VENTAS con claves sustitutas,
            miembro desconocido y DimTiempo poblada.
 GRANO    : una fila de dw.FactVentas = una linea de factura.
 REQUISITO: Ejecutar antes 00_schemas.sql y 01_staging.sql
 NOTA     : Idempotente. No borra hechos ya cargados.
=====================================================================
*/

USE DataPlatform;
GO
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET DATEFIRST 7;   -- 1 = domingo ... 7 = sabado (necesario para NombreDia)
GO

/*====================================================================
  DIMENSIONES
====================================================================*/

IF OBJECT_ID(N'dw.DimTiempo', N'U') IS NULL
CREATE TABLE dw.DimTiempo
(
    TiempoKey       int          NOT NULL,   -- AAAAMMDD
    Fecha           date         NOT NULL,
    Anio            smallint     NOT NULL,
    Trimestre       tinyint      NOT NULL,
    Mes             tinyint      NOT NULL,
    NombreMes       varchar(20)  NOT NULL,
    SemanaISO       tinyint      NOT NULL,
    Dia             tinyint      NOT NULL,
    NombreDia       varchar(20)  NOT NULL,
    DiaAnio         smallint     NOT NULL,
    AnioMes         int          NOT NULL,   -- AAAAMM para agrupaciones
    EsFinDeSemana   bit          NOT NULL,
    CONSTRAINT PK_dw_DimTiempo PRIMARY KEY CLUSTERED (TiempoKey),
    CONSTRAINT UQ_dw_DimTiempo_Fecha UNIQUE (Fecha)
);
GO

IF OBJECT_ID(N'dw.DimProducto', N'U') IS NULL
CREATE TABLE dw.DimProducto
(
    ProductoKey         int           IDENTITY(1,1) NOT NULL,
    ProductoNaturalKey  int           NOT NULL,
    NombreProducto      varchar(100)  NOT NULL,
    SubFamilia          varchar(100)  NULL,
    Familia             varchar(100)  NULL,
    Categoria           varchar(100)  NULL,
    Rubro               varchar(100)  NULL,
    Seccion             varchar(100)  NULL,
    JerarquiaCompleta   varchar(500)  NULL,
    EsVigente           bit           NOT NULL CONSTRAINT DF_dw_DimProducto_vigente DEFAULT 1,
    FilaDesde           datetime2(3)  NOT NULL CONSTRAINT DF_dw_DimProducto_desde   DEFAULT SYSUTCDATETIME(),
    FilaHasta           datetime2(3)  NULL,
    EsDesconocido       bit           NOT NULL CONSTRAINT DF_dw_DimProducto_desc    DEFAULT 0,
    CONSTRAINT PK_dw_DimProducto PRIMARY KEY CLUSTERED (ProductoKey),
    CONSTRAINT UQ_dw_DimProducto_Natural UNIQUE (ProductoNaturalKey)
);
GO

IF OBJECT_ID(N'dw.DimLocal', N'U') IS NULL
CREATE TABLE dw.DimLocal
(
    LocalKey        int           IDENTITY(1,1) NOT NULL,
    LocalNaturalKey int           NOT NULL,
    NombreLocal     varchar(100)  NULL,
    EsDesconocido   bit           NOT NULL CONSTRAINT DF_dw_DimLocal_desc DEFAULT 0,
    CONSTRAINT PK_dw_DimLocal PRIMARY KEY CLUSTERED (LocalKey),
    CONSTRAINT UQ_dw_DimLocal_Natural UNIQUE (LocalNaturalKey)
);
GO

IF OBJECT_ID(N'dw.DimVersion', N'U') IS NULL
CREATE TABLE dw.DimVersion
(
    VersionKey        int           IDENTITY(1,1) NOT NULL,
    VersionNaturalKey int           NOT NULL,
    NombreVersion     varchar(100)  NULL,
    EsDesconocido     bit           NOT NULL CONSTRAINT DF_dw_DimVersion_desc DEFAULT 0,
    CONSTRAINT PK_dw_DimVersion PRIMARY KEY CLUSTERED (VersionKey),
    CONSTRAINT UQ_dw_DimVersion_Natural UNIQUE (VersionNaturalKey)
);
GO

/*====================================================================
  TABLA DE HECHOS
====================================================================*/

IF OBJECT_ID(N'dw.FactVentas', N'U') IS NULL
CREATE TABLE dw.FactVentas
(
    VentaKey        bigint        IDENTITY(1,1) NOT NULL,
    TiempoKey       int           NOT NULL,
    ProductoKey     int           NOT NULL,
    LocalKey        int           NOT NULL,
    VersionKey      int           NOT NULL,
    IdFacturaDetalle int          NOT NULL,   -- clave natural de la linea (idempotencia)
    NumeroFactura   int           NOT NULL,   -- dimension degenerada
    Cantidad        int           NOT NULL,
    PrecioUnitario  decimal(18,2) NOT NULL,
    Descuento       decimal(18,2) NOT NULL CONSTRAINT DF_dw_FactVentas_desc DEFAULT 0,
    ImporteLinea    decimal(18,2) NOT NULL,
    FechaCarga      datetime2(3)  NOT NULL CONSTRAINT DF_dw_FactVentas_carga DEFAULT SYSUTCDATETIME(),
    ExecutionId     bigint        NOT NULL CONSTRAINT DF_dw_FactVentas_exec  DEFAULT 0,
    CONSTRAINT PK_dw_FactVentas PRIMARY KEY CLUSTERED (VentaKey),
    CONSTRAINT FK_dw_FactVentas_Tiempo   FOREIGN KEY (TiempoKey)   REFERENCES dw.DimTiempo   (TiempoKey),
    CONSTRAINT FK_dw_FactVentas_Producto FOREIGN KEY (ProductoKey) REFERENCES dw.DimProducto (ProductoKey),
    CONSTRAINT FK_dw_FactVentas_Local    FOREIGN KEY (LocalKey)    REFERENCES dw.DimLocal    (LocalKey),
    CONSTRAINT FK_dw_FactVentas_Version  FOREIGN KEY (VersionKey)  REFERENCES dw.DimVersion  (VersionKey),
    CONSTRAINT CK_dw_FactVentas_cantidad CHECK (Cantidad > 0),
    CONSTRAINT CK_dw_FactVentas_precio   CHECK (PrecioUnitario >= 0),
    CONSTRAINT CK_dw_FactVentas_descuento CHECK (Descuento >= 0),
    CONSTRAINT CK_dw_FactVentas_importe  CHECK (ImporteLinea = Cantidad * PrecioUnitario - Descuento)
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_dw_FactVentas_Tiempo' AND object_id = OBJECT_ID(N'dw.FactVentas'))
    CREATE INDEX IX_dw_FactVentas_Tiempo ON dw.FactVentas (TiempoKey) INCLUDE (Cantidad, ImporteLinea);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_dw_FactVentas_Producto' AND object_id = OBJECT_ID(N'dw.FactVentas'))
    CREATE INDEX IX_dw_FactVentas_Producto ON dw.FactVentas (ProductoKey) INCLUDE (Cantidad, ImporteLinea);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_dw_FactVentas_Local' AND object_id = OBJECT_ID(N'dw.FactVentas'))
    CREATE INDEX IX_dw_FactVentas_Local ON dw.FactVentas (LocalKey) INCLUDE (Cantidad, ImporteLinea);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_dw_FactVentas_Factura' AND object_id = OBJECT_ID(N'dw.FactVentas'))
    CREATE INDEX IX_dw_FactVentas_Factura ON dw.FactVentas (NumeroFactura);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_dw_FactVentas_Linea' AND object_id = OBJECT_ID(N'dw.FactVentas'))
    CREATE UNIQUE INDEX UQ_dw_FactVentas_Linea ON dw.FactVentas (IdFacturaDetalle);
GO

/*====================================================================
  MIEMBRO DESCONOCIDO (clave 0)
  Politica: un hecho sin correspondencia se carga con clave 0 y se
  registra en cuarentena para revision. Nunca se descarta en silencio.
====================================================================*/

IF NOT EXISTS (SELECT 1 FROM dw.DimTiempo WHERE TiempoKey = 0)
INSERT INTO dw.DimTiempo
    (TiempoKey, Fecha, Anio, Trimestre, Mes, NombreMes, SemanaISO, Dia, NombreDia, DiaAnio, AnioMes, EsFinDeSemana)
VALUES
    (0, '1900-01-01', 1900, 1, 1, 'Desconocido', 1, 1, 'Desconocido', 1, 190001, 0);
GO

IF NOT EXISTS (SELECT 1 FROM dw.DimProducto WHERE ProductoKey = 0)
BEGIN
    SET IDENTITY_INSERT dw.DimProducto ON;
    INSERT INTO dw.DimProducto
        (ProductoKey, ProductoNaturalKey, NombreProducto, SubFamilia, Familia, Categoria, Rubro, Seccion, JerarquiaCompleta, EsVigente, EsDesconocido)
    VALUES
        (0, 0, 'Producto desconocido', 'Desconocido', 'Desconocido', 'Desconocido', 'Desconocido', 'Desconocido', 'Desconocido', 1, 1);
    SET IDENTITY_INSERT dw.DimProducto OFF;
END
GO

IF NOT EXISTS (SELECT 1 FROM dw.DimLocal WHERE LocalKey = 0)
BEGIN
    SET IDENTITY_INSERT dw.DimLocal ON;
    INSERT INTO dw.DimLocal (LocalKey, LocalNaturalKey, NombreLocal, EsDesconocido)
    VALUES (0, 0, 'Local desconocido', 1);
    SET IDENTITY_INSERT dw.DimLocal OFF;
END
GO

IF NOT EXISTS (SELECT 1 FROM dw.DimVersion WHERE VersionKey = 0)
BEGIN
    SET IDENTITY_INSERT dw.DimVersion ON;
    INSERT INTO dw.DimVersion (VersionKey, VersionNaturalKey, NombreVersion, EsDesconocido)
    VALUES (0, 0, 'Version desconocida', 1);
    SET IDENTITY_INSERT dw.DimVersion OFF;
END
GO

/*====================================================================
  POBLADO DE DimTiempo (2000-01-01 a 2035-12-31)
====================================================================*/

;WITH Fechas AS
(
    SELECT CAST('2000-01-01' AS date) AS Fecha
    UNION ALL
    SELECT DATEADD(day, 1, Fecha)
    FROM Fechas
    WHERE Fecha < '2035-12-31'
)
INSERT INTO dw.DimTiempo
    (TiempoKey, Fecha, Anio, Trimestre, Mes, NombreMes, SemanaISO, Dia, NombreDia, DiaAnio, AnioMes, EsFinDeSemana)
SELECT
    YEAR(Fecha) * 10000 + MONTH(Fecha) * 100 + DAY(Fecha),
    Fecha,
    YEAR(Fecha),
    DATEPART(quarter, Fecha),
    MONTH(Fecha),
    CASE MONTH(Fecha)
        WHEN 1 THEN 'Enero'      WHEN 2 THEN 'Febrero'
        WHEN 3 THEN 'Marzo'      WHEN 4 THEN 'Abril'
        WHEN 5 THEN 'Mayo'       WHEN 6 THEN 'Junio'
        WHEN 7 THEN 'Julio'      WHEN 8 THEN 'Agosto'
        WHEN 9 THEN 'Septiembre' WHEN 10 THEN 'Octubre'
        WHEN 11 THEN 'Noviembre' WHEN 12 THEN 'Diciembre'
    END,
    DATEPART(iso_week, Fecha),
    DAY(Fecha),
    CASE DATEPART(weekday, Fecha)
        WHEN 1 THEN 'Domingo'  WHEN 2 THEN 'Lunes'
        WHEN 3 THEN 'Martes'   WHEN 4 THEN 'Miercoles'
        WHEN 5 THEN 'Jueves'   WHEN 6 THEN 'Viernes'
        WHEN 7 THEN 'Sabado'
    END,
    DATEPART(dayofyear, Fecha),
    YEAR(Fecha) * 100 + MONTH(Fecha),
    CASE WHEN DATEPART(weekday, Fecha) IN (1, 7) THEN 1 ELSE 0 END
FROM Fechas
WHERE NOT EXISTS (SELECT 1 FROM dw.DimTiempo t WHERE t.Fecha = Fechas.Fecha)
OPTION (MAXRECURSION 0);
GO

/*====================================================================
  VISTA DE CONSUMO (BI / API)
  El frontend y la API leen de vistas, nunca de SQL libre.
====================================================================*/

CREATE OR ALTER VIEW dw.vw_Ventas
AS
SELECT
    f.VentaKey,
    f.NumeroFactura,
    t.Fecha,
    t.Anio,
    t.Trimestre,
    t.Mes,
    t.NombreMes,
    t.AnioMes,
    t.NombreDia,
    t.EsFinDeSemana,
    p.ProductoKey,
    p.NombreProducto,
    p.Seccion,
    p.Rubro,
    p.Categoria,
    p.Familia,
    p.SubFamilia,
    l.LocalKey,
    l.NombreLocal,
    v.VersionKey,
    v.NombreVersion,
    f.Cantidad,
    f.PrecioUnitario,
    f.Descuento,
    f.ImporteLinea
FROM dw.FactVentas f
JOIN dw.DimTiempo   t ON t.TiempoKey   = f.TiempoKey
JOIN dw.DimProducto p ON p.ProductoKey = f.ProductoKey
JOIN dw.DimLocal    l ON l.LocalKey    = f.LocalKey
JOIN dw.DimVersion  v ON v.VersionKey  = f.VersionKey;
GO

PRINT 'Modelo dimensional creado correctamente.';
GO

SELECT 'DimTiempo' AS tabla, COUNT(*) AS filas FROM dw.DimTiempo
UNION ALL SELECT 'DimProducto', COUNT(*) FROM dw.DimProducto
UNION ALL SELECT 'DimLocal',    COUNT(*) FROM dw.DimLocal
UNION ALL SELECT 'DimVersion',  COUNT(*) FROM dw.DimVersion
UNION ALL SELECT 'FactVentas',  COUNT(*) FROM dw.FactVentas;
GO
