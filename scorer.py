"""
Sistema de scoring 0-100 para propiedades de Temuco.
Criterios y pesos transparentes, reproducibles.
"""
from __future__ import annotations

from models import ScoreDetalle
from market_data import SectorData


def calcular_score(
    sector: SectorData | None,
    tipo_propiedad: str,
    precio_publicado_uf: float | None,
    valor_mercado_uf: float | None,
    estado_conservacion: str | None,
    riesgo_urbano: str,
    riesgo_legal: str,
    liquidez: str,
    cap_rate_neto_pct: float | None,
    potencial_reconversion: str,
    plusvalia_anual_pct: float | None,
) -> ScoreDetalle:

    # 1. Precio relativo vs mercado (20 pts)
    score_precio = _score_precio(precio_publicado_uf, valor_mercado_uf)

    # 2. Ubicación (15 pts)
    score_ubicacion = _score_ubicacion(sector)

    # 3. Liquidez (15 pts)
    score_liquidez = _score_liquidez(liquidez, sector)

    # 4. Plusvalía histórica (10 pts)
    score_plusvalia = _score_plusvalia(plusvalia_anual_pct, sector)

    # 5. Rentabilidad por arriendo (10 pts)
    score_rentabilidad = _score_rentabilidad(cap_rate_neto_pct)

    # 6. Riesgo urbano (10 pts)
    score_riesgo_urbano = _score_riesgo(riesgo_urbano)

    # 7. Riesgo legal (5 pts)
    score_riesgo_legal = _score_riesgo_legal(riesgo_legal)

    # 8. Estado de conservación (5 pts)
    score_conservacion = _score_conservacion(estado_conservacion)

    # 9. Potencial de reconversión (5 pts)
    score_reconversion = _score_reconversion(potencial_reconversion, sector, tipo_propiedad)

    # 10. Facilidad de venta (5 pts)
    score_facilidad = _score_facilidad(liquidez, sector, tipo_propiedad)

    total = (
        score_precio + score_ubicacion + score_liquidez + score_plusvalia +
        score_rentabilidad + score_riesgo_urbano + score_riesgo_legal +
        score_conservacion + score_reconversion + score_facilidad
    )

    return ScoreDetalle(
        precio_relativo=score_precio,
        ubicacion=score_ubicacion,
        liquidez=score_liquidez,
        plusvalia=score_plusvalia,
        rentabilidad=score_rentabilidad,
        riesgo_urbano=score_riesgo_urbano,
        riesgo_legal=score_riesgo_legal,
        conservacion=score_conservacion,
        reconversion=score_reconversion,
        facilidad_venta=score_facilidad,
        total=min(total, 100),
    )


def label_score(total: int) -> str:
    if total >= 80:
        return "excelente"
    elif total >= 65:
        return "bueno"
    elif total >= 50:
        return "regular"
    elif total >= 35:
        return "bajo"
    else:
        return "descartar"


def _score_precio(precio_pub: float | None, valor_mercado: float | None) -> int:
    if not precio_pub or not valor_mercado or valor_mercado == 0:
        return 10  # neutro sin datos
    ratio = precio_pub / valor_mercado
    if ratio <= 0.80:   return 20   # +20% bajo mercado → oportunidad máxima
    if ratio <= 0.90:   return 17
    if ratio <= 0.97:   return 14
    if ratio <= 1.03:   return 11   # precio justo
    if ratio <= 1.10:   return 8
    if ratio <= 1.20:   return 4
    return 0                         # >20% sobre mercado → sobreprecio severo


def _score_ubicacion(sector: SectorData | None) -> int:
    if not sector:
        return 7  # neutro
    tabla = {
        "premium": 15, "alto": 13, "medio_alto": 11,
        "medio": 8, "medio_bajo": 5, "bajo": 2,
    }
    return tabla.get(sector.clasificacion, 7)


def _score_liquidez(liquidez_str: str, sector: SectorData | None) -> int:
    dias = sector.dias_mercado_promedio if sector else 75
    if liquidez_str == "alta" or dias <= 45:   return 15
    if liquidez_str == "media" or dias <= 75:  return 10
    if liquidez_str == "baja" or dias <= 120:  return 5
    return 2  # muy_baja


def _score_plusvalia(plusvalia: float | None, sector: SectorData | None) -> int:
    p = plusvalia if plusvalia is not None else (sector.plusvalia_anual_pct if sector else None)
    if p is None:   return 5
    if p >= 6.0:    return 10
    if p >= 4.5:    return 8
    if p >= 3.0:    return 6
    if p >= 1.5:    return 4
    if p >= 0:      return 2
    return 0  # negativa


def _score_rentabilidad(cap_neto: float | None) -> int:
    if cap_neto is None:   return 5
    if cap_neto >= 8.0:    return 10
    if cap_neto >= 6.5:    return 8
    if cap_neto >= 5.0:    return 6
    if cap_neto >= 3.5:    return 4
    if cap_neto >= 2.0:    return 2
    return 0


def _score_riesgo(riesgo: str) -> int:
    tabla = {"muy_bajo": 10, "bajo": 8, "medio": 5, "alto": 2, "muy_alto": 0}
    return tabla.get(riesgo, 5)


def _score_riesgo_legal(riesgo: str) -> int:
    tabla = {"muy_bajo": 5, "bajo": 4, "medio": 2, "alto": 1, "muy_alto": 0}
    return tabla.get(riesgo, 3)


def _score_conservacion(estado: str | None) -> int:
    tabla = {
        "nuevo": 5, "excelente": 5, "bueno": 4,
        "regular": 2, "malo": 1, "muy_malo": 0,
    }
    return tabla.get(estado or "regular", 2)


def _score_reconversion(potencial: str, sector: SectorData | None, tipo: str) -> int:
    potencial_l = potencial.lower() if potencial else ""
    if any(w in potencial_l for w in ["alto", "excelente", "muy_alto"]):
        return 5
    if any(w in potencial_l for w in ["medio", "moderado"]):
        return 3
    clasificacion = sector.clasificacion if sector else "medio"
    if clasificacion in ("premium", "alto", "medio_alto") and tipo in ("terreno", "mixto"):
        return 4
    return 1


def _score_facilidad(liquidez_str: str, sector: SectorData | None, tipo: str) -> int:
    base = {"alta": 5, "media": 3, "baja": 2, "muy_baja": 1}.get(liquidez_str, 2)
    if tipo in ("terreno", "bodega", "mixto"):
        base = max(base - 1, 0)
    return base
