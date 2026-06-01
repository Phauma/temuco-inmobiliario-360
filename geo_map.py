"""
Mapas interactivos de Temuco con 8 capas de análisis inmobiliario.
Polígonos georreferenciados, heatmap por indicador, leyenda y filtros por capa.
"""
from __future__ import annotations

import math
import random
import folium
from folium.plugins import Fullscreen
from market_data import SECTORES_TEMUCO, SectorData

TEMUCO_CENTER = [-38.7394, -72.5986]
TILE = "CartoDB positron"

# ─── Helpers de geometría ─────────────────────────────────────────────────────

def _polygon_points(lat: float, lon: float, radius_km: float, n: int, seed: int) -> list:
    """Genera polígono irregular alrededor del centro del sector."""
    random.seed(seed)
    lat_per_km = 1 / 111.0
    lon_per_km = 1 / (111.0 * math.cos(math.radians(lat)))
    pts = []
    for i in range(n):
        angle = 2 * math.pi * i / n + random.uniform(-0.25, 0.25)
        r = radius_km * random.uniform(0.60, 1.40)
        pts.append([lat + r * lat_per_km * math.cos(angle),
                    lon + r * lon_per_km * math.sin(angle)])
    pts.append(pts[0])
    return pts


def _geojson_feature(lat: float, lon: float, props: dict,
                     radius: float = 0.9, seed: int = 0) -> dict:
    pts = _polygon_points(lat, lon, radius, 9, seed)
    return {
        "type": "Feature",
        "properties": props,
        "geometry": {"type": "Polygon",
                     "coordinates": [[[p[1], p[0]] for p in pts]]},
    }


# ─── Escala de color: rojo → amarillo → verde ─────────────────────────────────

def _val_to_color(val: float, lo: float, hi: float, invert: bool) -> str:
    """invert=True → alto valor es VERDE (oportunidad); False → alto es ROJO."""
    t = (val - lo) / (hi - lo) if hi != lo else 0.5
    t = max(0.0, min(1.0, t))
    if invert:
        t = 1.0 - t
    # rojo(220,38,38) → amarillo(202,138,4) → verde(22,163,74)
    if t < 0.5:
        f = t * 2
        r, g, b = (int(220+(202-220)*f), int(38+(138-38)*f), int(38+(4-38)*f))
    else:
        f = (t - 0.5) * 2
        r, g, b = (int(202+(22-202)*f), int(138+(163-138)*f), int(4+(74-4)*f))
    return f"#{r:02x}{g:02x}{b:02x}"


# ─── Estimadores por sector ───────────────────────────────────────────────────

def _cap_rate(s: SectorData) -> float:
    precio_m2 = (s.precio_casa_uf_m2_min + s.precio_casa_uf_m2_max) / 2
    precio    = precio_m2 * 100                         # referencia 100 m²
    arr_anual = s.arriendo_casa_uf_mes_ref * 12
    vacancia  = {"alta": 0.05, "media": 0.09, "baja": 0.15}.get(s.demanda_arriendo, 0.09)
    contrib   = precio * 0.006                          # contribuciones ~0.6 % valor comercial/año
    gastos_op = arr_anual * 0.10                        # admin + mantención: 10 % arriendo anual
    noi       = arr_anual * (1 - vacancia) - contrib - gastos_op
    return round(max(noi / precio * 100, 1.0), 1)


def _transacciones_anuales(s: SectorData) -> int:
    stock = {"premium": 150, "alto": 250, "medio_alto": 450,
             "medio": 700, "medio_bajo": 500, "bajo": 300}.get(s.clasificacion, 400)
    return max(5, int(stock * 0.12 * (365 / s.dias_mercado_promedio)))


def _oferta_activa(s: SectorData) -> int:
    stock = {"premium": 150, "alto": 250, "medio_alto": 450,
             "medio": 700, "medio_bajo": 500, "bajo": 300}.get(s.clasificacion, 400)
    rate = {"alta": 0.08, "media": 0.18, "baja": 0.30, "muy_baja": 0.45}.get(s.liquidez, 0.20)
    return max(3, int(stock * rate))


def _riesgo_sobreoferta(s: SectorData) -> int:
    base = s.dias_mercado_promedio / 130 * 70
    adj = {"muy_baja": 30, "baja": 15, "media": 0, "alta": -20}.get(s.liquidez, 0)
    return max(0, min(100, int(base + adj)))


