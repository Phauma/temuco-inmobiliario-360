"""
Nómina de Bienes Raíces SII — Temuco (comuna 09101).
Carga y consulta del catastro oficial de propiedades del SII.

Fuente: SII → Estadísticas → Bienes Raíces → Catastro de Propiedades
Formato CSV descargable por comuna. Sin costo, público.
"""
from __future__ import annotations

import csv
import io
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text,
    Index, create_engine, func,
)
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import StaticPool


# ── Base y motor ──────────────────────────────────────────────────────────────

NOMINA_DB_URL = "sqlite:///./sii_nomina.db"


class NominaBase(DeclarativeBase):
    pass


class PropiedadSII(NominaBase):
    """Una fila de la nómina de bienes raíces SII."""
    __tablename__ = "sii_nomina"

    id               = Column(Integer, primary_key=True)
    rol              = Column(String(20), unique=True, index=True)   # "MMMM-PPPP" normalizado
    manzana          = Column(String(10))
    predio           = Column(String(10))
    direccion        = Column(String(400), nullable=True)
    destino          = Column(String(100), nullable=True)            # Habitacional/Comercial/…
    sup_construida   = Column(Float, nullable=True)                  # m²
    sup_terreno      = Column(Float, nullable=True)                  # m²
    av_total_clp     = Column(Float, nullable=True)                  # avalúo total en $ CLP
    av_afecto_clp    = Column(Float, nullable=True)
    av_exento_clp    = Column(Float, nullable=True)
    av_total_uf      = Column(Float, nullable=True)                  # avalúo en UF (al cargar)
    contrib_anual_clp = Column(Float, nullable=True)                 # contribuciones CLP/año
    contrib_anual_uf  = Column(Float, nullable=True)                 # contribuciones UF/año
    estado           = Column(String(20), nullable=True)             # Vigente / Eliminado
    uf_carga         = Column(Float, nullable=True)                  # valor UF usado al importar
    fecha_carga      = Column(DateTime, default=datetime.now)
    fuente_archivo   = Column(String(200), nullable=True)            # nombre del CSV cargado


# Índice compuesto para búsqueda por dirección
Index("ix_nomina_direccion", PropiedadSII.direccion)


