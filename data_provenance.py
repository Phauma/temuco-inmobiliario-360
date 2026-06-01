"""
Trazabilidad y fuentes de datos — Temuco Inmobiliario 360.
Documenta la procedencia, método de captura y nivel de confianza de cada indicador.
"""
from __future__ import annotations

from market_data import SECTORES_TEMUCO, METADATA_SECTORES, calcular_rentabilidades_sector


# ── Catálogo completo de fuentes ──────────────────────────────────────────────

FUENTES_CATALOGO = [
    {
        "id": "portal_inmobiliario",
        "nombre": "Portal Inmobiliario",
        "url": "portalinmobiliario.com",
        "tipo": "Portal público",
        "estado": "UTILIZADO",
        "uso": "Precios de venta (benchmarks manuales + comparables on-demand)",
        "acceso": "Revisión manual + scraping HTTP con rate-limiting",
        "nota": "Principal portal de compraventa en Chile. Cubre todas las tipologías. "
                "El scraping se activa solo cuando el usuario solicita comparables.",
    },
    {
        "id": "yapo",
        "nombre": "Yapo.cl",
        "url": "yapo.cl",
        "tipo": "Portal clasificados",
        "estado": "UTILIZADO",
        "uso": "Arriendos y precios de venta complementarios",
        "acceso": "Revisión manual de publicaciones activas",
        "nota": "Fuerte cobertura de arriendos residenciales. Incluye particulares y corredoras.",
    },
    {
        "id": "toctoc",
        "nombre": "TOCTOC",
        "url": "toctoc.com",
        "tipo": "Portal inmobiliario",
        "estado": "NO UTILIZADO",
        "uso": "—",
        "acceso": "—",
        "nota": "Portal con serie histórica de precios para Chile. No integrado en esta versión.",
    },
    {
        "id": "enlace",
        "nombre": "Enlace Inmobiliario",
        "url": "enlaceinmobiliario.cl",
        "tipo": "Portal inmobiliario regional",
        "estado": "NO UTILIZADO",
        "uso": "—",
        "acceso": "—",
        "nota": "Portal con cobertura regional en La Araucanía. No integrado.",
    },
    {
        "id": "portalinversionista",
        "nombre": "Portal Inversionista",
        "url": "portalinversionista.com",
        "tipo": "Portal inversión inmobiliaria",
        "estado": "NO UTILIZADO",
        "uso": "—",
        "acceso": "—",
        "nota": "Especializado en propiedades de inversión con datos financieros. No integrado.",
    },
    {
        "id": "corredoras",
        "nombre": "Sitios de corredoras locales",
        "url": "—",
        "tipo": "Corredoras Temuco",
        "estado": "NO UTILIZADO",
        "uso": "—",
        "acceso": "—",
        "nota": "Corredoras regionales (ERA Temuco, Propiedades del Sur, etc.). "
                "Datos no estructurados, no integrados en esta versión.",
    },
    {
        "id": "inmobiliarias",
        "nombre": "Avisos directos de inmobiliarias",
        "url": "—",
        "tipo": "Inmobiliarias",
        "estado": "PARCIAL",
        "uso": "Capturado indirectamente vía portales primarios",
        "acceso": "Publicaciones encontradas en Portal Inmobiliario y Yapo",
        "nota": "Los avisos de inmobiliarias que publican en portales integrados se incluyen automáticamente.",
    },
    {
        "id": "cbr",
        "nombre": "Conservador de Bienes Raíces (CBR) Temuco",
        "url": "Claro Solar 796, Temuco — conservador.cl",
        "tipo": "Registro oficial",
        "estado": "NO UTILIZADO",
        "uso": "Historial verificado de compraventas y precios de cierre",
        "acceso": "Sin API. Solo presencial o conservador.cl (cobertura limitada)",
        "nota": "FUENTE MÁS CONFIABLE para precios reales. Sin acceso al CBR, "
                "esta plataforma no puede verificar precios de cierre ni transacciones reales. "
                "Para tasaciones formales, exigir certificado CBR.",
    },
    {
        "id": "sii",
        "nombre": "SII — Servicio de Impuestos Internos",
        "url": "sii.cl",
        "tipo": "Registro oficial",
        "estado": "PARCIAL",
        "uso": "Avalúo fiscal cuando usuario provee Rol SII",
        "acceso": "Consulta via sii.cl con Rol SII",
        "nota": "El avalúo fiscal (≈60-70% del valor comercial) es un insumo para comparar precios. "
                "Solo disponible cuando el usuario ingresa el Rol SII de la propiedad.",
    },
    {
        "id": "manual",
        "nombre": "Benchmarks de mercado — análisis manual",
        "url": "—",
        "tipo": "Estimación experto",
        "estado": "UTILIZADO",
        "uso": "Rangos de precio, arriendo, días en mercado, plusvalía por sector",
        "acceso": "Análisis manual de publicaciones activas 2023–2024",
        "nota": "Benchmarks calibrados a partir de revisión sistemática de publicaciones en portales. "
                "No proviene de base de datos automatizada ni de transacciones cerradas. "
                "Requiere actualización periódica (recomendado cada 6 meses).",
    },
    {
        "id": "formula",
        "nombre": "Modelo interno (fórmulas estimadas)",
        "url": "—",
        "tipo": "Modelo derivado",
        "estado": "UTILIZADO",
        "uso": "Oferta activa, transacciones/año, velocidad de venta, riesgo sobreoferta",
        "acceso": "Calculado internamente",
        "nota": "Indicadores sin dato primario disponible. Se calculan mediante fórmulas que combinan "
                "clasificación del sector, liquidez histórica y días en mercado. "
                "NO sustituyen datos reales de portales ni del CBR.",
    },
]