# ─── Definición de las 8 capas ───────────────────────────────────────────────

CAPAS: dict[str, dict] = {
    "precio_m2": {
        "titulo": "Precio UF/m²",
        "descripcion": "Precio promedio de venta/m² construido (casas)",
        "unidad": "UF/m²",
        "fn": lambda s: round((s.precio_casa_uf_m2_min + s.precio_casa_uf_m2_max) / 2, 1),
        "invert": False,
        "low_label": "Precio bajo → Oportunidad",
        "high_label": "Precio alto → Sobrevalorado",
    },
    "arriendo_mes": {
        "titulo": "Arriendo UF/mes",
        "descripcion": "Arriendo mensual estimado para casa 100 m²",
        "unidad": "UF/mes",
        "fn": lambda s: s.arriendo_casa_uf_mes_ref,
        "invert": True,
        "low_label": "Arriendo bajo",
        "high_label": "Arriendo alto → Mayor retorno",
    },
    "cap_rate": {
        "titulo": "Cap Rate Neto",
        "descripcion": "Rentabilidad neta estimada por arriendo",
        "unidad": "%",
        "fn": _cap_rate,
        "invert": True,
        "low_label": "Baja rentabilidad",
        "high_label": "Alta rentabilidad → Oportunidad",
    },
    "velocidad_venta": {
        "titulo": "Velocidad de Venta",
        "descripcion": "Índice 0-100 de rapidez de venta del sector",
        "unidad": "/100",
        "fn": lambda s: s.indice_velocidad_venta,
        "invert": True,
        "low_label": "Mercado lento",
        "high_label": "Mercado activo → Fácil de vender",
    },
    "plusvalia_5a": {
        "titulo": "Plusvalía 5 Años",
        "descripcion": "Apreciación acumulada estimada base (5 años)",
        "unidad": "%",
        "fn": lambda s: round(s.plusvalia_anual_pct * 5, 1),
        "invert": True,
        "low_label": "Baja plusvalía",
        "high_label": "Alta plusvalía → Inversión a largo plazo",
    },
    "transacciones": {
        "titulo": "Transacciones / Año",
        "descripcion": "Estimación de operaciones anuales en el sector",
        "unidad": "ops/año",
        "fn": _transacciones_anuales,
        "invert": True,
        "low_label": "Mercado inactivo",
        "high_label": "Alta rotación → Mercado dinámico",
    },
    "oferta_activa": {
        "titulo": "Oferta Activa",
        "descripcion": "Propiedades actualmente en venta (estimado)",
        "unidad": "prop.",
        "fn": _oferta_activa,
        "invert": False,
        "low_label": "Escasa oferta → Presión al alza",
        "high_label": "Alta oferta → Presión a la baja",
    },
    "riesgo_sobreoferta": {
        "titulo": "Riesgo de Sobreoferta",
        "descripcion": "Riesgo de caída de precios por exceso de oferta",
        "unidad": "/100",
        "fn": _riesgo_sobreoferta,
        "invert": False,
        "low_label": "Bajo riesgo → Seguro",
        "high_label": "Alto riesgo → Precaución",
    },
}


# ─── Tooltip HTML por sector ──────────────────────────────────────────────────

