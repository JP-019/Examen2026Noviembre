/*
=====================================================================
 PROYECTO : Plataforma Integral de Ingenieria de Datos y Analitica
 TAREA    : T04 - Staging 3 zonas + auditoria + cuarentena
 ARCHIVO  : 01_staging.sql
 OBJETIVO : Zonas raw (copia fiel), clean (tipado/validado) y
            ready (integrado), mas auditoria, watermark, linaje y
            cuarentena.
 REQUISITO: Ejecutar antes 00_schemas.sql
 NOTA     : Idempotente (CREATE IF MISSING). No borra datos.
=====================================================================
*/

USE DataPlatform;
GO

/* Requerido para columnas calculadas persistidas e indices */
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

/*====================================================================
  ZONA 1: RAW  (LANDING)
  Copia fiel de la fuente. Solo INSERT. Sin PK de negocio, sin
  transformaciones. Se agrega un id tecnico y metadatos de carga.
====================================================================*/

IF OBJECT_ID(N'raw.Factura', N'U') IS NULL
CREATE TABLE raw.Factura
(
    RawFacturaId    bigint IDENTITY(1,1) NOT NULL,
    IdFactura       int            NOT NULL,
    VentaAsociada   decimal(8,2)   NOT NULL,
    Fecha           datetime       NOT NULL,
    NumeroFactura   int            NOT NULL,   -- origen: [n°Factura]
    IdLocal         int            NULL,
    IdVersion       int            NULL,
    _execution_id   bigint         NOT NULL,
    _extracted_at   datetime2(3)   NOT NULL CONSTRAINT DF_raw_Factura_extracted DEFAULT SYSUTCDATETIME(),
    _source_object  varchar(200)   NOT NULL CONSTRAINT DF_raw_Factura_source    DEFAULT 'Venta.dbo.Factura',
    CONSTRAINT PK_raw_Factura PRIMARY KEY CLUSTERED (RawFacturaId)
);
GO

IF OBJECT_ID(N'raw.FacturaDetalle', N'U') IS NULL
CREATE TABLE raw.FacturaDetalle
(
    RawFacturaDetalleId bigint IDENTITY(1,1) NOT NULL,
    IdFacturaDetalle    int            NOT NULL,   -- origen: Id_Factura_Detalle
    IdProducto          int            NOT NULL,
    IdFactura           int            NOT NULL,
    PrecioSinImporte    decimal(8,2)   NOT NULL,
    Cantidad            int            NOT NULL,
    _execution_id       bigint         NOT NULL,
    _extracted_at       datetime2(3)   NOT NULL CONSTRAINT DF_raw_FacturaDetalle_extracted DEFAULT SYSUTCDATETIME(),
    _source_object      varchar(200)   NOT NULL CONSTRAINT DF_raw_FacturaDetalle_source    DEFAULT 'Venta.dbo.Factura_Detalle',
    CONSTRAINT PK_raw_FacturaDetalle PRIMARY KEY CLUSTERED (RawFacturaDetalleId)
);
GO

IF OBJECT_ID(N'raw.Producto', N'U') IS NULL
CREATE TABLE raw.Producto
(
    RawProductoId   bigint IDENTITY(1,1) NOT NULL,
    IdProducto      int          NOT NULL,
    NombreProducto  varchar(30)  NOT NULL,
    IdSubFamilia    int          NOT NULL,
    _execution_id   bigint       NOT NULL,
    _extracted_at   datetime2(3) NOT NULL CONSTRAINT DF_raw_Producto_extracted DEFAULT SYSUTCDATETIME(),
    _source_object  varchar(200) NOT NULL CONSTRAINT DF_raw_Producto_source    DEFAULT 'Venta.dbo.Producto',
    CONSTRAINT PK_raw_Producto PRIMARY KEY CLUSTERED (RawProductoId)
);
GO