def _get_engine():
    if NOMINA_DB_URL.startswith("sqlite"):
        return create_engine(
            NOMINA_DB_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(NOMINA_DB_URL)


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = _get_engine()
        NominaBase.metadata.create_all(bind=_engine)
    return _engine


# ── Normalización de Rol ───────────────────────────────────────────────────────

def normalizar_rol(rol: str) -> str | None:
    """Convierte '799-12' o '0799-0012' → '0799-0012' (4-4 dígitos)."""
    rol = rol.strip().replace(" ", "")
    if "-" not in rol:
        return None
    partes = rol.split("-")
    if len(partes) != 2:
        return None
    try:
        m = str(int(partes[0])).zfill(4)
        p = str(int(partes[1])).zfill(4)
        return f"{m}-{p}"
    except ValueError:
        return None


# ── Lookup principal ──────────────────────────────────────────────────────────

def lookup_rol(rol: str) -> dict | None:
    """
    Busca un Rol en la nómina local.
    Retorna dict con datos o None si no se encuentra.
    """
    rol_norm = normalizar_rol(rol)
    if not rol_norm:
        return None

    engine = get_engine()
    with Session(engine) as session:
        prop = session.query(PropiedadSII).filter(
            PropiedadSII.rol == rol_norm
        ).first()

        if not prop:
            return None

        return _prop_to_dict(prop, fuente="nomina_local")


def lookup_direccion(texto: str, limit: int = 5) -> list[dict]:
    """
    Búsqueda parcial por dirección (para autocompletado).
    """
    engine = get_engine()
    with Session(engine) as session:
        props = session.query(PropiedadSII).filter(
            PropiedadSII.direccion.ilike(f"%{texto.upper()}%"),
            PropiedadSII.estado == "Vigente",
        ).limit(limit).all()
        return [_prop_to_dict(p, "nomina_local") for p in props]


def _prop_to_dict(prop: PropiedadSII, fuente: str) -> dict:
    return {
        "found":            True,
        "rol":              prop.rol,
        "direccion":        prop.direccion,
        "destino":          prop.destino,
        "sup_construida_m2": prop.sup_construida,
        "sup_terreno_m2":   prop.sup_terreno,
        "av_total_uf":      prop.av_total_uf,
        "av_total_clp":     prop.av_total_clp,
        "contrib_anual_uf": prop.contrib_anual_uf,
        "contrib_anual_clp": prop.contrib_anual_clp,
        "estado":           prop.estado,
        "fuente":           fuente,
        "fecha_carga":      prop.fecha_carga.strftime("%d/%m/%Y") if prop.fecha_carga else None,
        "uf_carga":         prop.uf_carga,
    }


# ── Detección de columnas ─────────────────────────────────────────────────────

# Mapeo flexible de nombres de columnas SII → campos internos
_COLUMN_MAP = {
    # Rol
    "rol_manzana":   "manzana",
    "manzana":       "manzana",
    "num_manzana":   "manzana",
    "rol_predio":    "predio",
    "predio":        "predio",
    "num_predio":    "predio",
    # Dirección
    "calle":         "calle",
    "direccion":     "calle",
    "nombre_calle":  "calle",
    "numero":        "numero",
    "num":           "numero",
    "nro":           "numero",
    # Destino
    "destino":       "destino",
    "dest":          "destino",
    "tipo_destino":  "destino",
    # Superficies
    "sup_constr":    "sup_constr",
    "sup_construida":"sup_constr",
    "sup_const":     "sup_constr",
    "sup_const_m2":  "sup_constr",
    "superficie_construida": "sup_constr",
    "sup_terreno":   "sup_terreno",
    "terreno":       "sup_terreno",
    "sup_terr":      "sup_terreno",
    # Avalúos
    "av_total":      "av_total",
    "avaluo_total":  "av_total",
    "avaluo":        "av_total",
    "av_afecto":     "av_afecto",
    "avaluo_afecto": "av_afecto",
    "av_exento":     "av_exento",
    "avaluo_exento": "av_exento",
    # Contribuciones
    "contrib_anual": "contrib",
    "contribuciones":"contrib",
    "contribucion":  "contrib",
    "contrib_1_sem": "contrib_sem",
    # Estado
    "estado":        "estado",
}


def _detect_columns(header: list[str]) -> dict[int, str]:
    """Retorna {índice_columna: campo_interno} para las columnas detectadas."""
    mapping = {}
    for i, col in enumerate(header):
        key = col.strip().lower().replace(" ", "_").replace(".", "")
        if key in _COLUMN_MAP:
            campo = _COLUMN_MAP[key]
            if campo not in mapping.values():  # primera ocurrencia gana
                mapping[i] = campo
    return mapping


# ── Parseo de valores ─────────────────────────────────────────────────────────

def _parse_clp(texto: str) -> float | None:
    """Convierte '$ 12.345.678' o '12345678' a float."""
    if not texto:
        return None
    limpio = re.sub(r"[^\d,.]", "", texto).replace(".", "").replace(",", ".")
    try:
        v = float(limpio)
        return v if v > 0 else None
    except ValueError:
        return None


def _parse_float(texto: str) -> float | None:
    if not texto:
        return None
    limpio = texto.strip().replace(",", ".")
    try:
        v = float(limpio)
        return v if v >= 0 else None
    except ValueError:
        return None


def _parse_int_str(texto: str) -> str:
    """Normaliza número a string sin decimales. '799.0' → '799'."""
    try:
        return str(int(float(texto.strip())))
    except (ValueError, AttributeError):
        return texto.strip()


# ── Cargador CSV ─────────────────────────────────────────────────────────────

def cargar_csv(
    ruta: str | Path,
    uf_valor: float = 38_000.0,
    delimitador: str = ";",
    encoding: str = "latin-1",
    verbose: bool = True,
) -> dict:
    """
    Importa la nómina de bienes raíces SII desde un archivo CSV.

    Parámetros:
        ruta:       Ruta al archivo CSV descargado del SII
        uf_valor:   Valor UF vigente al momento de carga (en CLP) para conversión
        delimitador: Separador de columnas (';' en archivos SII, ',' en otros)
        encoding:   Codificación del archivo ('latin-1' para archivos SII, 'utf-8' alternativa)
        verbose:    Imprimir progreso

    Retorna dict con estadísticas de la importación.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    engine = get_engine()
    nombre_archivo = ruta.name
    fecha_carga = datetime.now()

    stats = {
        "archivo": str(ruta),
        "total_leidas": 0,
        "importadas": 0,
        "actualizadas": 0,
        "omitidas": 0,
        "errores": 0,
        "uf_valor": uf_valor,
    }

    with open(ruta, encoding=encoding, errors="replace") as f:
        # Intentar detectar delimitador si no se especificó
        muestra = f.read(4096)
        f.seek(0)
        if delimitador == ";" and muestra.count(";") < muestra.count(","):
            delimitador = ","

        reader = csv.reader(f, delimiter=delimitador)

        try:
            header_raw = next(reader)
        except StopIteration:
            raise ValueError("El archivo CSV está vacío.")

        col_map = _detect_columns(header_raw)
        if not col_map:
            raise ValueError(
                f"No se reconocieron columnas SII en el header: {header_raw[:8]}. "
                "Verificar formato o delimitador."
            )

        if verbose:
            print(f"Columnas detectadas: {col_map}")

        with Session(engine) as session:
            for row_num, row in enumerate(reader, start=2):
                stats["total_leidas"] += 1

                try:
                    # Extraer campos
                    vals = {campo: row[idx].strip() if idx < len(row) else ""
                            for idx, campo in col_map.items()}

                    manzana_raw = _parse_int_str(vals.get("manzana", ""))
                    predio_raw  = _parse_int_str(vals.get("predio", ""))
                    if not manzana_raw or not predio_raw:
                        stats["omitidas"] += 1
                        continue

                    rol = f"{manzana_raw.zfill(4)}-{predio_raw.zfill(4)}"

                    calle  = vals.get("calle", "").strip()
                    numero = vals.get("numero", "").strip()
                    direccion = f"{calle} {numero}".strip().upper() if calle else None

                    destino = vals.get("destino", "").strip() or None

                    sup_c = _parse_float(vals.get("sup_constr", ""))
                    sup_t = _parse_float(vals.get("sup_terreno", ""))

                    av_total = _parse_clp(vals.get("av_total", ""))
                    av_afecto = _parse_clp(vals.get("av_afecto", ""))
                    av_exento = _parse_clp(vals.get("av_exento", ""))

                    # Contribuciones: usar anual si existe, sino semestral × 2
                    contrib_clp = _parse_clp(vals.get("contrib", ""))
                    if contrib_clp is None:
                        sem = _parse_clp(vals.get("contrib_sem", ""))
                        if sem is not None:
                            contrib_clp = sem * 2

                    estado = vals.get("estado", "Vigente").strip() or "Vigente"

                    # Conversión a UF
                    av_uf = round(av_total / uf_valor, 1) if av_total else None
                    contrib_uf = round(contrib_clp / uf_valor, 2) if contrib_clp else None

                    # Upsert
                    existing = session.query(PropiedadSII).filter(
                        PropiedadSII.rol == rol
                    ).first()

                    if existing:
                        existing.direccion      = direccion or existing.direccion
                        existing.destino        = destino or existing.destino
                        existing.sup_construida = sup_c
                        existing.sup_terreno    = sup_t
                        existing.av_total_clp   = av_total
                        existing.av_afecto_clp  = av_afecto
                        existing.av_exento_clp  = av_exento
                        existing.av_total_uf    = av_uf
                        existing.contrib_anual_clp = contrib_clp
                        existing.contrib_anual_uf  = contrib_uf
                        existing.estado         = estado
                        existing.uf_carga       = uf_valor
                        existing.fecha_carga    = fecha_carga
                        existing.fuente_archivo = nombre_archivo
                        stats["actualizadas"] += 1
                    else:
                        prop = PropiedadSII(
                            rol=rol,
                            manzana=manzana_raw.zfill(4),
                            predio=predio_raw.zfill(4),
                            direccion=direccion,
                            destino=destino,
                            sup_construida=sup_c,
                            sup_terreno=sup_t,
                            av_total_clp=av_total,
                            av_afecto_clp=av_afecto,
                            av_exento_clp=av_exento,
                            av_total_uf=av_uf,
                            contrib_anual_clp=contrib_clp,
                            contrib_anual_uf=contrib_uf,
                            estado=estado,
                            uf_carga=uf_valor,
                            fecha_carga=fecha_carga,
                            fuente_archivo=nombre_archivo,
                        )
                        session.add(prop)
                        stats["importadas"] += 1

                    # Commit cada 2000 filas para no sobrecargar memoria
                    if (stats["importadas"] + stats["actualizadas"]) % 2000 == 0:
                        session.commit()
                        if verbose:
                            print(f"  … {stats['importadas'] + stats['actualizadas']:,} filas procesadas")

                except Exception as e:
                    stats["errores"] += 1
                    if verbose and stats["errores"] <= 5:
                        print(f"  Error fila {row_num}: {e}")
                    continue

            session.commit()

    if verbose:
        print(
            f"\nImportación completada:\n"
            f"  Leídas:      {stats['total_leidas']:,}\n"
            f"  Importadas:  {stats['importadas']:,}\n"
            f"  Actualizadas:{stats['actualizadas']:,}\n"
            f"  Omitidas:    {stats['omitidas']:,}\n"
            f"  Errores:     {stats['errores']:,}\n"
            f"  UF usada:    ${uf_valor:,.0f}"
        )

    return stats


# ── Estadísticas de la nómina ─────────────────────────────────────────────────

def estadisticas_nomina() -> dict:
    """Retorna estadísticas de la nómina cargada para el dashboard."""
    engine = get_engine()
    with Session(engine) as session:
        total = session.query(func.count(PropiedadSII.id)).scalar() or 0
        if total == 0:
            return {"cargada": False, "total": 0}

        vigentes = session.query(func.count(PropiedadSII.id)).filter(
            PropiedadSII.estado == "Vigente"
        ).scalar() or 0

        por_destino = {}
        rows = session.query(
            PropiedadSII.destino, func.count(PropiedadSII.id)
        ).group_by(PropiedadSII.destino).all()
        for destino, cnt in rows:
            por_destino[destino or "Sin clasificar"] = cnt

        ultima_carga = session.query(func.max(PropiedadSII.fecha_carga)).scalar()
        uf_carga = session.query(PropiedadSII.uf_carga).filter(
            PropiedadSII.fecha_carga == ultima_carga
        ).first()
        fuente = session.query(PropiedadSII.fuente_archivo).filter(
            PropiedadSII.fecha_carga == ultima_carga
        ).first()

        return {
            "cargada": True,
            "total": total,
            "vigentes": vigentes,
            "por_destino": por_destino,
            "ultima_carga": ultima_carga.strftime("%d/%m/%Y %H:%M") if ultima_carga else None,
            "uf_carga": uf_carga[0] if uf_carga else None,
            "fuente_archivo": fuente[0] if fuente else None,
        }
