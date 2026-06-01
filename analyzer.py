"""
Motor de análisis inmobiliario powered by Claude (claude-sonnet-4-6).
Integra datos del sector, comparables y genera análisis completo estructurado.
"""
from __future__ import annotations

import os
import json
import asyncio
from datetime import datetime

import anthropic
from dotenv import load_dotenv

from models import (
    PropertyInput, AnalysisResult, ScoreDetalle, ComparableActivo,
    NivelRiesgo, Liquidez, Recomendacion, TipoPropiedad,
    FactorVerificable, ImpactoFactor, EstadoFactor,
)
from market_data import SECTORES_TEMUCO, calcular_precio_m2_referencia
from scorer import calcular_score, label_score

load_dotenv(override=False)  # solo carga .env si la variable no existe en el sistema

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY no está configurada. "
                "Agrégala en las variables de entorno de Render."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


SYSTEM_PROMPT = """Eres un analista inmobiliario senior especializado en el mercado de Temuco, Chile.
Tienes 15 años de experiencia como tasador, corredor y analista financiero en La Araucanía.

CONTEXTO DEL MERCADO TEMUCO (datos 2024-2025):
- Temuco: capital regional La Araucanía, ~350.000 habitantes.
- Demanda universitaria (UFRO, UCT, UCTEM), hospitales, sector público y comercio.
- Moneda: UF (Unidad de Fomento). 1 UF ≈ $38.000 CLP.
- Contribuciones: 0.42%-1.2% del avalúo fiscal anual según destino SII.
- Brecha publicación/cierre histórica Temuco: 8-15%.

ARRIENDOS REALES EN TEMUCO (valores calibrados 2024):
Expresa el arriendo mensual en UF según superficie real de la propiedad, NO como UF/m².
Rangos reales por sector (casa 100m² / depto 55m²):
- Barrio Inglés / Pedro de Valdivia: casa 20-28 UF/mes | depto 12-15 UF/mes
- Pueblo Nuevo / Av. Alemania: casa 13-17 UF/mes | depto 9-12 UF/mes
- Centro Temuco: casa 14-18 UF/mes | depto 10-13 UF/mes
- Los Robles / Ricardo Saldías / Santa Rosa: casa 10-14 UF/mes | depto 7-10 UF/mes
- Amanecer / Villa Aromos: casa 8-12 UF/mes | depto 6-8 UF/mes
- Padre Las Casas / Labranza: casa 6-9 UF/mes | depto 4.5-7 UF/mes
Ajusta proporcionalmente si la superficie difiere de la referencia.

CAP RATES NETOS REALES TEMUCO (ya descontados vacancia, contribuciones, gastos):
- Dptos centro alta demanda: 3.8-5.5% neto
- Casas barrios medios: 3.0-4.8% neto
- Locales comerciales: 4.5-7.0% neto
- Bodegas/galpones: 5.0-7.5% neto
- Oficinas centro: 4.0-6.0% neto
NUNCA reportes cap rate neto >7.5% para Temuco sin justificación explícita.

PLUSVALÍA — METODOLOGÍA Y ESCENARIOS:
Debes reportar SIEMPRE tres escenarios y explicar la base:
- BASE: variación de precios de publicación por sector 2019-2024 (fuente estimada: portales)
- PESIMISTA: recesión local, sobreoferta, deterioro infraestructura, caída demanda
- OPTIMISTA: infraestructura nueva (tren, hospital, UFRO expansión), escasez oferta, demanda creciente
Ranking base actualizado:
1. Barrio Inglés: 5.0% | Pesimista 2.8% | Optimista 7.0%
2. Pedro de Valdivia: 4.8% | Pesimista 2.5% | Optimista 6.5%
3. Pueblo Nuevo: 4.2% | Pesimista 2.0% | Optimista 6.0%
4. Av. Alemania: 4.0% | Pesimista 2.0% | Optimista 5.5%
5. Centro: 3.8% | Pesimista 1.5% | Optimista 5.5%
6. Los Robles: 3.0% | Pesimista 1.0% | Optimista 4.5%
7. Ricardo Saldías / Santa Rosa: 2.8% | Pesimista 0.8% | Optimista 4.2%
8. Amanecer: 2.5% | Pesimista 0.5% | Optimista 3.8%
9. Villa Aromos: 2.0% | Pesimista 0.0% | Optimista 3.2%
10. Padre Las Casas: 1.8% | Pesimista 0.0% | Optimista 3.0%
11. Labranza: 1.5% | Pesimista 0.0% | Optimista 2.5%

VALOR DE MERCADO — METODOLOGÍA OBLIGATORIA:
Explica cómo llegaste al valor estimado mencionando:
1. Comparables activos: tipo, superficie, estado similares en el mismo sector
2. Precio/m² del sector para ese tipo de propiedad
3. Ajustes aplicados: antigüedad (-0.5-1%/año >20 años), estado, estacionamiento, gastos comunes
4. Relación con avalúo fiscal si se proporcionó (mercado suele ser 1.5-3x el avalúo fiscal en Temuco)
5. Brecha estimada respecto al precio publicado

LIMITACIONES DE DATOS — SÉ TRANSPARENTE:
- No tienes acceso al CBR (Conservador de Bienes Raíces): no puedes citar compraventas reales
- Los benchmarks son estimados de mercado de oferta (portales), no de transacciones cerradas
- Para compraventas históricas verificadas: CBR Temuco (Claro Solar 796) o conservador.cl
- Los arriendos son de referencia de mercado; ajustar según estado real de la propiedad

REGLAS DE TASACIÓN:
- Depreciación antigüedad: 0.5% anual primeros 20 años; 0.8% años 20-40; menor después
- Premium estacionamiento: +3-8 UF según zona
- Descuento gastos comunes altos: -5-15% sobre valor base
- Descuento conservación mala: -15-25%

ESTRATEGIA NEGOCIACIÓN CHILE:
- Primera oferta: 10-15% bajo precio publicado
- >90 días en mercado → propietario más flexible (-15-20%)
- Escritura rápida (30-45 días) como argumento de cierre

ANÁLISIS BASADO EN EVIDENCIA — PROTOCOLO OBLIGATORIO:

Para cada factor relevante (plusvalía, infraestructura, transporte, salud, educación, normativa,
desarrollo urbano, crecimiento económico), clasifica con rigor:

🟢 CONFIRMADO: existe documento público oficial que lo respalda directamente.
🟡 EN DESARROLLO: hay antecedentes oficiales pero no está concluido ni garantizado.
🟠 EN EVALUACIÓN: existen estudios o propuestas en proceso, sin resolución.
🔴 HIPÓTESIS: inferencia del modelo sin fuente pública verificable.

Fuentes aceptables (únicas): MOP, MINVU, SERVIU, MINSAL, Gobierno Regional de La Araucanía,
Municipalidad de Temuco, Plan Regulador Comunal, SII, CBR, INE, universidades oficiales,
documentos públicos o decretos.

LENGUAJE PROHIBIDO — nunca uses:
- "garantiza plusvalía", "inversión segura", "aumentará su valor", "sin duda", "certeza"

LENGUAJE OBLIGATORIO en su lugar:
- "podría favorecer", "existe potencial de", "podría influir positivamente",
  "es consistente con escenarios de crecimiento", "según datos disponibles"

Si confianza < 50%: agrega advertencia explícita: "Este factor corresponde a una proyección o
hipótesis y no debe utilizarse como fundamento principal para una decisión de inversión."

Si no existe fuente verificable: escribe exactamente: "Sin evidencia pública verificable al momento del análisis."

Genera entre 4 y 8 factores relevantes para la propiedad analizada, priorizando los que más
impactan la decisión de inversión o venta.

Entrega análisis concreto, honesto y basado en datos verificables. Cuando no tengas datos suficientes, dilo explícitamente."""


