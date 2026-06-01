from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class TipoPropiedad(str, Enum):
    CASA = "casa"
    DEPARTAMENTO = "departamento"
    TERRENO = "terreno"
    LOCAL = "local_comercial"
    OFICINA = "oficina"
    BODEGA = "bodega"
    MIXTO = "mixto"


class EstadoConservacion(str, Enum):
    NUEVO = "nuevo"
    EXCELENTE = "excelente"
    BUENO = "bueno"
    REGULAR = "regular"
    MALO = "malo"
    MUY_MALO = "muy_malo"


class NivelRiesgo(str, Enum):
    MUY_BAJO = "muy_bajo"
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"
    MUY_ALTO = "muy_alto"


class Liquidez(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"
    MUY_BAJA = "muy_baja"


class Recomendacion(str, Enum):
    COMPRAR = "comprar"
    VENDER = "vender"
    CAPTAR = "captar"
    ESPERAR = "esperar"
    NEGOCIAR = "negociar"
    DESCARTAR = "descartar"


class EstadoFactor(str, Enum):
    CONFIRMADO = "confirmado"
    EN_DESARROLLO = "en_desarrollo"
    EN_EVALUACION = "en_evaluacion"
    HIPOTESIS = "hipotesis"


class ImpactoFactor(str, Enum):
    POSITIVO_ALTO = "positivo_alto"
    POSITIVO_MEDIO = "positivo_medio"
    POSITIVO_BAJO = "positivo_bajo"
    NEUTRO = "neutro"
    NEGATIVO_BAJO = "negativo_bajo"
    NEGATIVO_MEDIO = "negativo_medio"
    NEGATIVO_ALTO = "negativo_alto"


class FactorVerificable(BaseModel):
    factor: str
    descripcion: str
    impacto: ImpactoFactor
    estado: EstadoFactor
    confianza_pct: int = Field(..., ge=0, le=100)
    fuente: str
    advertencia: Optional[str] = None


class ObjetivoAnalisis(str, Enum):
    COMPRA = "compra"
    VENTA = "venta"
    CAPTACION = "captacion"
    TASACION = "tasacion"
    INVERSION = "inversion"
    GENERAL = "general"


class PropertyInput(BaseModel):
    # Identificación
    direccion: str = Field(..., description="Dirección o descripción de ubicación")
    sector: Optional[str] = Field(None, description="Sector/barrio de Temuco")
    objetivo: ObjetivoAnalisis = ObjetivoAnalisis.GENERAL

    # Tipo y superficies
    tipo_propiedad: TipoPropiedad
    superficie_util_m2: Optional[float] = Field(None, ge=1)
    superficie_terreno_m2: Optional[float] = Field(None, ge=1)

    # Precio
    precio_publicado_uf: Optional[float] = Field(None, ge=1)

    # Características físicas
    anio_construccion: Optional[int] = Field(None, ge=1900, le=2025)
    estado_conservacion: Optional[EstadoConservacion] = None
    dormitorios: Optional[int] = Field(None, ge=0)
    banos: Optional[float] = Field(None, ge=0)
    estacionamientos: int = Field(0, ge=0)
    bodegas_extra: int = Field(0, ge=0)
    orientacion: Optional[str] = None

    # Gastos
    gastos_comunes_uf: Optional[float] = Field(None, ge=0, description="UF/mes")
    contribuciones_uf: Optional[float] = Field(None, ge=0, description="UF/año")

    # Legal y fiscal
    rol_sii: Optional[str] = Field(None, description="Ej: 799-12")
    avaluo_fiscal_uf: Optional[float] = Field(None, ge=0)

    # Inversión
    arriendo_actual_uf: Optional[float] = Field(None, ge=0, description="Si está arrendado, UF/mes actual")

    # Contexto adicional
    observaciones: Optional[str] = None
    incluir_mapa: bool = True


class ScoreDetalle(BaseModel):
    precio_relativo: int = Field(..., ge=0, le=20)
    ubicacion: int = Field(..., ge=0, le=15)
    liquidez: int = Field(..., ge=0, le=15)
    plusvalia: int = Field(..., ge=0, le=10)
    rentabilidad: int = Field(..., ge=0, le=10)
    riesgo_urbano: int = Field(..., ge=0, le=10)
    riesgo_legal: int = Field(..., ge=0, le=5)
    conservacion: int = Field(..., ge=0, le=5)
    reconversion: int = Field(..., ge=0, le=5)
    facilidad_venta: int = Field(..., ge=0, le=5)
    total: int = Field(..., ge=0, le=100)


class ComparableActivo(BaseModel):
    descripcion: str
    precio_uf: float
    superficie_m2: Optional[float] = None
    precio_m2: Optional[float] = None
    dias_publicado: Optional[int] = None
    sector: Optional[str] = None


class AnalysisResult(BaseModel):
    # Metadatos
    id: Optional[int] = None
    fecha_analisis: datetime = Field(default_factory=datetime.now)
    input: PropertyInput

    # Valoración
    valor_mercado_uf: float
    rango_conservador_uf: float
    rango_base_uf: float
    rango_optimista_uf: float
    precio_m2_construido_uf: Optional[float] = None
    precio_m2_terreno_uf: Optional[float] = None
    precio_m2_mercado_uf: Optional[float] = None

    # Negociación
    precio_max_compra_uf: float
    precio_publicacion_sugerido_uf: float
    precio_cierre_probable_uf: float
    brecha_publicacion_cierre_pct: float
    descuento_probable_pct: float

    # Mercado
    dias_mercado_estimados: int
    liquidez: Liquidez
    probabilidad_venta_30d: float
    probabilidad_venta_60d: float
    probabilidad_venta_90d: float
    oferta_activa_estimada: int
    perfil_comprador: str
    comparables: list[ComparableActivo] = []

    # Financiero
    arriendo_probable_uf: Optional[float] = None
    cap_rate_bruto_pct: Optional[float] = None
    cap_rate_neto_pct: Optional[float] = None
    flujo_mensual_uf: Optional[float] = None
    vacancia_probable_pct: Optional[float] = None
    rentabilidad_anual_pct: Optional[float] = None
    plusvalia_anual_estimada_pct: Optional[float] = None
    plusvalia_pesimista_pct: Optional[float] = None
    plusvalia_optimista_pct: Optional[float] = None
    plusvalia_metodologia: Optional[str] = None
    plusvalia_factores_riesgo: Optional[str] = None
    plusvalia_factores_positivos: Optional[str] = None
    retorno_total_conservador_pct: Optional[float] = None
    retorno_total_base_pct: Optional[float] = None
    retorno_total_optimista_pct: Optional[float] = None
    escenario_gastos: Optional[str] = None
    supuestos_financieros_detalle: Optional[str] = None
    metodologia_valor_mercado: Optional[str] = None
    metodologia_arriendo: Optional[str] = None
    metodologia_rentabilidad: Optional[str] = None
    fuentes_datos: Optional[str] = None

    # Riesgos
    riesgo_urbano: NivelRiesgo
    riesgo_legal: NivelRiesgo
    riesgo_inundacion: NivelRiesgo
    riesgo_seguridad: NivelRiesgo

    # Potencial
    potencial_reconversion: str
    normativa_aplicable: Optional[str] = None

    # Score
    score: ScoreDetalle
    label_score: str  # excelente, bueno, regular, bajo, descartar

    # Recomendación
    recomendacion: Recomendacion
    nivel_urgencia: str  # alta, media, baja
    argumentos_venta: list[str] = []
    riesgos_principales: list[str] = []
    oportunidades: list[str] = []
    estrategia_negociacion: str

    # Análisis narrativos
    resumen_ejecutivo: str
    analisis_zona: str
    analisis_mercado: str
    analisis_financiero: str

    # Factores verificables (tabla de evidencia)
    factores_verificables: list[FactorVerificable] = []

    # Precio de cierre del sector
    cierre_sector_benchmark: Optional[dict] = None  # estimado estadístico (Opción A)
    cierre_sector_local: Optional[dict] = None       # cierres reportados (Opción B)

    # CBR — Conservador de Bienes Raíces de Temuco
    cbr_encontrado: Optional[bool] = None
    cbr_inscripciones: list = []
    cbr_ultima_transferencia: Optional[dict] = None
    cbr_total: Optional[int] = None
    cbr_advertencia: Optional[str] = None
    cbr_fecha_consulta: Optional[str] = None

    # Mapa HTML (generado por Folium)
    mapa_html: Optional[str] = None
