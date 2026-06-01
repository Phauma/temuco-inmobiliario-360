"""
Base de datos local de precios de cierre reportados por corredores/usuarios.
Complementa el benchmark estadístico con transacciones reales verificadas por
quienes tienen acceso directo (notarios, corredores, compradores/vendedores).
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, Integer, Float, String, Boolean, Date, DateTime, Text, func
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

DB_PATH = Path(__file__).parent / "data" / "cierres.db"


class CierresBase(DeclarativeBase):
    pass


class CierreReportado(CierresBase):
    __tablename__ = "cierres_reportados"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    fecha_cierre         = Column(Date, nullable=True)
    sector               = Column(String(50), index=True)
    tipo_propiedad       = Column(String(30))          # casa, departamento, terreno, local_comercial
    superficie_m2        = Column(Float)
    precio_cierre_uf     = Column(Float)
    precio_m2_cierre_uf  = Column(Float)               # calculado al insertar
    precio_publicado_uf  = Column(Float, nullable=True)
    descuento_pct        = Column(Float, nullable=True) # (pub-cierre)/pub × 100
    dormitorios          = Column(Integer, nullable=True)
    anio_construccion    = Column(Integer, nullable=True)
    estado_conservacion  = Column(String(30), nullable=True)
    direccion_ref        = Column(String(200), nullable=True)
    notas                = Column(Text, nullable=True)
    fuente               = Column(String(50), default="corredor")
    validado             = Column(Boolean, default=False)
    fecha_registro       = Column(DateTime, default=datetime.now)


def _get_engine():
    DB_PATH.parent.mkdir(exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    CierresBase.metadata.create_all(engine)
    return engine


def registrar_cierre(
    sector: str,
    tipo_propiedad: str,
    superficie_m2: float,
    precio_cierre_uf: float,
    precio_publicado_uf: Optional[float] = None,
    dormitorios: Optional[int] = None,
    anio_construccion: Optional[int] = None,
    estado_conservacion: Optional[str] = None,
    fecha_cierre: Optional[date] = None,
    direccion_ref: Optional[str] = None,
    notas: Optional[str] = None,
    fuente: str = "corredor",
) -> int:
    """Guarda un cierre reportado y retorna el ID."""
    precio_m2 = round(precio_cierre_uf / superficie_m2, 2) if superficie_m2 > 0 else None
    descuento = None
    if precio_publicado_uf and precio_publicado_uf > 0:
        descuento = round((precio_publicado_uf - precio_cierre_uf) / precio_publicado_uf * 100, 1)

    registro = CierreReportado(
        sector=sector,
        tipo_propiedad=tipo_propiedad.lower(),
        superficie_m2=superficie_m2,
        precio_cierre_uf=round(precio_cierre_uf, 1),
        precio_m2_cierre_uf=precio_m2,
        precio_publicado_uf=precio_publicado_uf,
        descuento_pct=descuento,
        dormitorios=dormitorios,
        anio_construccion=anio_construccion,
        estado_conservacion=estado_conservacion,
        fecha_cierre=fecha_cierre,
        direccion_ref=direccion_ref,
        notas=notas,
        fuente=fuente,
    )
    engine = _get_engine()
    with Session(engine) as s:
        s.add(registro)
        s.commit()
        s.refresh(registro)
        return registro.id


def estadisticas_cierres_sector(
    sector: str,
    tipo: str = "casa",
    meses: int = 18,
) -> dict | None:
    """
    Retorna estadísticas de precio de cierre para sector+tipo.
    Devuelve None si hay menos de 3 registros (insuficiente).
    """
    engine = _get_engine()
    fecha_limite = date.today() - timedelta(days=meses * 30)
    tipo_norm = tipo.lower()

    with Session(engine) as s:
        todos = (
            s.query(CierreReportado)
            .filter(
                CierreReportado.sector == sector,
                CierreReportado.tipo_propiedad == tipo_norm,
                CierreReportado.precio_m2_cierre_uf.isnot(None),
            )
            .all()
        )
        registros = [
            r for r in todos
            if r.fecha_cierre is None or r.fecha_cierre >= fecha_limite
        ]

    if len(registros) < 3:
        return None

    precios = sorted(r.precio_m2_cierre_uf for r in registros)
    descuentos = [r.descuento_pct for r in registros if r.descuento_pct is not None]
    n = len(precios)
    avg = sum(precios) / n
    median = precios[n // 2] if n % 2 else (precios[n // 2 - 1] + precios[n // 2]) / 2

    return {
        "n": n,
        "precio_m2_promedio": round(avg, 1),
        "precio_m2_mediana":  round(median, 1),
        "precio_m2_min":      round(min(precios), 1),
        "precio_m2_max":      round(max(precios), 1),
        "descuento_promedio_pct": round(sum(descuentos) / len(descuentos), 1) if descuentos else None,
        "meses_cobertura":    meses,
        "fuente":             "cierres_reportados",
    }


def ultimos_cierres(
    sector: Optional[str] = None,
    tipo: Optional[str] = None,
    limite: int = 50,
) -> list[dict]:
    """Lista de cierres recientes, ordenados por fecha de registro desc."""
    engine = _get_engine()
    with Session(engine) as s:
        q = s.query(CierreReportado).order_by(CierreReportado.fecha_registro.desc())
        if sector:
            q = q.filter(CierreReportado.sector == sector)
        if tipo:
            q = q.filter(CierreReportado.tipo_propiedad == tipo.lower())
        registros = q.limit(limite).all()

    return [
        {
            "id":                  r.id,
            "sector":              r.sector,
            "tipo_propiedad":      r.tipo_propiedad,
            "superficie_m2":       r.superficie_m2,
            "precio_cierre_uf":    r.precio_cierre_uf,
            "precio_m2_cierre_uf": r.precio_m2_cierre_uf,
            "precio_publicado_uf": r.precio_publicado_uf,
            "descuento_pct":       r.descuento_pct,
            "dormitorios":         r.dormitorios,
            "fecha_cierre":        r.fecha_cierre.isoformat() if r.fecha_cierre else None,
            "fecha_registro":      r.fecha_registro.strftime("%d/%m/%Y") if r.fecha_registro else None,
            "fuente":              r.fuente,
            "notas":               r.notas,
        }
        for r in registros
    ]


def total_cierres() -> int:
    engine = _get_engine()
    with Session(engine) as s:
        return s.query(func.count(CierreReportado.id)).scalar() or 0


def estadisticas_globales() -> dict:
    """Resumen para dashboard: total, por sector, por tipo."""
    engine = _get_engine()
    with Session(engine) as s:
        total = s.query(func.count(CierreReportado.id)).scalar() or 0
        por_sector = (
            s.query(CierreReportado.sector, func.count(CierreReportado.id))
            .group_by(CierreReportado.sector)
            .all()
        )
        por_tipo = (
            s.query(CierreReportado.tipo_propiedad, func.count(CierreReportado.id))
            .group_by(CierreReportado.tipo_propiedad)
            .all()
        )
    return {
        "total":      total,
        "por_sector": {k: v for k, v in por_sector},
        "por_tipo":   {k: v for k, v in por_tipo},
    }