IF OBJECT_ID(N'raw.SubFamilia', N'U') IS NULL
CREATE TABLE raw.SubFamilia
(
    RawSubFamiliaId bigint IDENTITY(1,1) NOT NULL,
    IdSubFamilia    int          NOT NULL,
    NombreSubFamilia varchar(30) NOT NULL,
    IdFamilia       int          NOT NULL,
    _execution_id   bigint       NOT NULL,
    _extracted_at   datetime2(3) NOT NULL CONSTRAINT DF_raw_SubFamilia_extracted DEFAULT SYSUTCDATETIME(),
    _source_object  varchar(200) NOT NULL CONSTRAINT DF_raw_SubFamilia_source    DEFAULT 'Venta.dbo.SubFamilia',
    CONSTRAINT PK_raw_SubFamilia PRIMARY KEY CLUSTERED (RawSubFamiliaId)
);
GO

IF OBJECT_ID(N'raw.Familia', N'U') IS NULL
CREATE TABLE raw.Familia
(
    RawFamiliaId    bigint IDENTITY(1,1) NOT NULL,
    IdFamilia       int          NOT NULL,
    NombreFamilia   varchar(30)  NOT NULL,
    IdCategoria     int          NOT NULL,
    _execution_id   bigint       NOT NULL,
    _extracted_at   datetime2(3) NOT NULL CONSTRAINT DF_raw_Familia_extracted DEFAULT SYSUTCDATETIME(),
    _source_object  varchar(200) NOT NULL CONSTRAINT DF_raw_Familia_source    DEFAULT 'Venta.dbo.Familia',
    CONSTRAINT PK_raw_Familia PRIMARY KEY CLUSTERED (RawFamiliaId)
);
GO

IF OBJECT_ID(N'raw.Categoria', N'U') IS NULL
CREATE TABLE raw.Categoria
(
    RawCategoriaId  bigint IDENTITY(1,1) NOT NULL,
    IdCategoria     int          NOT NULL,
    NombreCategoria varchar(30)  NOT NULL,
    IdRubro         int          NOT NULL,
    _execution_id   bigint       NOT NULL,
    _extracted_at   datetime2(3) NOT NULL CONSTRAINT DF_raw_Categoria_extracted DEFAULT SYSUTCDATETIME(),
    _source_object  varchar(200) NOT NULL CONSTRAINT DF_raw_Categoria_source    DEFAULT 'Venta.dbo.Categoria',
    CONSTRAINT PK_raw_Categoria PRIMARY KEY CLUSTERED (RawCategoriaId)
);
GO

IF OBJECT_ID(N'raw.Rubro', N'U') IS NULL
CREATE TABLE raw.Rubro
(
    RawRubroId      bigint IDENTITY(1,1) NOT NULL,
    IdRubro         int          NOT NULL,
    NombreRubro     varchar(30)  NOT NULL,
    IdSeccion       int          NOT NULL,
    _execution_id   bigint       NOT NULL,
    _extracted_at   datetime2(3) NOT NULL CONSTRAINT DF_raw_Rubro_extracted DEFAULT SYSUTCDATETIME(),
    _source_object  varchar(200) NOT NULL CONSTRAINT DF_raw_Rubro_source    DEFAULT 'Venta.dbo.Rubro',
    CONSTRAINT PK_raw_Rubro PRIMARY KEY CLUSTERED (RawRubroId)
);
GO

IF OBJECT_ID(N'raw.Seccion', N'U') IS NULL
CREATE TABLE raw.Seccion
(
    RawSeccionId    bigint IDENTITY(1,1) NOT NULL,
    IdSeccion       int          NOT NULL,
    NombreSeccion   varchar(30)  NOT NULL,
    _execution_id   bigint       NOT NULL,
    _extracted_at   datetime2(3) NOT NULL CONSTRAINT DF_raw_Seccion_extracted DEFAULT SYSUTCDATETIME(),
    _source_object  varchar(200) NOT NULL CONSTRAINT DF_raw_Seccion_source    DEFAULT 'Venta.dbo.Seccion',
    CONSTRAINT PK_raw_Seccion PRIMARY KEY CLUSTERED (RawSeccionId)
);
GO