def _tooltip(s: SectorData, sk: str, capa_key: str, val: float, capa: dict) -> str:
    cap = _cap_rate(s)
    trans = _transacciones_anuales(s)
    oferta = _oferta_activa(s)
    riesgo = _riesgo_sobreoferta(s)
    precio_m2 = round((s.precio_casa_uf_m2_min + s.precio_casa_uf_m2_max) / 2, 1)

    badge_color = {"alto": "#16a34a", "medio_alto": "#65a30d", "medio": "#ca8a04",
                   "medio_bajo": "#ea580c", "bajo": "#dc2626"}.get(s.clasificacion, "#6b7280")

    return f"""
    <div style='font-family:Arial;font-size:12px;min-width:220px;max-width:260px'>
      <div style='font-size:14px;font-weight:bold;color:#1e293b;margin-bottom:4px'>{s.nombre}</div>
      <span style='background:{badge_color};color:white;padding:1px 7px;border-radius:10px;
        font-size:10px;font-weight:bold'>{s.clasificacion.replace("_"," ").upper()}</span>
      <hr style='margin:6px 0;border-color:#e2e8f0'>
      <table style='width:100%;border-collapse:collapse'>
        <tr><td style='color:#64748b;padding:1px 0'>Precio/m²</td>
            <td style='text-align:right;font-weight:600'>{precio_m2} UF/m²</td></tr>
        <tr><td style='color:#64748b;padding:1px 0'>Arriendo ref.</td>
            <td style='text-align:right;font-weight:600'>{s.arriendo_casa_uf_mes_ref} UF/mes</td></tr>
        <tr><td style='color:#64748b;padding:1px 0'>Cap rate neto</td>
            <td style='text-align:right;font-weight:600'>{cap}%</td></tr>
        <tr><td style='color:#64748b;padding:1px 0'>Días en mercado</td>
            <td style='text-align:right;font-weight:600'>{s.dias_mercado_promedio} días</td></tr>
        <tr><td style='color:#64748b;padding:1px 0'>Velocidad venta</td>
            <td style='text-align:right;font-weight:600'>{s.indice_velocidad_venta}/100</td></tr>
        <tr><td style='color:#64748b;padding:1px 0'>Plusvalía base/año</td>
            <td style='text-align:right;font-weight:600'>{s.plusvalia_anual_pct}%</td></tr>
        <tr><td style='color:#64748b;padding:1px 0'>Transacciones/año</td>
            <td style='text-align:right;font-weight:600'>~{trans}</td></tr>
        <tr><td style='color:#64748b;padding:1px 0'>Oferta activa</td>
            <td style='text-align:right;font-weight:600'>~{oferta} prop.</td></tr>
        <tr><td style='color:#64748b;padding:1px 0'>Riesgo sobreoferta</td>
            <td style='text-align:right;font-weight:600'>{riesgo}/100</td></tr>
      </table>
      <hr style='margin:6px 0;border-color:#e2e8f0'>
      <div style='font-size:11px;color:#475569'>
        <b>Capa activa — {capa["titulo"]}:</b>
        <span style='font-size:13px;font-weight:bold;color:#1e293b'> {val} {capa["unidad"]}</span>
      </div>
    </div>"""


# ─── Generador principal: mapa multicapa ─────────────────────────────────────

def generar_mapa_calor(capa_activa: str = "velocidad_venta") -> str:
    if capa_activa not in CAPAS:
        capa_activa = "velocidad_venta"

    m = folium.Map(location=TEMUCO_CENTER, zoom_start=13, tiles=TILE)
    Fullscreen(position="topleft").add_to(m)

    for capa_key, capa in CAPAS.items():
        valores = {sk: capa["fn"](sd) for sk, sd in SECTORES_TEMUCO.items()}
        lo, hi = min(valores.values()), max(valores.values())
        mostrar = (capa_key == capa_activa)

        fg = folium.FeatureGroup(name=f"{'● ' if mostrar else ''}{capa['titulo']}",
                                 show=mostrar)

        for i, (sk, sd) in enumerate(SECTORES_TEMUCO.items()):
            val = valores[sk]
            fill = _val_to_color(val, lo, hi, capa["invert"])
            tip = _tooltip(sd, sk, capa_key, val, capa)

            folium.GeoJson(
                _geojson_feature(sd.latitud, sd.longitud, {}, sd.radio_km, seed=i * 11 + 7),
                style_function=lambda x, f=fill: {
                    "fillColor": f, "color": "#ffffff",
                    "weight": 1.5, "fillOpacity": 0.68,
                },
                highlight_function=lambda x: {
                    "weight": 3, "color": "#1e293b", "fillOpacity": 0.88,
                },
                tooltip=folium.Tooltip(tip, sticky=True),
            ).add_to(fg)

            folium.Marker(
                location=[sd.latitud, sd.longitud],
                icon=folium.DivIcon(
                    html=(f'<div style="font-size:9px;font-weight:bold;color:#1e293b;'
                          f'background:rgba(255,255,255,0.88);padding:1px 5px;'
                          f'border-radius:4px;white-space:nowrap;'
                          f'border:1px solid {fill}">{sd.nombre}</div>'),
                    icon_size=(160, 18), icon_anchor=(80, 9),
                ),
            ).add_to(fg)

        fg.add_to(m)

    folium.LayerControl(collapsed=False, position="topright").add_to(m)
    _add_leyenda(m, CAPAS[capa_activa])
    return m._repr_html_()


# ─── Mapa de propiedad individual ─────────────────────────────────────────────