ANALYSIS_TOOL = {
    "name": "analisis_inmobiliario_completo",
    "description": "Entrega análisis inmobiliario completo y estructurado para propiedad en Temuco",
    "input_schema": {
        "type": "object",
        "properties": {
            "valor_mercado_uf": {"type": "number", "description": "Valor de mercado estimado en UF"},
            "rango_conservador_uf": {"type": "number"},
            "rango_base_uf": {"type": "number"},
            "rango_optimista_uf": {"type": "number"},
            "precio_max_compra_uf": {"type": "number", "description": "Precio máximo recomendado para comprar con margen"},
            "precio_publicacion_sugerido_uf": {"type": "number"},
            "precio_cierre_probable_uf": {"type": "number"},
            "brecha_publicacion_cierre_pct": {"type": "number", "description": "% diferencia entre publicación y cierre"},
            "descuento_probable_pct": {"type": "number", "description": "% descuento probable sobre precio publicado"},
            "dias_mercado_estimados": {"type": "integer"},
            "liquidez": {"type": "string", "enum": ["alta", "media", "baja", "muy_baja"]},
            "probabilidad_venta_30d": {"type": "number"},
            "probabilidad_venta_60d": {"type": "number"},
            "probabilidad_venta_90d": {"type": "number"},
            "oferta_activa_estimada": {"type": "integer", "description": "# propiedades similares activas en portal"},
            "perfil_comprador": {"type": "string"},
            "arriendo_probable_uf": {"type": "number"},
            "cap_rate_bruto_pct": {"type": "number"},
            "cap_rate_neto_pct": {"type": "number"},
            "flujo_mensual_uf": {"type": "number", "description": "Flujo neto mensual en UF"},
            "vacancia_probable_pct": {"type": "number"},
            "rentabilidad_anual_pct": {"type": "number"},
            "plusvalia_anual_estimada_pct": {"type": "number"},
            "plusvalia_pesimista_pct": {"type": "number"},
            "plusvalia_optimista_pct": {"type": "number"},
            "plusvalia_metodologia": {"type": "string", "description": "Explicación de en qué datos se basa la plusvalía y el período considerado"},
            "plusvalia_factores_riesgo": {"type": "string", "description": "Factores que podrían llevar al escenario pesimista"},
            "plusvalia_factores_positivos": {"type": "string", "description": "Factores que podrían llevar al escenario optimista"},
            "metodologia_valor_mercado": {"type": "string", "description": "Explicación paso a paso de cómo se obtuvo el valor de mercado: comparables usados, ajustes aplicados, relación con avalúo fiscal"},
            "metodologia_arriendo": {"type": "string", "description": "Explicación de cómo se estimó el arriendo: superficies de referencia, sector, estado, ajustes"},
            "metodologia_rentabilidad": {"type": "string", "description": "Cálculo detallado: arriendo bruto anual / precio compra = cap bruto; luego descuentos para llegar al neto"},
            "fuentes_datos": {"type": "string", "description": "Declaración transparente de las fuentes usadas y sus limitaciones"},
            "riesgo_urbano": {"type": "string", "enum": ["muy_bajo", "bajo", "medio", "alto", "muy_alto"]},
            "riesgo_legal": {"type": "string", "enum": ["muy_bajo", "bajo", "medio", "alto", "muy_alto"]},
            "riesgo_inundacion": {"type": "string", "enum": ["muy_bajo", "bajo", "medio", "alto", "muy_alto"]},
            "riesgo_seguridad": {"type": "string", "enum": ["muy_bajo", "bajo", "medio", "alto", "muy_alto"]},
            "potencial_reconversion": {"type": "string", "description": "Descripción del potencial de reconversión"},
            "normativa_aplicable": {"type": "string"},
            "recomendacion": {"type": "string", "enum": ["comprar", "vender", "captar", "esperar", "negociar", "descartar"]},
            "nivel_urgencia": {"type": "string", "enum": ["alta", "media", "baja"]},
            "argumentos_venta": {"type": "array", "items": {"type": "string"}, "description": "3-5 argumentos clave de venta"},
            "riesgos_principales": {"type": "array", "items": {"type": "string"}, "description": "2-4 riesgos principales"},
            "oportunidades": {"type": "array", "items": {"type": "string"}, "description": "2-4 oportunidades detectadas"},
            "estrategia_negociacion": {"type": "string", "description": "Estrategia detallada de negociación"},
            "resumen_ejecutivo": {"type": "string", "description": "Párrafo ejecutivo de 3-4 oraciones con la conclusión principal"},
            "analisis_zona": {"type": "string", "description": "Análisis del sector/barrio (4-6 oraciones)"},
            "analisis_mercado": {"type": "string", "description": "Análisis de mercado y comparables (4-6 oraciones)"},
            "analisis_financiero": {"type": "string", "description": "Análisis financiero de inversión (4-6 oraciones)"},
            "factores_verificables": {
                "type": "array",
                "description": "Tabla de factores con evidencia verificable. Entre 4 y 8 factores.",
                "items": {
                    "type": "object",
                    "properties": {
                        "factor": {"type": "string", "description": "Nombre corto del factor (ej: 'Hospital Regional Nuevo')"},
                        "descripcion": {"type": "string", "description": "Descripción objetiva del factor y su relación con la propiedad"},
                        "impacto": {"type": "string", "enum": ["positivo_alto","positivo_medio","positivo_bajo","neutro","negativo_bajo","negativo_medio","negativo_alto"]},
                        "estado": {"type": "string", "enum": ["confirmado","en_desarrollo","en_evaluacion","hipotesis"]},
                        "confianza_pct": {"type": "integer", "minimum": 0, "maximum": 100, "description": "% de confianza en el factor"},
                        "fuente": {"type": "string", "description": "Fuente oficial o 'Sin evidencia pública verificable al momento del análisis.'"},
                        "advertencia": {"type": "string", "description": "Completar si confianza_pct < 50, de lo contrario dejar vacío"}
                    },
                    "required": ["factor","descripcion","impacto","estado","confianza_pct","fuente"]
                }
            },
        },
        "required": [
            "valor_mercado_uf", "rango_conservador_uf", "rango_base_uf", "rango_optimista_uf",
            "precio_max_compra_uf", "precio_publicacion_sugerido_uf", "precio_cierre_probable_uf",
            "brecha_publicacion_cierre_pct", "descuento_probable_pct",
            "dias_mercado_estimados", "liquidez",
            "probabilidad_venta_30d", "probabilidad_venta_60d", "probabilidad_venta_90d",
            "oferta_activa_estimada", "perfil_comprador",
            "arriendo_probable_uf", "cap_rate_bruto_pct", "cap_rate_neto_pct",
            "flujo_mensual_uf", "vacancia_probable_pct", "rentabilidad_anual_pct",
            "plusvalia_anual_estimada_pct", "plusvalia_pesimista_pct", "plusvalia_optimista_pct",
            "plusvalia_metodologia", "plusvalia_factores_riesgo", "plusvalia_factores_positivos",
            "metodologia_valor_mercado", "metodologia_arriendo", "metodologia_rentabilidad",
            "fuentes_datos",
            "riesgo_urbano", "riesgo_legal", "riesgo_inundacion", "riesgo_seguridad",
            "potencial_reconversion", "normativa_aplicable",
            "recomendacion", "nivel_urgencia",
            "argumentos_venta", "riesgos_principales", "oportunidades",
            "estrategia_negociacion",
            "resumen_ejecutivo", "analisis_zona", "analisis_mercado", "analisis_financiero",
            "factores_verificables",
        ],
    },
}


