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
    # Descuento típico publicación → precio real de cierre (calibrado por liquidez y sector)
    descuento_cierre_casa_pct: float = 10.0
    descuento_cierre_depto_pct: float = 8.5


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
        descuento_cierre_casa_pct=9.0, descuento_cierre_depto_pct=7.5,
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
        descuento_cierre_casa_pct=7.5, descuento_cierre_depto_pct=6.5,
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
        descuento_cierre_casa_pct=6.5, descuento_cierre_depto_pct=5.5,
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
        descuento_cierre_casa_pct=6.0, descuento_cierre_depto_pct=5.0,
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
        descuento_cierre_casa_pct=8.0, descuento_cierre_depto_pct=7.0,
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
        descuento_cierre_casa_pct=11.0, descuento_cierre_depto_pct=9.5,
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
        descuento_cierre_casa_pct=11.0, descuento_cierre_depto_pct=10.0,
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
        descuento_cierre_casa_pct=12.5, descuento_cierre_depto_pct=11.5,
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
        descuento_cierre_casa_pct=14.0, descuento_cierre_depto_pct=13.0,
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
        descuento_cierre_casa_pct=15.5, descuento_cierre_depto_pct=14.0,
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
        descuento_cierre_casa_pct=17.0, descuento_cierre_depto_pct=16.0,
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
        descuento_cierre_casa_pct=10.5, descuento_cierre_depto_pct=9.0,
    ),
}


# ── Factores de conversión y contexto económico ───────────────────────────────
UF_CLP = 38_000           # UF aproximada en CLP (actualizar según SII)
INFLACION_ANUAL = 0.045   # inflación promedio Chile

# Cap rates NETOS realistas para Temuco (NOI calibrado 2024-2025)
# Método: NOI = arriendo_anual × (1-vacancia) - contrib_SII - gastos_op
# NOTA: el mercado residencial chileno tiene cap rates comprimidos por fuerte demanda propietaria.
# La rentabilidad residencial se sostiene principalmente en plusvalía, no en flujo de arriendo.
CAP_RATE_REFERENCIA = {
    "departamento_centro": (0.028, 0.045),   # neto: 2.8-4.5% (incl. gastos comunes)
    "casa_barrio_medio":   (0.020, 0.035),   # neto: 2.0-3.5%
    "local_comercial":     (0.048, 0.075),   # neto: 4.8-7.5%
    "bodega":              (0.050, 0.080),   # neto: 5.0-8.0%
    "oficina_centro":      (0.040, 0.060),   # neto: 4.0-6.0%
}

# Vacancia calibrada para Temuco (reemplaza valores anteriores de 5/9/15%)
# Datos base: ratio rotación observado en publicaciones activas 2022-2024
VACANCIA_CALIBRADA = {
    "alta":  0.025,   # 2.5% ≈ 9 días/año | Barrio Inglés, Pedro Valdivia, Pueblo Nuevo, Alemania
    "media": 0.045,   # 4.5% ≈ 16 días/año | Centro, Los Robles, Ricardo Saldías, Santa Rosa
    "baja":  0.070,   # 7.0% ≈ 26 días/año | Amanecer, Villa Aromos, Padre Las Casas, Labranza
}
VACANCIA_JUSTIFICACION = {
    "alta":  "Demanda universitaria + profesional sostenida. Rotación baja observada.",
    "media": "Demanda moderada. Vacancia típica del mercado informal chileno.",
    "baja":  "Sectores periféricos. Mayor dificultad de colocación y rotación alta.",
    "fuente": "Estimación propia; sin estadísticas oficiales de vacancia disponibles para Temuco.",
}
# Alias para compatibilidad con código anterior
VACANCIA_REFERENCIA = {
    "alta_demanda":  VACANCIA_CALIBRADA["alta"],
    "media_demanda": VACANCIA_CALIBRADA["media"],
    "baja_demanda":  VACANCIA_CALIBRADA["baja"],
}

# Contribuciones SII calibradas para propiedad habitacional arrendada
# Tasa SII 1.2% s/avalúo fiscal; avalúo fiscal ≈ 60% valor comercial → efectiva 0.72%
CONTRIBUCIONES_SII = {
    "habitacional": {
        "ratio_avaluo": 0.60,
        "tasa":         0.012,
        "efectiva":     0.0072,
        "nota": "SII: 1.2% s/avalúo. Avalúo ≈ 60% valor comercial → 0.72% efectivo.",
    },
    "comercial": {
        "ratio_avaluo": 0.65,
        "tasa":         0.0158,
        "efectiva":     0.01027,
        "nota": "Promedio no habitacional SII. Verificar destino específico.",
    },
    "industrial": {
        "ratio_avaluo": 0.60,
        "tasa":         0.020,
        "efectiva":     0.012,
        "nota": "Industrial/bodega: 2.0% s/avalúo fiscal.",
    },
}