IF OBJECT_ID(N'raw.Local', N'U') IS NULL
CREATE TABLE raw.Local
(
    RawLocalId      bigint IDENTITY(1,1) NOT NULL,
    IdLocal         int          NOT NULL,
    Nombre          varchar(50)  NULL,
    _execution_id   bigint       NOT NULL,
    _extracted_at   datetime2(3) NOT NULL CONSTRAINT DF_raw_Local_extracted DEFAULT SYSUTCDATETIME(),
    _source_object  varchar(200) NOT NULL CONSTRAINT DF_raw_Local_source    DEFAULT 'Venta.dbo.Local',
    CONSTRAINT PK_raw_Local PRIMARY KEY CLUSTERED (RawLocalId)
);
GO

IF OBJECT_ID(N'raw.Version', N'U') IS NULL
CREATE TABLE raw.Version
(
    RawVersionId    bigint IDENTITY(1,1) NOT NULL,
    IdVersion       int          NOT NULL,
    Nombre          varchar(50)  NULL,
    _execution_id   bigint       NOT NULL,
    _extracted_at   datetime2(3) NOT NULL CONSTRAINT DF_raw_Version_extracted DEFAULT SYSUTCDATETIME(),
    _source_object  varchar(200) NOT NULL CONSTRAINT DF_raw_Version_source    DEFAULT 'Venta.dbo.Version',
    CONSTRAINT PK_raw_Version PRIMARY KEY CLUSTERED (RawVersionId)
);
GO

/* Indices de trazabilidad en raw */
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_raw_Factura_bk' AND object_id = OBJECT_ID(N'raw.Factura'))
    CREATE INDEX IX_raw_Factura_bk ON raw.Factura (IdFactura, _execution_id);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_raw_FacturaDetalle_bk' AND object_id = OBJECT_ID(N'raw.FacturaDetalle'))
    CREATE INDEX IX_raw_FacturaDetalle_bk ON raw.FacturaDetalle (IdFacturaDetalle, _execution_id);
GO

/*====================================================================
  ZONA 2: CLEAN  (VALIDATED)
  Tipado explicito, estandarizacion y claves de negocio.
====================================================================*/

IF OBJECT_ID(N'clean.Factura', N'U') IS NULL
CREATE TABLE clean.Factura
(
    IdFactura       int          NOT NULL,
    VentaAsociada   decimal(18,2) NOT NULL,
    Fecha           date         NOT NULL,
    NumeroFactura   int          NOT NULL,
    IdLocal         int          NULL,
    IdVersion       int          NULL,
    _execution_id   bigint       NOT NULL,
    _loaded_at      datetime2(3) NOT NULL CONSTRAINT DF_clean_Factura_loaded DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_clean_Factura PRIMARY KEY CLUSTERED (IdFactura)
);
GO

IF OBJECT_ID(N'clean.FacturaDetalle', N'U') IS NULL
CREATE TABLE clean.FacturaDetalle
(
    IdFacturaDetalle int           NOT NULL,
    IdProducto       int           NOT NULL,
    IdFactura        int           NOT NULL,
    PrecioUnitario   decimal(18,2) NOT NULL,
    Cantidad         int           NOT NULL,
    ImporteLinea     AS (CAST(Cantidad * PrecioUnitario AS decimal(18,2))) PERSISTED,
    _execution_id    bigint        NOT NULL,
    _loaded_at       datetime2(3)  NOT NULL CONSTRAINT DF_clean_FacturaDetalle_loaded DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_clean_FacturaDetalle PRIMARY KEY CLUSTERED (IdFacturaDetalle),
    CONSTRAINT CK_clean_FacturaDetalle_cantidad CHECK (Cantidad > 0),
    CONSTRAINT CK_clean_FacturaDetalle_precio   CHECK (PrecioUnitario >= 0)
);
GO