def _build_user_message(prop: PropertyInput, sector_data, comparables: list, sii_data: dict | None) -> str:
    lines = [
        "## PROPIEDAD A ANALIZAR",
        f"- Dirección: {prop.direccion}",
        f"- Sector/Barrio: {prop.sector or 'No especificado'}",
        f"- Objetivo del análisis: {prop.objetivo.value}",
        f"- Tipo: {prop.tipo_propiedad.value}",
    ]

    if prop.superficie_util_m2:
        lines.append(f"- Superficie útil: {prop.superficie_util_m2} m²")
    if prop.superficie_terreno_m2:
        lines.append(f"- Superficie terreno: {prop.superficie_terreno_m2} m²")
    if prop.precio_publicado_uf:
        lines.append(f"- Precio publicado: {prop.precio_publicado_uf:.1f} UF")
        if prop.superficie_util_m2:
            pm2 = prop.precio_publicado_uf / prop.superficie_util_m2
            lines.append(f"  → Precio/m² construido: {pm2:.1f} UF/m²")
    if prop.anio_construccion:
        edad = datetime.now().year - prop.anio_construccion
        lines.append(f"- Año construcción: {prop.anio_construccion} ({edad} años)")
    if prop.estado_conservacion:
        lines.append(f"- Estado conservación: {prop.estado_conservacion.value}")
    if prop.dormitorios:
        lines.append(f"- Dormitorios: {prop.dormitorios} | Baños: {prop.banos or 'N/D'}")
    if prop.estacionamientos > 0:
        lines.append(f"- Estacionamientos: {prop.estacionamientos}")
    if prop.bodegas_extra > 0:
        lines.append(f"- Bodegas: {prop.bodegas_extra}")
    if prop.gastos_comunes_uf:
        lines.append(f"- Gastos comunes: {prop.gastos_comunes_uf:.2f} UF/mes")
    if prop.contribuciones_uf:
        lines.append(f"- Contribuciones: {prop.contribuciones_uf:.2f} UF/año")
    if prop.rol_sii:
        lines.append(f"- Rol SII: {prop.rol_sii}")
    if prop.avaluo_fiscal_uf:
        lines.append(f"- Avalúo fiscal: {prop.avaluo_fiscal_uf:.1f} UF")
    if prop.arriendo_actual_uf:
        lines.append(f"- Arriendo actual: {prop.arriendo_actual_uf:.2f} UF/mes")
    if prop.observaciones:
        lines.append(f"- Observaciones: {prop.observaciones}")

    if sector_data:
        lines += [
            "",
            "## BENCHMARKS DEL SECTOR (datos de referencia)",
            f"- Sector: {sector_data.nombre} ({sector_data.clasificacion})",
            f"- Rango precio/m² casas: {sector_data.precio_casa_uf_m2_min}-{sector_data.precio_casa_uf_m2_max} UF/m²",
            f"- Rango precio/m² dptos: {sector_data.precio_depto_uf_m2_min}-{sector_data.precio_depto_uf_m2_max} UF/m²",
            f"- Rango precio/m² terreno: {sector_data.precio_terreno_uf_m2_min}-{sector_data.precio_terreno_uf_m2_max} UF/m²",
            f"- Arriendo referencia casa 100m²: {sector_data.arriendo_casa_uf_mes_ref:.1f} UF/mes",
            f"- Arriendo referencia depto 55m²: {sector_data.arriendo_depto_uf_mes_ref:.1f} UF/mes",
            f"- Días promedio en mercado: {sector_data.dias_mercado_promedio}",
            f"- Liquidez del barrio: {sector_data.liquidez}",
            f"- Plusvalía estimada: {sector_data.plusvalia_anual_pct}% anual",
            f"- Riesgo inundación: {sector_data.riesgo_inundacion}",
            f"- Riesgo seguridad: {sector_data.riesgo_seguridad}",
            f"- Demanda arriendo: {sector_data.demanda_arriendo}",
            f"- Perfil comprador habitual: {sector_data.perfil_comprador}",
            f"- Descripción zona: {sector_data.descripcion}",
        ]

    if sii_data:
        lines += [
            "",
            "## DATOS SII CONSULTADOS",
            json.dumps(sii_data, ensure_ascii=False, indent=2),
        ]

    if comparables:
        lines += ["", "## COMPARABLES ACTIVOS EN PORTAL INMOBILIARIO"]
        for c in comparables[:6]:
            parts = [f"  • {c.get('descripcion', 'N/D')}: {c.get('precio_uf', 0):.0f} UF"]
            if c.get("superficie_m2"):
                parts.append(f" | {c['superficie_m2']:.0f} m²")
            if c.get("precio_m2"):
                parts.append(f" | {c['precio_m2']:.1f} UF/m²")
            lines.append("".join(parts))

    lines += [
        "",
        "Analiza esta propiedad en profundidad usando tu conocimiento del mercado de Temuco.",
        "Sé específico con los números. Usa los benchmarks del sector como referencia.",
        "Entrega el análisis completo usando la herramienta analisis_inmobiliario_completo.",
    ]

    return "\n".join(lines)