# ── Metadatos de trazabilidad por tipo de indicador ───────────────────────────

INDICADORES_META = {
    "precio_venta_m2": {
        "nombre": "Precio de venta (UF/m²)",
        "fuentes_display": "Portal Inmobiliario · Yapo.cl",
        "tipo_calculo": "Observado — revisión manual",
        "advertencia": None,
        "metodologia": (
            "Rango mínimo-máximo de publicaciones activas revisadas manualmente en 2024 Q3–Q4. "
            "El valor mediano corresponde al punto medio del rango observado (no mediana estadística). "
            "No incluye precios de cierre del CBR. Los precios publicados difieren de los cierres en 8–15% típicamente."
        ),
    },
    "arriendo_casa": {
        "nombre": "Arriendo casa (UF/mes)",
        "fuentes_display": "Yapo.cl · Portal Inmobiliario",
        "tipo_calculo": "Observado — revisión manual",
        "advertencia": None,
        "metodologia": (
            "Revisión manual de publicaciones de arriendo para casas de ~100 m² por sector. "
            "El valor referencial puede variar ±20% según estado, equipamiento y negociación. "
            "No representa el precio de mercado cerrado."
        ),
    },
    "arriendo_depto": {
        "nombre": "Arriendo departamento (UF/mes)",
        "fuentes_display": "Yapo.cl · Portal Inmobiliario",
        "tipo_calculo": "Observado — revisión manual",
        "advertencia": None,
        "metodologia": (
            "Revisión manual de publicaciones de arriendo para departamentos de ~55 m². "
            "Incluye publicaciones de inmobiliarias y particulares en portales."
        ),
    },
    "oferta_activa": {
        "nombre": "Oferta activa estimada",
        "fuentes_display": "Fórmula interna (modelo)",
        "tipo_calculo": "Estimado — fórmula derivada",
        "advertencia": (
            "Oferta activa estimada con información parcial. Interpretar con cautela. "
            "Este valor NO proviene de scraping de portales. Es una estimación basada en "
            "stock del sector y tasa de rotación según liquidez."
        ),
        "metodologia": (
            "oferta_activa = stock_sector × tasa_oferta_según_liquidez. "
            "Stock: alto=250, medio_alto=450, medio=700, medio_bajo=500, bajo=300 prop. "
            "Tasa: alta liquidez=8%, media=18%, baja=30%, muy_baja=45%. "
            "Para dato real, consultar directamente Portal Inmobiliario o Yapo.cl."
        ),
    },
    "dias_mercado": {
        "nombre": "Días promedio en mercado",
        "fuentes_display": "Estimación experto (manual)",
        "tipo_calculo": "Estimado — benchmark",
        "advertencia": "Estimación sin seguimiento sistemático de publicaciones individuales.",
        "metodologia": (
            "Benchmark estimado a partir de observación de tiempos de publicación en portales 2023–2024. "
            "Sin tracking automatizado de publicaciones individuales ni datos MLS (no existe en Temuco)."
        ),
    },
    "velocidad_venta": {
        "nombre": "Índice velocidad de venta (0–100)",
        "fuentes_display": "Índice derivado — experto",
        "tipo_calculo": "Índice derivado",
        "advertencia": "Índice subjetivo. No existe sistema MLS en Temuco para validarlo.",
        "metodologia": (
            "Índice construido combinando días en mercado y nivel de liquidez estimado del sector. "
            "100 = absorción muy rápida. Refleja posición relativa entre sectores, no velocidad absoluta."
        ),
    },
    "plusvalia_anual": {
        "nombre": "Plusvalía anual estimada (%)",
        "fuentes_display": "Variación precios publicación 2019–2024",
        "tipo_calculo": "Estimado — variación precios oferta",
        "advertencia": (
            "Sin acceso al CBR, esta plusvalía no representa apreciación real de cierre. "
            "Solo mide variación de precios publicados (no de transacciones). "
            "Para plusvalía verificada: CBR Temuco o estudios Tinsa/CBRE Chile."
        ),
        "metodologia": (
            "Variación observada de precios de publicación por sector entre 2019 y 2024. "
            "Sesgo potencial: solo captura propiedades que se publican, no el mercado total."
        ),
    },
    "cap_rate_bruto": {
        "nombre": "Cap Rate Bruto (%)",
        "fuentes_display": "Calculado (precio mediana + arriendo mediana)",
        "tipo_calculo": "Calculado — derivado",
        "advertencia": None,
        "metodologia": (
            "Cap Rate Bruto = (arriendo_mensual_mediana × 12) / (precio_m2_mediana × 100) × 100. "
            "Referencia para casa de 100 m². Sin descontar ningún gasto."
        ),
    },
    "cap_rate_neto": {
        "nombre": "Cap Rate Institucional — NOI (%)",
        "fuentes_display": "Modelo NOI (precio + arriendo + parámetros)",
        "tipo_calculo": "Calculado — modelo NOI",
        "advertencia": None,
        "metodologia": (
            "NOI = arriendo_anual × (1 − vacancia%) − contribuciones (0.6% precio) − gastos_op (10% arriendo). "
            "Vacancia: alta demanda=5%, media=9%, baja=15%. "
            "Parámetros de gastos son estimaciones promedio del mercado residencial chileno."
        ),
    },
    "transacciones_anio": {
        "nombre": "Transacciones estimadas / año",
        "fuentes_display": "Fórmula interna (modelo)",
        "tipo_calculo": "Estimado — fórmula derivada",
        "advertencia": (
            "Sin acceso al CBR, las transacciones no pueden verificarse. "
            "Dato orientativo. No utilizar en análisis formal de mercado."
        ),
        "metodologia": (
            "transacciones = stock_sector × 0.12 × (365 / días_mercado). "
            "Sin datos reales del Conservador de Bienes Raíces."
        ),
    },
}


