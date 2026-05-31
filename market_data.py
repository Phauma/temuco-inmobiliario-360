"""
Datos de mercado inmobiliario de Temuco urbano.
Benchmarks por sector, liquidez, tendencias y clasificación de zonas.
Actualización estimada: 2024-2025.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SectorData:
    nombre: str
    clasificacion: str               # premium, alto, medio_alto, medio, medio_bajo, bajo
    precio_casa_uf_m2_min: float
    precio_casa_uf_m2_max: float
    precio_depto_uf_m2_min: float
    precio_depto_uf_m2_max: float
    precio_terreno_uf_m2_min: float
    precio_terreno_uf_m2_max: float
    precio_local_uf_m2_min: float
    precio_local_uf_m2_max: float
    # Arriendo expresado en UF/mes para superficie típica de referencia (no UF/m²)
    # Casa referencia 100m²: valor mensual típico en UF
    arriendo_casa_uf_mes_ref: float
    # Depto referencia 55m²: valor mensual típico en UF
    arriendo_depto_uf_mes_ref: float
    dias_mercado_promedio: int
    liquidez: str                    # alta, media, baja, muy_baja
    plusvalia_anual_pct: float       # % anual estimado últimos 5 años (base)
    plusvalia_pesimista_pct: float   # escenario adverso
    plusvalia_optimista_pct: float   # escenario favorable
    riesgo_inundacion: str           # muy_bajo, bajo, medio, alto, muy_alto
    riesgo_seguridad: str
    demanda_arriendo: str            # alta, media, baja
    perfil_comprador: str
    descripcion: str
    latitud: float
    longitud: float
    indice_velocidad_venta: int      # 0-100: 100=vende muy rápido
    radio_km: float = 0.8


SECTORES_TEMUCO: dict[str, SectorData] = {
    "centro": SectorData(
        nombre="Centro Histórico",
        clasificacion="medio_alto",
        precio_casa_uf_m2_min=48, precio_casa_uf_m2_max=75,
        precio_depto_uf_m2_min=52, precio_depto_uf_m2_max=85,
        precio_terreno_uf_m2_min=60, precio_terreno_uf_m2_max=120,
        precio_local_uf_m2_min=55, precio_local_uf_m2_max=110,
        arriendo_casa_uf_mes_ref=16.0,   # casa 100m²: ~16 UF/mes (~$608K CLP)
        arriendo_depto_uf_mes_ref=11.0,  # depto 55m²: ~11 UF/mes (~$418K CLP)
        dias_mercado_promedio=55, liquidez="alta",
        plusvalia_anual_pct=3.8, plusvalia_pesimista_pct=1.5, plusvalia_optimista_pct=5.5,
        riesgo_inundacion="bajo", riesgo_seguridad="medio",
        demanda_arriendo="alta",
        perfil_comprador="Profesional, inversionista, comercio",
        descripcion="Núcleo comercial y administrativo. Alta demanda de oficinas y locales. Congestión alta.",
        latitud=-38.7394, longitud=-72.5986,
        indice_velocidad_venta=82,
    ),
    "pueblo_nuevo": SectorData(
        nombre="Pueblo Nuevo",
        clasificacion="medio_alto",
        precio_casa_uf_m2_min=42, precio_casa_uf_m2_max=65,
        precio_depto_uf_m2_min=45, precio_depto_uf_m2_max=70,
        precio_terreno_uf_m2_min=35, precio_terreno_uf_m2_max=65,
        precio_local_uf_m2_min=40, precio_local_uf_m2_max=70,
        arriendo_casa_uf_mes_ref=15.0,   # casa 100m²: ~15 UF/mes
        arriendo_depto_uf_mes_ref=10.0,  # depto 55m²: ~10 UF/mes
        dias_mercado_promedio=48, liquidez="alta",
        plusvalia_anual_pct=4.2, plusvalia_pesimista_pct=2.0, plusvalia_optimista_pct=6.0,
        riesgo_inundacion="bajo", riesgo_seguridad="bajo",
        demanda_arriendo="alta",
        perfil_comprador="Familia clase media-alta, profesional joven",
        descripcion="Barrio consolidado con buena conectividad. Alta demanda residencial y gran liquidez.",
        latitud=-38.7270, longitud=-72.6050,
        indice_velocidad_venta=88,
    ),
    "pedro_valdivia": SectorData(
        nombre="Pedro de Valdivia",
        clasificacion="alto",
        precio_casa_uf_m2_min=50, precio_casa_uf_m2_max=80,
        precio_depto_uf_m2_min=55, precio_depto_uf_m2_max=90,
        precio_terreno_uf_m2_min=45, precio_terreno_uf_m2_max=80,
        precio_local_uf_m2_min=50, precio_local_uf_m2_max=85,
        arriendo_casa_uf_mes_ref=22.0,   # casa 120m²: ~22 UF/mes (~$836K CLP)
        arriendo_depto_uf_mes_ref=13.0,  # depto 60m²: ~13 UF/mes
        dias_mercado_promedio=42, liquidez="alta",
        plusvalia_anual_pct=4.8, plusvalia_pesimista_pct=2.5, plusvalia_optimista_pct=6.5,
        riesgo_inundacion="muy_bajo", riesgo_seguridad="muy_bajo",
        demanda_arriendo="alta",
        perfil_comprador="Profesional, médico, ejecutivo, familia NSE alto",
        descripcion="Zona premium residencial. Propiedades de alta calidad. Excelente plusvalía y liquidez.",
        latitud=-38.7450, longitud=-72.6180,
        indice_velocidad_venta=92,
    ),
    "barrio_ingles": SectorData(
        nombre="Barrio Inglés / Las Quilas",
        clasificacion="alto",
        precio_casa_uf_m2_min=50, precio_casa_uf_m2_max=82,
        precio_depto_uf_m2_min=52, precio_depto_uf_m2_max=88,
        precio_terreno_uf_m2_min=45, precio_terreno_uf_m2_max=85,
        precio_local_uf_m2_min=45, precio_local_uf_m2_max=75,
        arriendo_casa_uf_mes_ref=25.0,   # casa 150m²: ~25 UF/mes (~$950K CLP)
        arriendo_depto_uf_mes_ref=14.0,  # depto 65m²: ~14 UF/mes
        dias_mercado_promedio=40, liquidez="alta",
        plusvalia_anual_pct=5.0, plusvalia_pesimista_pct=2.8, plusvalia_optimista_pct=7.0,
        riesgo_inundacion="muy_bajo", riesgo_seguridad="muy_bajo",
        demanda_arriendo="alta",
        perfil_comprador="Médico, ejecutivo, familia NSE A/B",
        descripcion="Sector más exclusivo de Temuco. Lotes grandes, entorno arbolado. Alta demanda y escasa oferta.",
        latitud=-38.7520, longitud=-72.6310,
        indice_velocidad_venta=90,
    ),
    "alemana": SectorData(
        nombre="Avenida Alemania / Alessandri",
        clasificacion="medio_alto",
        precio_casa_uf_m2_min=42, precio_casa_uf_m2_max=68,
        precio_depto_uf_m2_min=46, precio_depto_uf_m2_max=72,
        precio_terreno_uf_m2_min=38, precio_terreno_uf_m2_max=65,
        precio_local_uf_m2_min=42, precio_local_uf_m2_max=68,
        arriendo_casa_uf_mes_ref=14.0,   # casa 100m²: ~14 UF/mes
        arriendo_depto_uf_mes_ref=10.5,  # depto 55m²: ~10.5 UF/mes
        dias_mercado_promedio=50, liquidez="alta",
        plusvalia_anual_pct=4.0, plusvalia_pesimista_pct=2.0, plusvalia_optimista_pct=5.5,
        riesgo_inundacion="bajo", riesgo_seguridad="bajo",
        demanda_arriendo="alta",
        perfil_comprador="Familia NSE C1/C2, profesional, estudiante universitario",
        descripcion="Corredor urbano consolidado. Cercanía a U. de La Frontera. Alta densidad y servicios.",
        latitud=-38.7360, longitud=-72.6150,
        indice_velocidad_venta=84,
    ),
    "los_robles": SectorData(
        nombre="Los Robles / Caupolicán Norte",
        clasificacion="medio",
        precio_casa_uf_m2_min=32, precio_casa_uf_m2_max=52,
        precio_depto_uf_m2_min=35, precio_depto_uf_m2_max=58,
        precio_terreno_uf_m2_min=25, precio_terreno_uf_m2_max=48,
        precio_local_uf_m2_min=30, precio_local_uf_m2_max=52,
        arriendo_casa_uf_mes_ref=12.0,   # casa 100m²: ~12 UF/mes (~$456K CLP)
        arriendo_depto_uf_mes_ref=8.5,   # depto 55m²: ~8.5 UF/mes
        dias_mercado_promedio=65, liquidez="media",
        plusvalia_anual_pct=3.0, plusvalia_pesimista_pct=1.0, plusvalia_optimista_pct=4.5,
        riesgo_inundacion="bajo", riesgo_seguridad="bajo",
        demanda_arriendo="media",
        perfil_comprador="Familia clase media, primera vivienda",
        descripcion="Barrio residencial consolidado. Buena calidad de vida. Precios accesibles para clase media.",
        latitud=-38.7200, longitud=-72.6020,
        indice_velocidad_venta=65,
    ),
    "santa_rosa": SectorData(
        nombre="Santa Rosa / San Sebastián",
        clasificacion="medio",
        precio_casa_uf_m2_min=30, precio_casa_uf_m2_max=50,
        precio_depto_uf_m2_min=33, precio_depto_uf_m2_max=55,
        precio_terreno_uf_m2_min=22, precio_terreno_uf_m2_max=44,
        precio_local_uf_m2_min=28, precio_local_uf_m2_max=50,
        arriendo_casa_uf_mes_ref=11.0,   # casa 100m²: ~11 UF/mes
        arriendo_depto_uf_mes_ref=8.0,   # depto 55m²: ~8 UF/mes
        dias_mercado_promedio=72, liquidez="media",
        plusvalia_anual_pct=2.8, plusvalia_pesimista_pct=0.8, plusvalia_optimista_pct=4.2,
        riesgo_inundacion="bajo", riesgo_seguridad="bajo",
        demanda_arriendo="media",
        perfil_comprador="Familia NSE C2/C3, primera vivienda joven",
        descripcion="Sector residencial de densidad media. Buena conectividad. Mercado activo y precios moderados.",
        latitud=-38.7280, longitud=-72.5850,
        indice_velocidad_venta=60,
    ),
    "amanecer": SectorData(
        nombre="Amanecer / Ñielol",
        clasificacion="medio",
        precio_casa_uf_m2_min=28, precio_casa_uf_m2_max=46,
        precio_depto_uf_m2_min=30, precio_depto_uf_m2_max=50,
        precio_terreno_uf_m2_min=20, precio_terreno_uf_m2_max=40,
        precio_local_uf_m2_min=25, precio_local_uf_m2_max=46,
        arriendo_casa_uf_mes_ref=10.0,   # casa 100m²: ~10 UF/mes
        arriendo_depto_uf_mes_ref=7.5,   # depto 55m²: ~7.5 UF/mes
        dias_mercado_promedio=80, liquidez="media",
        plusvalia_anual_pct=2.5, plusvalia_pesimista_pct=0.5, plusvalia_optimista_pct=3.8,
        riesgo_inundacion="medio", riesgo_seguridad="medio",
        demanda_arriendo="media",
        perfil_comprador="Familia NSE C3, primera vivienda",
        descripcion="Sector popular consolidado. Liquidez moderada. Oportunidades en renovación.",
        latitud=-38.7180, longitud=-72.5920,
        indice_velocidad_venta=52,
    ),
    "villa_aromos": SectorData(
        nombre="Villa Los Aromos / El Bosque",
        clasificacion="medio_bajo",
        precio_casa_uf_m2_min=22, precio_casa_uf_m2_max=38,
        precio_depto_uf_m2_min=24, precio_depto_uf_m2_max=42,
        precio_terreno_uf_m2_min=15, precio_terreno_uf_m2_max=30,
        precio_local_uf_m2_min=20, precio_local_uf_m2_max=36,
        arriendo_casa_uf_mes_ref=8.5,    # casa 90m²: ~8.5 UF/mes
        arriendo_depto_uf_mes_ref=6.5,   # depto 50m²: ~6.5 UF/mes
        dias_mercado_promedio=95, liquidez="baja",
        plusvalia_anual_pct=2.0, plusvalia_pesimista_pct=0.0, plusvalia_optimista_pct=3.2,
        riesgo_inundacion="medio", riesgo_seguridad="medio",
        demanda_arriendo="media",
        perfil_comprador="Primera vivienda NSE C3/D, SERVIU",
        descripcion="Sector periférico con alta proporción de vivienda social. Baja liquidez y plusvalía moderada.",
        latitud=-38.7100, longitud=-72.5750,
        indice_velocidad_venta=38,
    ),
    "padre_las_casas": SectorData(
        nombre="Padre Las Casas",
        clasificacion="medio_bajo",
        precio_casa_uf_m2_min=18, precio_casa_uf_m2_max=35,
        precio_depto_uf_m2_min=20, precio_depto_uf_m2_max=38,
        precio_terreno_uf_m2_min=12, precio_terreno_uf_m2_max=28,
        precio_local_uf_m2_min=18, precio_local_uf_m2_max=32,
        arriendo_casa_uf_mes_ref=7.5,    # casa 90m²: ~7.5 UF/mes
        arriendo_depto_uf_mes_ref=5.5,   # depto 50m²: ~5.5 UF/mes
        dias_mercado_promedio=105, liquidez="baja",
        plusvalia_anual_pct=1.8, plusvalia_pesimista_pct=0.0, plusvalia_optimista_pct=3.0,
        riesgo_inundacion="alto", riesgo_seguridad="medio",
        demanda_arriendo="baja",
        perfil_comprador="NSE C3/D, primera vivienda económica",
        descripcion="Comuna satélite. Precios bajos pero baja liquidez. Riesgo de inundación en sectores.",
        latitud=-38.7700, longitud=-72.5680,
        indice_velocidad_venta=30,
    ),
    "labranza": SectorData(
        nombre="Labranza",
        clasificacion="bajo",
        precio_casa_uf_m2_min=14, precio_casa_uf_m2_max=28,
        precio_depto_uf_m2_min=16, precio_depto_uf_m2_max=30,
        precio_terreno_uf_m2_min=8, precio_terreno_uf_m2_max=20,
        precio_local_uf_m2_min=12, precio_local_uf_m2_max=25,
        arriendo_casa_uf_mes_ref=6.0,    # casa 90m²: ~6 UF/mes
        arriendo_depto_uf_mes_ref=4.5,   # depto 50m²: ~4.5 UF/mes
        dias_mercado_promedio=130, liquidez="muy_baja",
        plusvalia_anual_pct=1.5, plusvalia_pesimista_pct=0.0, plusvalia_optimista_pct=2.5,
        riesgo_inundacion="medio", riesgo_seguridad="bajo",
        demanda_arriendo="baja",
        perfil_comprador="NSE D/E, rural-urbano, primera vivienda económica",
        descripcion="Zona periurbana rural. Muy baja liquidez. Potencial solo en parcelas con proyecto específico.",
        latitud=-38.8200, longitud=-72.6050,
        indice_velocidad_venta=20,
    ),
    "ricardo_saldivar": SectorData(
        nombre="Ricardo Saldías / Cautín",
        clasificacion="medio",
        precio_casa_uf_m2_min=30, precio_casa_uf_m2_max=48,
        precio_depto_uf_m2_min=32, precio_depto_uf_m2_max=52,
        precio_terreno_uf_m2_min=22, precio_terreno_uf_m2_max=42,
        precio_local_uf_m2_min=28, precio_local_uf_m2_max=48,
        arriendo_casa_uf_mes_ref=11.5,   # casa 100m²: ~11.5 UF/mes
        arriendo_depto_uf_mes_ref=8.0,   # depto 55m²: ~8 UF/mes
        dias_mercado_promedio=70, liquidez="media",
        plusvalia_anual_pct=2.8, plusvalia_pesimista_pct=0.8, plusvalia_optimista_pct=4.2,
        riesgo_inundacion="bajo", riesgo_seguridad="bajo",
        demanda_arriendo="media",
        perfil_comprador="Familia NSE C2/C3, inversionista moderado",
        descripcion="Sector residencial bien ubicado. Cercanía a hospitales y equipamiento. Buen potencial.",
        latitud=-38.7350, longitud=-72.5900,
        indice_velocidad_venta=62,
    ),
}


# ── Factores de conversión y contexto económico ───────────────────────────────
UF_CLP = 38_000           # UF aproximada en CLP (actualizar según SII)
INFLACION_ANUAL = 0.045   # inflación promedio Chile

# Cap rates NETOS realistas para Temuco (descontando vacancia, contrib., gastos comunes)
# Fuente estimada: análisis de publicaciones Portal Inmobiliario + Yapo 2023-2024
CAP_RATE_REFERENCIA = {
    "departamento_centro": (0.040, 0.058),   # neto: 4-5.8%
    "casa_barrio_medio":   (0.032, 0.050),   # neto: 3.2-5%
    "local_comercial":     (0.048, 0.075),   # neto: 4.8-7.5%
    "bodega":              (0.050, 0.080),   # neto: 5-8%
    "oficina_centro":      (0.042, 0.062),   # neto: 4.2-6.2%
}
VACANCIA_REFERENCIA = {
    "alta_demanda": 0.05,    # ~18 días/año sin arrendar
    "media_demanda": 0.09,   # ~33 días/año
    "baja_demanda": 0.15,    # ~55 días/año
}

# ── Transparencia de fuentes de datos ─────────────────────────────────────────
FUENTES_DATOS = {
    "precios_venta": (
        "Estimación basada en publicaciones activas de Portal Inmobiliario, Yapo.cl y Toctoc "
        "(2022-2024). NO proviene de transacciones reales del Conservador de Bienes Raíces (CBR). "
        "Los precios de cierre reales pueden diferir en 8-15% del precio publicado."
    ),
    "plusvalia": (
        "Estimación basada en variación de precios de publicación por zona (2019-2024). "
        "Sin acceso a registros históricos de compraventas del CBR ni índices oficiales INE para Temuco. "
        "Para datos verificados, consultar directamente el CBR de Temuco o estudios de Tinsa/CBRE Chile."
    ),
    "arriendos": (
        "Valores de arriendo calibrados en base a publicaciones activas de Yapo.cl y Portal Inmobiliario "
        "para Temuco (2024). Expresados como valor mensual típico según superficie de referencia por sector. "
        "Pueden variar según estado, equipamiento y negociación individual."
    ),
    "cbr_disclaimer": (
        "IMPORTANTE: Esta plataforma NO tiene acceso directo al Conservador de Bienes Raíces de Temuco. "
        "Para obtener historial de compraventas verificado (últimos 3-5 años), solicitar certificado "
        "de dominio vigente e historial de transferencias directamente en el CBR de Temuco "
        "(calle Claro Solar 796) o en conservador.cl si está disponible en línea."
    ),
    "benchmarks": (
        "Benchmarks de precio/m² construidos a partir de análisis estadístico de publicaciones "
        "por sector (muestra estimada 2023-2024). Representativos del mercado de oferta, "
        "no del precio real de cierre. Actualización recomendada cada 6 meses."
    ),
}

# Normativa urbana Temuco resumida
NORMATIVA_ZONAS = {
    "ZC": "Zona Centro: uso mixto, altura hasta 12 pisos, densidad alta.",
    "ZR1": "Zona Residencial 1: vivienda unifamiliar, 2 pisos máx.",
    "ZR2": "Zona Residencial 2: vivienda mixta, hasta 4 pisos.",
    "ZR3": "Zona Residencial 3: densidad media, hasta 6 pisos.",
    "ZI": "Zona Industrial: usos productivos, no residencial.",
    "ZCE": "Zona Comercio Especial: grandes superficies, equipamiento.",
    "ZV": "Zona Verde: parques, sin edificación.",
    "ZER": "Zona de Expansión Residencial: periferia en consolidación.",
}

# Mapa de sectores a clasificaciones geoespaciales
HEATMAP_SCORES = {
    "barrio_ingles":    {"plusvalia": 95, "liquidez": 90, "inversion": 88, "captacion": 75},
    "pedro_valdivia":   {"plusvalia": 92, "liquidez": 88, "inversion": 85, "captacion": 78},
    "pueblo_nuevo":     {"plusvalia": 85, "liquidez": 85, "inversion": 80, "captacion": 82},
    "alemana":          {"plusvalia": 82, "liquidez": 83, "inversion": 78, "captacion": 80},
    "centro":           {"plusvalia": 78, "liquidez": 80, "inversion": 75, "captacion": 70},
    "los_robles":       {"plusvalia": 72, "liquidez": 65, "inversion": 68, "captacion": 75},
    "santa_rosa":       {"plusvalia": 68, "liquidez": 62, "inversion": 65, "captacion": 72},
    "ricardo_saldivar": {"plusvalia": 65, "liquidez": 63, "inversion": 63, "captacion": 70},
    "amanecer":         {"plusvalia": 58, "liquidez": 55, "inversion": 55, "captacion": 65},
    "villa_aromos":     {"plusvalia": 48, "liquidez": 40, "inversion": 45, "captacion": 55},
    "padre_las_casas":  {"plusvalia": 40, "liquidez": 35, "inversion": 38, "captacion": 48},
    "labranza":         {"plusvalia": 30, "liquidez": 25, "inversion": 28, "captacion": 35},
}


def get_sector(nombre: str) -> Optional[SectorData]:
    key = nombre.lower().replace(" ", "_").replace("-", "_")
    return SECTORES_TEMUCO.get(key)


def get_sector_keys() -> list[str]:
    return list(SECTORES_TEMUCO.keys())


def get_sector_names() -> list[tuple[str, str]]:
    return [(k, v.nombre) for k, v in SECTORES_TEMUCO.items()]


def calcular_precio_m2_referencia(sector_key: str, tipo: str) -> tuple[float, float]:
    sector = SECTORES_TEMUCO.get(sector_key)
    if not sector:
        return (30.0, 55.0)
    tipo = tipo.lower()
    if "depto" in tipo or "departamento" in tipo:
        return (sector.precio_depto_uf_m2_min, sector.precio_depto_uf_m2_max)
    elif "terreno" in tipo:
        return (sector.precio_terreno_uf_m2_min, sector.precio_terreno_uf_m2_max)
    elif "local" in tipo or "comercial" in tipo:
        return (sector.precio_local_uf_m2_min, sector.precio_local_uf_m2_max)
    else:
        return (sector.precio_casa_uf_m2_min, sector.precio_casa_uf_m2_max)