IF OBJECT_ID(N'clean.Producto', N'U') IS NULL
CREATE TABLE clean.Producto
(
    IdProducto      int          NOT NULL,
    NombreProducto  varchar(100) NOT NULL,
    IdSubFamilia    int          NOT NULL,
    _execution_id   bigint       NOT NULL,
    _loaded_at      datetime2(3) NOT NULL CONSTRAINT DF_clean_Producto_loaded DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_clean_Producto PRIMARY KEY CLUSTERED (IdProducto)
);
GO

IF OBJECT_ID(N'clean.SubFamilia', N'U') IS NULL
CREATE TABLE clean.SubFamilia
(
    IdSubFamilia     int          NOT NULL,
    NombreSubFamilia varchar(100) NOT NULL,
    IdFamilia        int          NOT NULL,
    _execution_id    bigint       NOT NULL,
    _loaded_at       datetime2(3) NOT NULL CONSTRAINT DF_clean_SubFamilia_loaded DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_clean_SubFamilia PRIMARY KEY CLUSTERED (IdSubFamilia)
);
GO

IF OBJECT_ID(N'clean.Familia', N'U') IS NULL
CREATE TABLE clean.Familia
(
    IdFamilia       int          NOT NULL,
    NombreFamilia   varchar(100) NOT NULL,
    IdCategoria     int          NOT NULL,
    _execution_id   bigint       NOT NULL,
    _loaded_at      datetime2(3) NOT NULL CONSTRAINT DF_clean_Familia_loaded DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_clean_Familia PRIMARY KEY CLUSTERED (IdFamilia)
);
GO

IF OBJECT_ID(N'clean.Categoria', N'U') IS NULL
CREATE TABLE clean.Categoria
(
    IdCategoria      int          NOT NULL,
    NombreCategoria  varchar(100) NOT NULL,
    IdRubro          int          NOT NULL,
    _execution_id    bigint       NOT NULL,
    _loaded_at       datetime2(3) NOT NULL CONSTRAINT DF_clean_Categoria_loaded DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_clean_Categoria PRIMARY KEY CLUSTERED (IdCategoria)
);
GO

IF OBJECT_ID(N'clean.Rubro', N'U') IS NULL
CREATE TABLE clean.Rubro
(
    IdRubro         int          NOT NULL,
    NombreRubro     varchar(100) NOT NULL,
    IdSeccion       int          NOT NULL,
    _execution_id   bigint       NOT NULL,
    _loaded_at      datetime2(3) NOT NULL CONSTRAINT DF_clean_Rubro_loaded DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_clean_Rubro PRIMARY KEY CLUSTERED (IdRubro)
);
GO

IF OBJECT_ID(N'clean.Seccion', N'U') IS NULL
CREATE TABLE clean.Seccion
(
    IdSeccion       int          NOT NULL,
    NombreSeccion   varchar(100) NOT NULL,
    _execution_id   bigint       NOT NULL,
    _loaded_at      datetime2(3) NOT NULL CONSTRAINT DF_clean_Seccion_loaded DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_clean_Seccion PRIMARY KEY CLUSTERED (IdSeccion)
);
GO

IF OBJECT_ID(N'clean.Local', N'U') IS NULL
CREATE TABLE clean.Local
(
    IdLocal         int          NOT NULL,
    NombreLocal     varchar(100) NULL,
    _execution_id   bigint       NOT NULL,
    _loaded_at      datetime2(3) NOT NULL CONSTRAINT DF_clean_Local_loaded DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_clean_Local PRIMARY KEY CLUSTERED (IdLocal)
);
GO

IF OBJECT_ID(N'clean.Version', N'U') IS NULL
CREATE TABLE clean.Version
(
    IdVersion       int          NOT NULL,
    NombreVersion   varchar(100) NULL,
    _execution_id   bigint       NOT NULL,
    _loaded_at      datetime2(3) NOT NULL CONSTRAINT DF_clean_Version_loaded DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_clean_Version PRIMARY KEY CLUSTERED (IdVersion)
);
GO