def generar_mapa_propiedad(
    lat: float | None, lon: float | None, sector_key: str | None,
    titulo: str, precio_uf: float | None, recomendacion: str, score_total: int,
) -> str:
    m = folium.Map(location=[lat, lon] if lat else TEMUCO_CENTER,
                   zoom_start=15 if lat else 13, tiles=TILE)

    # Polígonos de fondo con velocidad de venta
    capa = CAPAS["velocidad_venta"]
    valores = {sk: capa["fn"](sd) for sk, sd in SECTORES_TEMUCO.items()}
    lo, hi = min(valores.values()), max(valores.values())

    for i, (sk, sd) in enumerate(SECTORES_TEMUCO.items()):
        val = valores[sk]
        fill = _val_to_color(val, lo, hi, capa["invert"])
        tip = _tooltip(sd, sk, "velocidad_venta", val, capa)
        folium.GeoJson(
            _geojson_feature(sd.latitud, sd.longitud, {}, sd.radio_km, seed=i * 11 + 7),
            style_function=lambda x, f=fill: {
                "fillColor": f, "color": "#ffffff", "weight": 1, "fillOpacity": 0.45,
            },
            tooltip=folium.Tooltip(tip, sticky=True),
        ).add_to(m)
        folium.Marker(
            location=[sd.latitud, sd.longitud],
            icon=folium.DivIcon(
                html=(f'<div style="font-size:8px;color:#475569;background:rgba(255,255,255,0.8);'
                      f'padding:1px 3px;border-radius:3px;white-space:nowrap">{sd.nombre}</div>'),
                icon_size=(150, 16), icon_anchor=(75, 8),
            ),
        ).add_to(m)

    # Marcador de la propiedad
    color_rec = {"comprar": "green", "negociar": "lightgreen", "captar": "blue",
                 "vender": "orange", "esperar": "gray", "descartar": "red"}.get(recomendacion, "blue")
    if lat and lon:
        popup_html = (f"<div style='font-family:Arial;min-width:180px'>"
                      f"<b>{titulo}</b><br><hr style='margin:4px 0'>"
                      f"{'<b>Precio: ' + f'{precio_uf:.0f} UF</b><br>' if precio_uf else ''}"
                      f"<b>Score: {score_total}/100</b><br>"
                      f"<span style='color:{color_rec};text-transform:capitalize'>"
                      f"<b>{recomendacion.upper()}</b></span></div>")
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"📍 {titulo}",
            icon=folium.Icon(color=color_rec, icon="home", prefix="fa"),
        ).add_to(m)

    _add_leyenda(m, capa, titulo="Velocidad de venta por zona")
    return m._repr_html_()


# ─── Leyenda ──────────────────────────────────────────────────────────────────

def _add_leyenda(m: folium.Map, capa: dict, titulo: str | None = None) -> None:
    t = titulo or capa["titulo"]
    html = f"""
    <div style='position:fixed;bottom:24px;left:10px;background:white;
        padding:12px 16px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.18);
        font-family:Arial;font-size:11px;z-index:1000;min-width:190px'>
      <b style='font-size:12px'>{t}</b><br>
      <span style='font-size:10px;color:#64748b'>{capa['descripcion']}</span>
      <div style='margin-top:8px'>
        <div style='height:14px;width:160px;border-radius:4px;
          background:linear-gradient(to right,#16a34a,#ca8a04,#dc2626);
          {"" if capa["invert"] else "transform:scaleX(-1)"}'>
        </div>
        <div style='display:flex;justify-content:space-between;font-size:9px;color:#475569;margin-top:2px'>
          <span>{"Oportunidad" if capa["invert"] else "Bajo / Seguro"}</span>
          <span>Valor justo</span>
          <span>{"Sobrevalorado" if not capa["invert"] else "Riesgo / Caro"}</span>
        </div>
      </div>
      <div style='margin-top:6px;font-size:10px;color:#64748b'>
        <span style='color:#16a34a'>■</span> {capa["low_label"] if capa["invert"] else capa["high_label"]}<br>
        <span style='color:#ca8a04'>■</span> Valor intermedio<br>
        <span style='color:#dc2626'>■</span> {capa["high_label"] if capa["invert"] else capa["low_label"]}
      </div>
      <div style='margin-top:6px;font-size:9px;color:#94a3b8'>Pasa el cursor sobre cada zona</div>
    </div>"""
    m.get_root().html.add_child(folium.Element(html))
