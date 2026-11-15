# 📦 packages/ — Código compartido

Aquí vive el código reutilizable entre servicios. **No** contiene lógica de negocio
de un dominio específico.

| Paquete | Qué contiene | Por qué |
|---------|--------------|---------|
| [`common/`](common/README.md) | Utilidades, modelos/contratos, validaciones y config. | Evitar duplicar código entre servicios. |

## Reglas
- Nada de lógica de pedidos/menú/reservas aquí.
- Solo cosas **genéricas** y estables.
- Si un paquete crece demasiado, se divide en su propia carpeta.
