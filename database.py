"""
Persistencia de análisis en SQLite via SQLAlchemy.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, create_engine, desc
)
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import StaticPool


DATABASE_URL = "sqlite:///./temuco_inmobiliario.db"


class Base(DeclarativeBase):
    pass


class AnalysisRecord(Base):
    __tablename__ = "analisis"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.now)
    direccion = Column(String(300))
    sector = Column(String(100))
    tipo_propiedad = Column(String(50))
    precio_publicado_uf = Column(Float, nullable=True)
    valor_mercado_uf = Column(Float)
    recomendacion = Column(String(30))
    score_total = Column(Integer)
    label_score = Column(String(20))
    objetivo = Column(String(30))
    json_input = Column(Text)
    json_result = Column(Text)


def get_engine():
    if DATABASE_URL.startswith("sqlite"):
        return create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(DATABASE_URL)


engine = get_engine()
Base.metadata.create_all(bind=engine)


def guardar_analisis(result) -> int:
    from models import AnalysisResult
    with Session(engine) as session:
        record = AnalysisRecord(
            fecha=result.fecha_analisis,
            direccion=result.input.direccion,
            sector=result.input.sector or "",
            tipo_propiedad=result.input.tipo_propiedad.value,
            precio_publicado_uf=result.input.precio_publicado_uf,
            valor_mercado_uf=result.valor_mercado_uf,
            recomendacion=result.recomendacion.value,
            score_total=result.score.total,
            label_score=result.label_score,
            objetivo=result.input.objetivo.value,
            json_input=result.input.model_dump_json(),
            json_result=result.model_dump_json(exclude={"mapa_html"}),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.id


def listar_analisis(limit: int = 20) -> list[dict]:
    with Session(engine) as session:
        records = (
            session.query(AnalysisRecord)
            .order_by(desc(AnalysisRecord.fecha))
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "fecha": r.fecha.strftime("%d/%m/%Y %H:%M"),
                "direccion": r.direccion,
                "sector": r.sector,
                "tipo": r.tipo_propiedad,
                "precio_pub": r.precio_publicado_uf,
                "valor_mercado": r.valor_mercado_uf,
                "recomendacion": r.recomendacion,
                "score": r.score_total,
                "label": r.label_score,
                "objetivo": r.objetivo,
            }
            for r in records
        ]


def obtener_analisis(id: int) -> dict | None:
    with Session(engine) as session:
        record = session.query(AnalysisRecord).filter(AnalysisRecord.id == id).first()
        if not record:
            return None
        return json.loads(record.json_result)