def _parse_factores(raw: list) -> list[FactorVerificable]:
    factores = []
    for f in raw:
        if not isinstance(f, dict):
            continue
        try:
            confianza = int(f.get("confianza_pct", 50))
            advertencia = f.get("advertencia") or (
                "Este factor corresponde a una proyección o hipótesis y no debe "
                "utilizarse como fundamento principal para una decisión de inversión."
                if confianza < 50 else None
            )
            factores.append(FactorVerificable(
                factor=f.get("factor", ""),
                descripcion=f.get("descripcion", ""),
                impacto=ImpactoFactor(f.get("impacto", "neutro")),
                estado=EstadoFactor(f.get("estado", "hipotesis")),
                confianza_pct=confianza,
                fuente=f.get("fuente") or "Sin evidencia pública verificable al momento del análisis.",
                advertencia=advertencia,
            ))
        except Exception:
            continue
    return factores


async def analizar_propiedad(
    prop: PropertyInput,
    comparables: list | None = None,
    sii_data: dict | None = None,
) -> AnalysisResult:
    sector_data = SECTORES_TEMUCO.get(prop.sector or "")

    user_msg = _build_user_message(prop, sector_data, comparables or [], sii_data)

    client = get_client()

    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        tools=[ANALYSIS_TOOL],
        tool_choice={"type": "tool", "name": "analisis_inmobiliario_completo"},
        messages=[{"role": "user", "content": user_msg}],
    )

    tool_call = next(
        (b for b in response.content if b.type == "tool_use"),
        None,
    )
    if not tool_call:
        raise ValueError("Claude no retornó análisis estructurado.")

    d = tool_call.input

    # Calcular precio/m²
    precio_m2_c = None
    precio_m2_t = None
    if prop.precio_publicado_uf:
        if prop.superficie_util_m2:
            precio_m2_c = round(prop.precio_publicado_uf / prop.superficie_util_m2, 1)
        if prop.superficie_terreno_m2:
            precio_m2_t = round(prop.precio_publicado_uf / prop.superficie_terreno_m2, 1)

    precio_m2_mercado = None
    if d.get("valor_mercado_uf") and prop.superficie_util_m2:
        precio_m2_mercado = round(d["valor_mercado_uf"] / prop.superficie_util_m2, 1)

    # Calcular score
    score = calcular_score(
        sector=sector_data,
        tipo_propiedad=prop.tipo_propiedad.value,
        precio_publicado_uf=prop.precio_publicado_uf,
        valor_mercado_uf=d.get("valor_mercado_uf"),
        estado_conservacion=prop.estado_conservacion.value if prop.estado_conservacion else None,
        riesgo_urbano=d.get("riesgo_urbano", "medio"),
        riesgo_legal=d.get("riesgo_legal", "bajo"),
        liquidez=d.get("liquidez", "media"),
        cap_rate_neto_pct=d.get("cap_rate_neto_pct"),
        potencial_reconversion=d.get("potencial_reconversion", ""),
        plusvalia_anual_pct=d.get("plusvalia_anual_estimada_pct"),
    )

    comps = [
        ComparableActivo(**c) for c in (comparables or [])
        if isinstance(c, dict) and c.get("precio_uf")
    ]

    return AnalysisResult(
        fecha_analisis=datetime.now(),
        input=prop,

        valor_mercado_uf=d["valor_mercado_uf"],
        rango_conservador_uf=d["rango_conservador_uf"],
        rango_base_uf=d["rango_base_uf"],
        rango_optimista_uf=d["rango_optimista_uf"],
        precio_m2_construido_uf=precio_m2_c,
        precio_m2_terreno_uf=precio_m2_t,
        precio_m2_mercado_uf=precio_m2_mercado,

        precio_max_compra_uf=d.get("precio_max_compra_uf", d["valor_mercado_uf"] * 0.90),
        precio_publicacion_sugerido_uf=d.get("precio_publicacion_sugerido_uf", d["valor_mercado_uf"] * 1.05),
        precio_cierre_probable_uf=d.get("precio_cierre_probable_uf", d["valor_mercado_uf"] * 0.92),
        brecha_publicacion_cierre_pct=d.get("brecha_publicacion_cierre_pct", 10.0),
        descuento_probable_pct=d.get("descuento_probable_pct", 8.0),

        dias_mercado_estimados=d.get("dias_mercado_estimados", 75),
        liquidez=Liquidez(d.get("liquidez", "media")),
        probabilidad_venta_30d=d.get("probabilidad_venta_30d", 0.25),
        probabilidad_venta_60d=d.get("probabilidad_venta_60d", 0.55),
        probabilidad_venta_90d=d.get("probabilidad_venta_90d", 0.75),
        oferta_activa_estimada=d.get("oferta_activa_estimada", 5),
        perfil_comprador=d.get("perfil_comprador", "Por determinar"),
        comparables=comps,

        arriendo_probable_uf=d.get("arriendo_probable_uf"),
        cap_rate_bruto_pct=d.get("cap_rate_bruto_pct"),
        cap_rate_neto_pct=d.get("cap_rate_neto_pct"),
        flujo_mensual_uf=d.get("flujo_mensual_uf"),
        vacancia_probable_pct=d.get("vacancia_probable_pct"),
        rentabilidad_anual_pct=d.get("rentabilidad_anual_pct"),
        plusvalia_anual_estimada_pct=d.get("plusvalia_anual_estimada_pct"),
        plusvalia_pesimista_pct=d.get("plusvalia_pesimista_pct"),
        plusvalia_optimista_pct=d.get("plusvalia_optimista_pct"),
        plusvalia_metodologia=d.get("plusvalia_metodologia"),
        plusvalia_factores_riesgo=d.get("plusvalia_factores_riesgo"),
        plusvalia_factores_positivos=d.get("plusvalia_factores_positivos"),
        metodologia_valor_mercado=d.get("metodologia_valor_mercado"),
        metodologia_arriendo=d.get("metodologia_arriendo"),
        metodologia_rentabilidad=d.get("metodologia_rentabilidad"),
        fuentes_datos=d.get("fuentes_datos"),

        riesgo_urbano=NivelRiesgo(d.get("riesgo_urbano", "medio")),
        riesgo_legal=NivelRiesgo(d.get("riesgo_legal", "bajo")),
        riesgo_inundacion=NivelRiesgo(d.get("riesgo_inundacion", "bajo")),
        riesgo_seguridad=NivelRiesgo(d.get("riesgo_seguridad", "medio")),

        potencial_reconversion=d.get("potencial_reconversion", "Por determinar"),
        normativa_aplicable=d.get("normativa_aplicable"),

        score=score,
        label_score=label_score(score.total),

        recomendacion=Recomendacion(d.get("recomendacion", "esperar")),
        nivel_urgencia=d.get("nivel_urgencia", "media"),
        argumentos_venta=d.get("argumentos_venta", []),
        riesgos_principales=d.get("riesgos_principales", []),
        oportunidades=d.get("oportunidades", []),
        estrategia_negociacion=d.get("estrategia_negociacion", ""),

        resumen_ejecutivo=d.get("resumen_ejecutivo", ""),
        analisis_zona=d.get("analisis_zona", ""),
        analisis_mercado=d.get("analisis_mercado", ""),
        analisis_financiero=d.get("analisis_financiero", ""),
        factores_verificables=_parse_factores(d.get("factores_verificables", [])),
    )
