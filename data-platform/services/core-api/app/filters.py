"""Traduccion de filtros HTTP a un WHERE parametrizado.

Las columnas se eligen de un conjunto fijo (nunca del texto del usuario); los
valores viajan como parametros `?`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

# Columnas permitidas. Si un filtro no esta aca, no puede llegar al SQL.
ALLOWED_COLUMNS = {
    "desde": "Fecha",
    "hasta": "Fecha",
    "local": "NombreLocal",
    "seccion": "Seccion",
    "producto": "NombreProducto",
}


@dataclass
class Filter:
    desde: date | None = None
    hasta: date | None = None
    local: str | None = None
    seccion: str | None = None
    producto: str | None = None
    _clauses: list[str] = field(default_factory=list)
    _params: list[object] = field(default_factory=list)

    def build(self) -> tuple[str, list[object]]:
        clauses: list[str] = []
        params: list[object] = []

        if self.desde is not None:
            clauses.append(f"[{ALLOWED_COLUMNS['desde']}] >= ?")
            params.append(self.desde)
        if self.hasta is not None:
            clauses.append(f"[{ALLOWED_COLUMNS['hasta']}] <= ?")
            params.append(self.hasta)
        if self.local:
            clauses.append(f"[{ALLOWED_COLUMNS['local']}] = ?")
            params.append(self.local)
        if self.seccion:
            clauses.append(f"[{ALLOWED_COLUMNS['seccion']}] = ?")
            params.append(self.seccion)
        if self.producto:
            clauses.append(f"[{ALLOWED_COLUMNS['producto']}] = ?")
            params.append(self.producto)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        return where, params

    def as_dict(self) -> dict[str, str | None]:
        return {
            "desde": self.desde.isoformat() if self.desde else None,
            "hasta": self.hasta.isoformat() if self.hasta else None,
            "local": self.local,
            "seccion": self.seccion,
            "producto": self.producto,
        }

    def previous_period(self) -> "Filter":
        """Periodo inmediatamente anterior de igual duracion (si hay fechas)."""
        if not self.desde or not self.hasta:
            return Filter(local=self.local, seccion=self.seccion, producto=self.producto)
        days = (self.hasta - self.desde).days + 1
        prev_hasta = self.desde - timedelta(days=1)
        prev_desde = prev_hasta - timedelta(days=days - 1)
        return Filter(
            desde=prev_desde,
            hasta=prev_hasta,
            local=self.local,
            seccion=self.seccion,
            producto=self.producto,
        )