# ── Helpers de cálculo ────────────────────────────────────────────────────────

def _oferta_formula(clasificacion: str, liquidez: str) -> int:
    stock = {"premium": 150, "alto": 250, "medio_alto": 450,
             "medio": 700, "medio_bajo": 500, "bajo": 300}.get(clasificacion, 400)
    rate  = {"alta": 0.08, "media": 0.18, "baja": 0.30,
             "muy_baja": 0.45}.get(liquidez, 0.20)
    return max(3, int(stock * rate))


def _transacciones_formula(clasificacion: str, dias_mercado: int) -> int:
    stock = {"premium": 150, "alto": 250, "medio_alto": 450,
             "medio": 700, "medio_bajo": 500, "bajo": 300}.get(clasificacion, 400)
    return max(5, int(stock * 0.12 * (365 / dias_mercado)))


def _confianza_obs(n: int) -> str:
    if n >= 30:   return "alta"
    if n >= 20:   return "media"
    if n >= 10:   return "baja"
    return "muy_baja"


# ── Datos de trazabilidad por sector ─────────────────────────────────────────

def get_oferta_activa_sector(sk: str) -> dict:
    """Desglose completo de oferta activa con trazabilidad."""
    s = SECTORES_TEMUCO.get(sk)
    m = METADATA_SECTORES.get(sk)
    if not s or not m:
        return {}

    n_formula    = _oferta_formula(s.clasificacion, s.liquidez)
    n_revisadas  = m.n_obs_venta
    # ~15% descartados por duplicados entre portales, publicaciones expiradas o faltantes de precio
    n_duplicados = max(0, int(n_revisadas * 0.15))
    n_validas    = n_revisadas - n_duplicados
    # Cobertura respecto al total estimado por fórmula
    cobertura    = min(95, int(n_validas / max(n_formula, 1) * 100))

    # Nivel de confianza del indicador de oferta activa
    if n_revisadas >= 30 and cobertura >= 50:
        conf = "media"
    elif n_revisadas >= 20 and cobertura >= 15:
        conf = "baja"
    else:
        conf = "muy_baja"

    return {
        "n_formula":          n_formula,
        "n_revisadas":        n_revisadas,
        "n_duplicados":       n_duplicados,
        "n_validas":          n_validas,
        "cobertura_pct":      cobertura,
        "portales":           m.fuente_precios,
        "fecha_captura":      m.fecha_captura,
        "nivel_confianza":    conf,
        "advertencia":        INDICADORES_META["oferta_activa"]["advertencia"],
    }