/*====================================================================
  ZONA 3: READY  (INTEGRATION)
  Una fila por linea de factura, con jerarquia resuelta. Es la
  unica entrada del DW.
====================================================================*/

IF OBJECT_ID(N'ready.Ventas', N'U') IS NULL
CREATE TABLE ready.Ventas
(
    IdFacturaDetalle int           NOT NULL,
    IdFactura        int           NOT NULL,
    NumeroFactura    int           NOT NULL,
    Fecha            date          NOT NULL,
    IdProducto       int           NOT NULL,
    NombreProducto   varchar(100)  NOT NULL,
    IdSubFamilia     int           NOT NULL,
    NombreSubFamilia varchar(100)  NULL,
    IdFamilia        int           NOT NULL,
    NombreFamilia    varchar(100)  NULL,
    IdCategoria      int           NOT NULL,
    NombreCategoria  varchar(100)  NULL,
    IdRubro          int           NOT NULL,
    NombreRubro      varchar(100)  NULL,
    IdSeccion        int           NOT NULL,
    NombreSeccion    varchar(100)  NULL,
    IdLocal          int           NULL,
    NombreLocal      varchar(100)  NULL,
    IdVersion        int           NULL,
    NombreVersion    varchar(100)  NULL,
    Cantidad         int           NOT NULL,
    PrecioUnitario   decimal(18,2) NOT NULL,
    ImporteLinea     decimal(18,2) NOT NULL,
    _execution_id    bigint        NOT NULL,
    _loaded_at       datetime2(3)  NOT NULL CONSTRAINT DF_ready_Ventas_loaded DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_ready_Ventas PRIMARY KEY CLUSTERED (IdFacturaDetalle),
    CONSTRAINT CK_ready_Ventas_cantidad CHECK (Cantidad > 0),
    CONSTRAINT CK_ready_Ventas_importe  CHECK (ImporteLinea >= 0)
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_ready_Ventas_fecha' AND object_id = OBJECT_ID(N'ready.Ventas'))
    CREATE INDEX IX_ready_Ventas_fecha ON ready.Ventas (Fecha) INCLUDE (ImporteLinea, Cantidad);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_ready_Ventas_producto' AND object_id = OBJECT_ID(N'ready.Ventas'))
    CREATE INDEX IX_ready_Ventas_producto ON ready.Ventas (IdProducto);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_ready_Ventas_local' AND object_id = OBJECT_ID(N'ready.Ventas'))
    CREATE INDEX IX_ready_Ventas_local ON ready.Ventas (IdLocal);
GO

/*====================================================================
  AUDITORIA
====================================================================*/

IF OBJECT_ID(N'audit.etl_execution', N'U') IS NULL
CREATE TABLE audit.etl_execution
(
    execution_id    bigint IDENTITY(1,1) NOT NULL,
    pipeline_name   varchar(100)  NOT NULL,
    start_time      datetime2(3)  NOT NULL CONSTRAINT DF_audit_exec_start DEFAULT SYSUTCDATETIME(),
    end_time        datetime2(3)  NULL,
    source_object   varchar(200)  NOT NULL,
    target_object   varchar(200)  NOT NULL,
    rows_read       int           NOT NULL CONSTRAINT DF_audit_exec_read     DEFAULT 0,
    rows_inserted   int           NOT NULL CONSTRAINT DF_audit_exec_inserted DEFAULT 0,
    rows_updated    int           NOT NULL CONSTRAINT DF_audit_exec_updated  DEFAULT 0,
    rows_rejected   int           NOT NULL CONSTRAINT DF_audit_exec_rejected DEFAULT 0,
    status          varchar(20)   NOT NULL CONSTRAINT DF_audit_exec_status   DEFAULT 'RUNNING',
    error_detail    nvarchar(max) NULL,
    watermark_start datetime2(3)  NULL,
    watermark_end   datetime2(3)  NULL,
    CONSTRAINT PK_audit_etl_execution PRIMARY KEY CLUSTERED (execution_id),
    CONSTRAINT CK_audit_exec_status CHECK (status IN ('RUNNING','SUCCESS','FAILED','PARTIAL'))
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_audit_exec_pipeline' AND object_id = OBJECT_ID(N'audit.etl_execution'))
    CREATE INDEX IX_audit_exec_pipeline ON audit.etl_execution (pipeline_name, start_time DESC);
GO

IF OBJECT_ID(N'audit.etl_watermark', N'U') IS NULL
CREATE TABLE audit.etl_watermark
(
    pipeline_name   varchar(100) NOT NULL,
    source_object   varchar(200) NOT NULL,
    watermark_column varchar(100) NOT NULL,
    watermark_value datetime2(3) NULL,
    last_execution_id bigint     NULL,
    updated_at      datetime2(3) NOT NULL CONSTRAINT DF_audit_wm_updated DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_audit_etl_watermark PRIMARY KEY CLUSTERED (pipeline_name, source_object)
);
GO

IF OBJECT_ID(N'audit.row_lineage', N'U') IS NULL
CREATE TABLE audit.row_lineage
(
    lineage_id      bigint IDENTITY(1,1) NOT NULL,
    execution_id    bigint        NOT NULL,
    source_object   varchar(200)  NOT NULL,
    target_object   varchar(200)  NOT NULL,
    business_key    varchar(200)  NOT NULL,
    operation       varchar(10)   NOT NULL,
    registered_at   datetime2(3)  NOT NULL CONSTRAINT DF_audit_lineage_reg DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_audit_row_lineage PRIMARY KEY CLUSTERED (lineage_id),
    CONSTRAINT FK_audit_lineage_execution FOREIGN KEY (execution_id) REFERENCES audit.etl_execution (execution_id)
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_audit_lineage_exec' AND object_id = OBJECT_ID(N'audit.row_lineage'))
    CREATE INDEX IX_audit_lineage_exec ON audit.row_lineage (execution_id, target_object);
GO

/*====================================================================
  CUARENTENA
====================================================================*/

IF OBJECT_ID(N'quarantine.rejected_row', N'U') IS NULL
CREATE TABLE quarantine.rejected_row
(
    rejected_id     bigint IDENTITY(1,1) NOT NULL,
    execution_id    bigint        NOT NULL,
    source_object   varchar(200)  NOT NULL,
    rule_code       varchar(20)   NOT NULL,
    rule_detail     nvarchar(500) NOT NULL,
    business_key    varchar(200)  NULL,
    payload         nvarchar(max) NULL,
    rejected_at     datetime2(3)  NOT NULL CONSTRAINT DF_quarantine_rejected DEFAULT SYSUTCDATETIME(),
    status          varchar(20)   NOT NULL CONSTRAINT DF_quarantine_status   DEFAULT 'PENDIENTE',
    resolved_at     datetime2(3)  NULL,
    CONSTRAINT PK_quarantine_rejected_row PRIMARY KEY CLUSTERED (rejected_id),
    CONSTRAINT CK_quarantine_status CHECK (status IN ('PENDIENTE','REPROCESADO','DESCARTADO')),
    CONSTRAINT FK_quarantine_execution FOREIGN KEY (execution_id) REFERENCES audit.etl_execution (execution_id)
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_quarantine_status' AND object_id = OBJECT_ID(N'quarantine.rejected_row'))
    CREATE INDEX IX_quarantine_status ON quarantine.rejected_row (status, rule_code);
GO

PRINT 'Staging creado correctamente.';
GO

SELECT s.name AS esquema, COUNT(*) AS tablas
FROM sys.tables t
JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE s.name IN ('raw','clean','ready','audit','quarantine')
GROUP BY s.name
ORDER BY s.name;
GO
