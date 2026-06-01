"""
Temuco Inmobiliario 360 — Plataforma de análisis inmobiliario para Temuco urbano.
FastAPI + Claude AI + Datos sectoriales Temuco.
"""
from __future__ import annotations

import os
import asyncio
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from models import PropertyInput, TipoPropiedad, EstadoConservacion, ObjetivoAnalisis
from market_data import get_sector_names, SECTORES_TEMUCO, METADATA_SECTORES, calcular_rentabilidades_sector
from analyzer import analizar_propiedad
from scrapers.portal_scraper import buscar_comparables
from scrapers.sii_client import consultar_avaluo
from geo_map import generar_mapa_propiedad, generar_mapa_calor
from database import guardar_analisis, listar_analisis, obtener_analisis
from sii_nomina import lookup_rol, estadisticas_nomina

load_dotenv()

BASE_DIR = Path(__file__).parent
app = FastAPI(title="Temuco Inmobiliario 360", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def fmt_uf(value: float | None, decimals: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:,.{decimals}f} UF"


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1f}%"


def fmt_int(value: int | None) -> str:
    if value is None:
        return "—"
    return str(value)


templates.env.filters["uf"] = fmt_uf
templates.env.filters["pct"] = fmt_pct
templates.env.filters["entero"] = fmt_int


# ─── Rutas ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    historial = listar_analisis(10)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "sectores": get_sector_names(),
        "tipos": [(t.value, t.value.replace("_", " ").title()) for t in TipoPropiedad],
        "estados": [(e.value, e.value.replace("_", " ").title()) for e in EstadoConservacion],
        "objetivos": [(o.value, o.value.replace("_", " ").title()) for o in ObjetivoAnalisis],
        "historial": historial,
    })


@app.post("/analizar", response_class=HTMLResponse)
async def analizar(
    request: Request,
    direccion: str = Form(...),
    sector: str = Form(""),
    objetivo: str = Form("general"),
    tipo_propiedad: str = Form(...),
    superficie_util_m2: str = Form(""),
    superficie_terreno_m2: str = Form(""),
    precio_publicado_uf: str = Form(""),
    anio_construccion: str = Form(""),
    estado_conservacion: str = Form(""),
    dormitorios: str = Form(""),
    banos: str = Form(""),
    estacionamientos: str = Form("0"),
    bodegas_extra: str = Form("0"),
    gastos_comunes_uf: str = Form(""),
    contribuciones_uf: str = Form(""),
    rol_sii: str = Form(""),
    avaluo_fiscal_uf: str = Form(""),
    arriendo_actual_uf: str = Form(""),
    observaciones: str = Form(""),
    buscar_comparables_portal: str = Form("off"),
    consultar_sii: str = Form("off"),
    incluir_mapa: str = Form("on"),
):
    def opt_float(s: str) -> float | None:
        try:
            v = float(s.replace(",", "."))
            return v if v > 0 else None
        except (ValueError, AttributeError):
            return None

    def opt_int(s: str) -> int | None:
        try:
            v = int(s)
            return v if v > 0 else None
        except (ValueError, AttributeError):
            return None

    prop = PropertyInput(
        direccion=direccion.strip(),
        sector=sector.strip() or None,
        objetivo=ObjetivoAnalisis(objetivo),
        tipo_propiedad=TipoPropiedad(tipo_propiedad),
        superficie_util_m2=opt_float(superficie_util_m2),
        superficie_terreno_m2=opt_float(superficie_terreno_m2),
        precio_publicado_uf=opt_float(precio_publicado_uf),
        anio_construccion=opt_int(anio_construccion),
        estado_conservacion=EstadoConservacion(estado_conservacion) if estado_conservacion else None,
        dormitorios=opt_int(dormitorios),
        banos=opt_float(banos),
        estacionamientos=int(estacionamientos or 0),
        bodegas_extra=int(bodegas_extra or 0),
        gastos_comunes_uf=opt_float(gastos_comunes_uf),
        contribuciones_uf=opt_float(contribuciones_uf),
        rol_sii=rol_sii.strip() or None,
        avaluo_fiscal_uf=opt_float(avaluo_fiscal_uf),
        arriendo_actual_uf=opt_float(arriendo_actual_uf),
        observaciones=observaciones.strip() or None,
        incluir_mapa=incluir_mapa == "on",
    )

    # Tareas paralelas: comparables + SII
    comparables_task = None
    sii_task = None

    tasks = []
    if buscar_comparables_portal == "on" and prop.tipo_propiedad.value != "terreno":
        tasks.append(("comparables", buscar_comparables(
            tipo_propiedad=prop.tipo_propiedad.value,
            sector=prop.sector or "temuco",
            precio_max_uf=prop.precio_publicado_uf,
            superficie_min=prop.superficie_util_m2,
        )))
    if consultar_sii == "on" and prop.rol_sii:
        tasks.append(("sii", consultar_avaluo(prop.rol_sii)))

    comparables = []
    sii_data = None

    if tasks:
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
        for i, (name, _) in enumerate(tasks):
            result = results[i]
            if isinstance(result, Exception):
                continue
            if name == "comparables" and result:
                comparables = result
            elif name == "sii" and result:
                sii_data = result

    # Análisis principal
    try:
        result = await analizar_propiedad(prop, comparables, sii_data)
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e),
        }, status_code=500)

    # Generar mapa
    if prop.incluir_mapa:
        sector_data = SECTORES_TEMUCO.get(prop.sector or "")
        lat = sector_data.latitud if sector_data else None
        lon = sector_data.longitud if sector_data else None
        result.mapa_html = generar_mapa_propiedad(
            lat=lat, lon=lon,
            sector_key=prop.sector,
            titulo=prop.direccion[:50],
            precio_uf=prop.precio_publicado_uf,
            recomendacion=result.recomendacion.value,
            score_total=result.score.total,
        )

    # Guardar en BD
    analysis_id = guardar_analisis(result)
    result.id = analysis_id

    return templates.TemplateResponse("report.html", {
        "request": request,
        "r": result,
        "prop": prop,
        "ahora": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })


@app.get("/historial", response_class=HTMLResponse)
async def historial(request: Request):
    registros = listar_analisis(50)
    return templates.TemplateResponse("historial.html", {
        "request": request,
        "registros": registros,
    })


@app.get("/analisis/{id}", response_class=HTMLResponse)
async def ver_analisis(request: Request, id: int):
    data = obtener_analisis(id)
    if not data:
        raise HTTPException(404, "Análisis no encontrado")
    return templates.TemplateResponse("report_saved.html", {
        "request": request,
        "data": data,
        "ahora": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })


@app.get("/mapa/{capa}", response_class=HTMLResponse)
async def mapa_calor(request: Request, capa: str = "velocidad_venta"):
    capas_validas = [
        "precio_m2", "arriendo_mes", "cap_rate", "velocidad_venta",
        "plusvalia_5a", "transacciones", "oferta_activa", "riesgo_sobreoferta",
    ]
    if capa not in capas_validas:
        capa = "velocidad_venta"
    mapa_html = generar_mapa_calor(capa)
    return templates.TemplateResponse("mapa.html", {
        "request": request,
        "mapa_html": mapa_html,
        "capa_actual": capa,
        "capas": capas_validas,
    })


@app.get("/trazabilidad", response_class=HTMLResponse)
async def trazabilidad_datos(request: Request):
    from data_provenance import get_all_provenance
    data = get_all_provenance()
    return templates.TemplateResponse("trazabilidad.html", {
        "request": request,
        "data": data,
        "ahora": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })


@app.get("/transparencia", response_class=HTMLResponse)
async def transparencia_datos(request: Request):
    datos = {}
    for sk, sd in SECTORES_TEMUCO.items():
        meta = METADATA_SECTORES.get(sk)
        if meta:
            datos[sk] = {
                "sector": sd,
                "meta": meta,
                "rent": calcular_rentabilidades_sector(sk),
            }
    total_obs_v = sum(v["meta"].n_obs_venta for v in datos.values())
    total_obs_a = sum(v["meta"].n_obs_arriendo for v in datos.values())
    sectores_baja_conf = sum(1 for v in datos.values() if v["meta"].baja_conf_any)
    return templates.TemplateResponse("transparencia.html", {
        "request": request,
        "datos": datos,
        "total_obs_venta": total_obs_v,
        "total_obs_arriendo": total_obs_a,
        "sectores_baja_conf": sectores_baja_conf,
        "ahora": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })


@app.get("/api/sii/{rol}")
async def api_sii_rol(rol: str):
    """
    Consulta datos de una propiedad por Rol SII.
    Primero busca en la nómina local (instantáneo).
    Si no encuentra, intenta scraping del sitio SII (lento, requiere Internet).
    """
    # 1. Búsqueda en nómina local
    resultado = lookup_rol(rol)
    if resultado:
        return JSONResponse(resultado)

    # 2. Fallback: scraping SII web
    try:
        from scrapers.sii_client import consultar_avaluo
        sii_data = await consultar_avaluo(rol)
        if sii_data:
            return JSONResponse({
                "found": True,
                "rol": rol,
                "direccion": None,
                "destino": sii_data.get("destino"),
                "sup_construida_m2": sii_data.get("superficie_construida_m2"),
                "sup_terreno_m2": sii_data.get("superficie_terreno_m2"),
                "av_total_uf": sii_data.get("avaluo_fiscal_uf"),
                "av_total_clp": None,
                "contrib_anual_uf": sii_data.get("contribuciones_anuales_uf"),
                "contrib_anual_clp": None,
                "estado": "Vigente",
                "fuente": "sii_web",
                "fecha_carga": None,
                "uf_carga": None,
            })
    except Exception:
        pass

    return JSONResponse({"found": False, "rol": rol})


@app.get("/api/sii-stats")
async def api_sii_stats():
    """Estado de la nómina SII local."""
    return JSONResponse(estadisticas_nomina())


@app.get("/api/sectores")
async def api_sectores():
    return {
        k: {
            "nombre": v.nombre,
            "clasificacion": v.clasificacion,
            "precio_casa_m2_min": v.precio_casa_uf_m2_min,
            "precio_casa_m2_max": v.precio_casa_uf_m2_max,
            "liquidez": v.liquidez,
            "plusvalia_anual_pct": v.plusvalia_anual_pct,
            "dias_mercado": v.dias_mercado_promedio,
        }
        for k, v in SECTORES_TEMUCO.items()
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
