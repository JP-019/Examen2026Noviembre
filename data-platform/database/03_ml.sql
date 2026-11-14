-- =====================================================================
-- T11 - Tabla de experimentos de Machine Learning
-- Registra cada entrenamiento con su corte temporal y metricas.
-- Idempotente: se puede ejecutar varias veces.
-- =====================================================================
USE DataPlatform;
GO

IF OBJECT_ID(N'audit.ml_experiment', N'U') IS NULL
BEGIN
    CREATE TABLE audit.ml_experiment (
        experiment_id   int IDENTITY(1,1) NOT NULL CONSTRAINT PK_audit_ml_experiment PRIMARY KEY,
        version         nvarchar(50)   NOT NULL,
        model_name      nvarchar(100)  NOT NULL,
        trained_at      datetime2(0)   NOT NULL CONSTRAINT DF_ml_experiment_trained_at DEFAULT SYSUTCDATETIME(),
        train_periods   int            NOT NULL,
        test_periods    int            NOT NULL,
        mae             decimal(18,2)  NULL,
        rmse            decimal(18,2)  NULL,
        baseline_mae    decimal(18,2)  NULL,
        baseline_rmse   decimal(18,2)  NULL,
        parameters      nvarchar(max)  NULL,
        notes           nvarchar(max)  NULL,
        CONSTRAINT CK_ml_experiment_split CHECK (train_periods > 0 AND test_periods > 0)
    );
END
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_audit_ml_experiment_version'
      AND object_id = OBJECT_ID(N'audit.ml_experiment')
)
    CREATE INDEX IX_audit_ml_experiment_version
        ON audit.ml_experiment (version, trained_at DESC);
GO

PRINT 'Tabla audit.ml_experiment lista.';
GO

SELECT COUNT(*) AS experimentos FROM audit.ml_experiment;
GO