# Gastos operacionales por escenario de gestión
GASTOS_OPERACIONALES = {
    "autoadmin": {
        "mantención":         0.035,   # 3.5% arriendo anual
        "seguro_pct_precio":  0.002,   # 0.2% valor comercial/año
        "admin_corredor":     0.000,
        "reserva_reposición": 0.020,   # 2.0% arriendo anual
        "total_pct_arriendo": 0.055,   # subtotal sobre arriendo (excluye seguro)
        "descripcion": "Propietario autogestiona. Sin comisión corredora.",
    },
    "profesional": {
        "mantención":         0.035,
        "seguro_pct_precio":  0.002,
        "admin_corredor":     0.090,   # 9% arriendo (~1 mes/año ÷ 11 meses efectivos)
        "reserva_reposición": 0.020,
        "total_pct_arriendo": 0.145,   # subtotal sobre arriendo (excluye seguro)
        "descripcion": "Corredora gestiona arriendo. Comisión ~9% anual.",
    },
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


# ── Metadatos de fuente y confiabilidad por sector ────────────────────────────

@dataclass
class SectorMetadata:
    """Transparencia: fuente, cobertura y calidad de datos por sector."""
    n_obs_venta: int          # publicaciones activas de venta analizadas (estimado)
    n_obs_arriendo: int       # publicaciones activas de arriendo analizadas (estimado)
    fuente_precios: str
    fuente_arriendos: str
    fecha_captura: str
    precio_m2_min: float      # precio venta casa (UF/m²) — mínimo observado
    precio_m2_mediana: float  # punto medio del rango; no mediana estadística
    precio_m2_max: float
    arr_casa_min: float       # arriendo casa (UF/mes) — mínimo referencial
    arr_casa_mediana: float
    arr_casa_max: float
    arr_depto_min: float      # arriendo depto (UF/mes)
    arr_depto_mediana: float
    arr_depto_max: float

    @property
    def baja_conf_venta(self) -> bool:
        return self.n_obs_venta < 20

    @property
    def baja_conf_arriendo(self) -> bool:
        return self.n_obs_arriendo < 20

    @property
    def baja_conf_any(self) -> bool:
        return self.baja_conf_venta or self.baja_conf_arriendo

    @property
    def nivel_confianza(self) -> str:
        if not self.baja_conf_venta and not self.baja_conf_arriendo:
            return "alta"
        if self.baja_conf_venta and self.baja_conf_arriendo:
            return "baja"
        return "media"


METADATA_SECTORES: dict[str, SectorMetadata] = {
    "centro": SectorMetadata(
        n_obs_venta=45, n_obs_arriendo=35,
        fuente_precios="Portal Inmobiliario / Yapo.cl",
        fuente_arriendos="Yapo.cl / Portal Inmobiliario",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=48.0, precio_m2_mediana=61.5, precio_m2_max=75.0,
        arr_casa_min=13.0, arr_casa_mediana=16.0, arr_casa_max=20.0,
        arr_depto_min=9.0, arr_depto_mediana=11.0, arr_depto_max=13.5,
    ),
    "pueblo_nuevo": SectorMetadata(
        n_obs_venta=38, n_obs_arriendo=28,
        fuente_precios="Portal Inmobiliario / Yapo.cl",
        fuente_arriendos="Yapo.cl / Portal Inmobiliario",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=42.0, precio_m2_mediana=53.5, precio_m2_max=65.0,
        arr_casa_min=12.0, arr_casa_mediana=15.0, arr_casa_max=19.0,
        arr_depto_min=8.0, arr_depto_mediana=10.0, arr_depto_max=12.5,
    ),
    "pedro_valdivia": SectorMetadata(
        n_obs_venta=22, n_obs_arriendo=16,
        fuente_precios="Portal Inmobiliario / Yapo.cl",
        fuente_arriendos="Yapo.cl",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=50.0, precio_m2_mediana=65.0, precio_m2_max=80.0,
        arr_casa_min=18.0, arr_casa_mediana=22.0, arr_casa_max=27.0,
        arr_depto_min=11.0, arr_depto_mediana=13.0, arr_depto_max=16.0,
    ),
    "barrio_ingles": SectorMetadata(
        n_obs_venta=12, n_obs_arriendo=8,
        fuente_precios="Portal Inmobiliario",
        fuente_arriendos="Yapo.cl",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=50.0, precio_m2_mediana=66.0, precio_m2_max=82.0,
        arr_casa_min=20.0, arr_casa_mediana=25.0, arr_casa_max=31.0,
        arr_depto_min=11.0, arr_depto_mediana=14.0, arr_depto_max=17.5,
    ),
    "alemana": SectorMetadata(
        n_obs_venta=42, n_obs_arriendo=32,
        fuente_precios="Portal Inmobiliario / Yapo.cl",
        fuente_arriendos="Yapo.cl / Portal Inmobiliario",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=42.0, precio_m2_mediana=55.0, precio_m2_max=68.0,
        arr_casa_min=11.0, arr_casa_mediana=14.0, arr_casa_max=18.0,
        arr_depto_min=8.5, arr_depto_mediana=10.5, arr_depto_max=13.0,
    ),
    "los_robles": SectorMetadata(
        n_obs_venta=28, n_obs_arriendo=20,
        fuente_precios="Portal Inmobiliario / Yapo.cl",
        fuente_arriendos="Yapo.cl / Portal Inmobiliario",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=32.0, precio_m2_mediana=42.0, precio_m2_max=52.0,
        arr_casa_min=9.5, arr_casa_mediana=12.0, arr_casa_max=15.0,
        arr_depto_min=7.0, arr_depto_mediana=8.5, arr_depto_max=10.5,
    ),
    "santa_rosa": SectorMetadata(
        n_obs_venta=25, n_obs_arriendo=17,
        fuente_precios="Portal Inmobiliario / Yapo.cl",
        fuente_arriendos="Yapo.cl",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=30.0, precio_m2_mediana=40.0, precio_m2_max=50.0,
        arr_casa_min=9.0, arr_casa_mediana=11.0, arr_casa_max=14.0,
        arr_depto_min=6.5, arr_depto_mediana=8.0, arr_depto_max=10.0,
    ),
    "amanecer": SectorMetadata(
        n_obs_venta=18, n_obs_arriendo=12,
        fuente_precios="Portal Inmobiliario / Yapo.cl",
        fuente_arriendos="Yapo.cl",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=28.0, precio_m2_mediana=37.0, precio_m2_max=46.0,
        arr_casa_min=8.0, arr_casa_mediana=10.0, arr_casa_max=13.0,
        arr_depto_min=6.0, arr_depto_mediana=7.5, arr_depto_max=9.5,
    ),
    "villa_aromos": SectorMetadata(
        n_obs_venta=15, n_obs_arriendo=10,
        fuente_precios="Portal Inmobiliario / Yapo.cl",
        fuente_arriendos="Yapo.cl",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=22.0, precio_m2_mediana=30.0, precio_m2_max=38.0,
        arr_casa_min=7.0, arr_casa_mediana=8.5, arr_casa_max=11.0,
        arr_depto_min=5.5, arr_depto_mediana=6.5, arr_depto_max=8.0,
    ),
    "padre_las_casas": SectorMetadata(
        n_obs_venta=16, n_obs_arriendo=9,
        fuente_precios="Portal Inmobiliario / Yapo.cl",
        fuente_arriendos="Yapo.cl",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=18.0, precio_m2_mediana=26.5, precio_m2_max=35.0,
        arr_casa_min=6.0, arr_casa_mediana=7.5, arr_casa_max=10.0,
        arr_depto_min=4.5, arr_depto_mediana=5.5, arr_depto_max=7.0,
    ),
    "labranza": SectorMetadata(
        n_obs_venta=8, n_obs_arriendo=5,
        fuente_precios="Yapo.cl",
        fuente_arriendos="Yapo.cl",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=14.0, precio_m2_mediana=21.0, precio_m2_max=28.0,
        arr_casa_min=5.0, arr_casa_mediana=6.0, arr_casa_max=8.0,
        arr_depto_min=3.5, arr_depto_mediana=4.5, arr_depto_max=5.5,
    ),
    "ricardo_saldivar": SectorMetadata(
        n_obs_venta=20, n_obs_arriendo=14,
        fuente_precios="Portal Inmobiliario / Yapo.cl",
        fuente_arriendos="Yapo.cl",
        fecha_captura="2024 Q3–Q4",
        precio_m2_min=30.0, precio_m2_mediana=39.0, precio_m2_max=48.0,
        arr_casa_min=9.5, arr_casa_mediana=11.5, arr_casa_max=14.5,
        arr_depto_min=6.5, arr_depto_mediana=8.0, arr_depto_max=10.0,
    ),
}


def calcular_rentabilidades_sector(sk: str) -> dict:
    """Cap rate calibrado, retorno total (3 escenarios) y rentabilidades por sector."""
    sector = SECTORES_TEMUCO.get(sk)
    meta   = METADATA_SECTORES.get(sk)
    if not sector or not meta:
        return {}

    precio    = meta.precio_m2_mediana * 100   # referencia 100 m²
    arr_anual = meta.arr_casa_mediana * 12

    bruto = arr_anual / precio * 100

    # Neta simplificada: descuento plano 15% (referencia rápida)
    neta_simple = arr_anual * 0.85 / precio * 100

    # Vacancia calibrada
    vacancia = VACANCIA_CALIBRADA.get(sector.demanda_arriendo, VACANCIA_CALIBRADA["media"])

    # Contribuciones SII habitacional: 0.72% valor comercial
    contrib = precio * CONTRIBUCIONES_SII["habitacional"]["efectiva"]

    # Gastos operacionales — escenario autoadmin
    g_auto = GASTOS_OPERACIONALES["autoadmin"]
    gastos_auto = arr_anual * g_auto["total_pct_arriendo"] + precio * g_auto["seguro_pct_precio"]

    # Gastos operacionales — escenario profesional
    g_prof = GASTOS_OPERACIONALES["profesional"]
    gastos_prof = arr_anual * g_prof["total_pct_arriendo"] + precio * g_prof["seguro_pct_precio"]

    # NOI por escenario
    ing_efectivo = arr_anual * (1 - vacancia)
    noi_auto = ing_efectivo - contrib - gastos_auto
    noi_prof = ing_efectivo - contrib - gastos_prof

    cap_auto = round(max(noi_auto / precio * 100, 0.5), 2)
    cap_prof = round(max(noi_prof / precio * 100, 0.5), 2)

    # Cap Rate institucional (autoadmin = referencia principal)
    cap_inst = cap_auto

    # Retorno Total = Cap Rate Neto + Plusvalía (3 escenarios de plusvalía)
    plus_pesimista = sector.plusvalia_pesimista_pct
    plus_base      = sector.plusvalia_anual_pct
    plus_optimista = sector.plusvalia_optimista_pct

    # Precio de cierre estimado (publicación × (1 - descuento))
    desc_casa  = sector.descuento_cierre_casa_pct
    desc_depto = sector.descuento_cierre_depto_pct
    pm2_pub_casa  = meta.precio_m2_mediana
    pm2_pub_depto = (meta.arr_depto_mediana / meta.arr_casa_mediana) * meta.precio_m2_mediana
    pm2_cierre_casa  = round(pm2_pub_casa  * (1 - desc_casa  / 100), 1)
    pm2_cierre_depto = round(pm2_pub_depto * (1 - desc_depto / 100), 1)

    return {
        # Compatibilidad backward
        "bruto":        round(bruto, 2),
        "neta_simple":  round(neta_simple, 2),
        "cap_inst":     cap_inst,
        "vacancia_pct": round(vacancia * 100, 1),
        # Desglose calibrado
        "cap_auto":     cap_auto,
        "cap_prof":     cap_prof,
        "contrib_uf":   round(contrib, 1),
        "gastos_auto_uf": round(gastos_auto, 1),
        "gastos_prof_uf": round(gastos_prof, 1),
        "noi_auto_uf":  round(noi_auto, 1),
        "noi_prof_uf":  round(noi_prof, 1),
        "ing_efectivo_uf": round(ing_efectivo, 1),
        # Retorno Total (cap_auto + plusvalía)
        "retorno_conservador": round(cap_auto + plus_pesimista, 2),
        "retorno_base":        round(cap_auto + plus_base, 2),
        "retorno_optimista":   round(cap_auto + plus_optimista, 2),
        "plusvalia_base":      plus_base,
        "plusvalia_pesimista": plus_pesimista,
        "plusvalia_optimista": plus_optimista,
        # Precio de cierre estimado por tipo
        "descuento_cierre_casa_pct":   desc_casa,
        "descuento_cierre_depto_pct":  desc_depto,
        "precio_m2_publicacion_casa":  pm2_pub_casa,
        "precio_m2_cierre_casa":       pm2_cierre_casa,
        "precio_m2_cierre_depto":      pm2_cierre_depto,
        "fuente_descuento": "Calibrado con reportes Portal Inmobiliario/TOCTOC 2024 · sector " + sector.nombre,
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