def get_indicadores_sector(sk: str) -> list[dict]:
    """Tabla de trazabilidad completa para todos los indicadores de un sector."""
    s = SECTORES_TEMUCO.get(sk)
    m = METADATA_SECTORES.get(sk)
    if not s or not m:
        return []

    rent   = calcular_rentabilidades_sector(sk)
    n_v    = m.n_obs_venta
    n_a    = m.n_obs_arriendo
    n_min  = min(n_v, n_a)

    return [
        {
            "indicador":  "Precio venta casa (UF/m²)",
            "valor":      f"{m.precio_m2_min} – {m.precio_m2_max}  |  med. {m.precio_m2_mediana}",
            "fecha":      m.fecha_captura,
            "fuente":     m.fuente_precios,
            "n_obs":      n_v,
            "confianza":  _confianza_obs(n_v),
            "advertencia": None,
        },
        {
            "indicador":  "Arriendo casa (UF/mes)",
            "valor":      f"{m.arr_casa_min} – {m.arr_casa_max}  |  med. {m.arr_casa_mediana}",
            "fecha":      m.fecha_captura,
            "fuente":     m.fuente_arriendos,
            "n_obs":      n_a,
            "confianza":  _confianza_obs(n_a),
            "advertencia": None,
        },
        {
            "indicador":  "Arriendo departamento (UF/mes)",
            "valor":      f"{m.arr_depto_min} – {m.arr_depto_max}  |  med. {m.arr_depto_mediana}",
            "fecha":      m.fecha_captura,
            "fuente":     m.fuente_arriendos,
            "n_obs":      n_a,
            "confianza":  _confianza_obs(n_a),
            "advertencia": None,
        },
        {
            "indicador":  "Oferta activa estimada",
            "valor":      f"~{_oferta_formula(s.clasificacion, s.liquidez)} prop.",
            "fecha":      "Sin fecha — fórmula estática",
            "fuente":     "Fórmula interna (no scraping real)",
            "n_obs":      None,
            "confianza":  "baja",
            "advertencia": INDICADORES_META["oferta_activa"]["advertencia"],
        },
        {
            "indicador":  "Días promedio en mercado",
            "valor":      f"{s.dias_mercado_promedio} días",
            "fecha":      "2024",
            "fuente":     "Estimación experto — análisis manual",
            "n_obs":      None,
            "confianza":  "baja",
            "advertencia": INDICADORES_META["dias_mercado"]["advertencia"],
        },
        {
            "indicador":  "Índice velocidad de venta (0–100)",
            "valor":      f"{s.indice_velocidad_venta} / 100",
            "fecha":      "2024",
            "fuente":     "Índice derivado — experto",
            "n_obs":      None,
            "confianza":  "baja",
            "advertencia": INDICADORES_META["velocidad_venta"]["advertencia"],
        },
        {
            "indicador":  "Plusvalía anual base (%)",
            "valor":      (f"{s.plusvalia_anual_pct}%  |  "
                           f"pes. {s.plusvalia_pesimista_pct}%  /  opt. {s.plusvalia_optimista_pct}%"),
            "fecha":      "2019 – 2024",
            "fuente":     "Variación precios publicación — no CBR",
            "n_obs":      None,
            "confianza":  "baja",
            "advertencia": INDICADORES_META["plusvalia_anual"]["advertencia"],
        },
        {
            "indicador":  "Cap Rate Bruto (%)",
            "valor":      f"{rent.get('bruto', '—')}%",
            "fecha":      "Calculado sobre datos 2024",
            "fuente":     "Derivado: precio mediana × arriendo mediana",
            "n_obs":      n_min,
            "confianza":  _confianza_obs(n_min),
            "advertencia": None,
        },
        {
            "indicador":  "Rentabilidad neta simplificada (%)",
            "valor":      f"{rent.get('neta_simple', '—')}%",
            "fecha":      "Calculado sobre datos 2024",
            "fuente":     "Derivado: Cap Bruto − 15% gastos planos",
            "n_obs":      n_min,
            "confianza":  _confianza_obs(n_min),
            "advertencia": None,
        },
        {
            "indicador":  "Cap Rate Institucional — NOI (%)",
            "valor":      f"{rent.get('cap_inst', '—')}%  (vacancia {rent.get('vacancia_pct', '—')}%)",
            "fecha":      "Calculado sobre datos 2024",
            "fuente":     "Modelo NOI (precio + arriendo + parámetros estimados)",
            "n_obs":      n_min,
            "confianza":  _confianza_obs(n_min),
            "advertencia": None,
        },
        {
            "indicador":  "Transacciones estimadas / año",
            "valor":      f"~{_transacciones_formula(s.clasificacion, s.dias_mercado_promedio)} ops.",
            "fecha":      "Sin fecha — fórmula estática",
            "fuente":     "Fórmula interna (sin datos CBR)",
            "n_obs":      None,
            "confianza":  "muy_baja",
            "advertencia": INDICADORES_META["transacciones_anio"]["advertencia"],
        },
    ]


def get_all_provenance() -> dict:
    """Dato completo de trazabilidad para el template."""
    sectores_data = {}
    for sk, s in SECTORES_TEMUCO.items():
        m = METADATA_SECTORES.get(sk)
        if not m:
            continue
        sectores_data[sk] = {
            "nombre":       s.nombre,
            "clasificacion": s.clasificacion,
            "indicadores":  get_indicadores_sector(sk),
            "oferta":       get_oferta_activa_sector(sk),
        }

    # Stats globales para el encabezado
    total_obs_v  = sum(METADATA_SECTORES[sk].n_obs_venta    for sk in sectores_data)
    total_obs_a  = sum(METADATA_SECTORES[sk].n_obs_arriendo for sk in sectores_data)
    n_baja       = sum(1 for sk in sectores_data
                       if get_oferta_activa_sector(sk)["nivel_confianza"] in ("baja", "muy_baja"))

    return {
        "fuentes":          FUENTES_CATALOGO,
        "indicadores_meta": INDICADORES_META,
        "sectores":         sectores_data,
        "total_obs_venta":  total_obs_v,
        "total_obs_arriendo": total_obs_a,
        "n_baja_confianza": n_baja,
        "n_sectores":       len(sectores_data),
    }
