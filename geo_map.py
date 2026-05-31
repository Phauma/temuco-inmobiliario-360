"""
Generación de mapas interactivos para propiedades de Temuco.
Usa Folium para crear HTML embebible.
"""
from __future__ import annotations

import folium
from folium.plugins import HeatMap
from market_data import SECTORES_TEMUCO, HEATMAP_SCORES

TEMUCO_CENTER = [-38.7394, -72.5986]
TILE = "CartoDB positron"


def generar_mapa_propiedad(
    lat: float | None,
    lon: float | None,
    sector_key: str | None,
    titulo: str,
    precio_uf: float | None,
    recomendacion: str,
    score_total: int,
) -> str:
    """Genera mapa HTML centrado en la propiedad con marcador y contexto de zona."""
    center = [lat, lon] if lat and lon else TEMUCO_CENTER
    zoom = 15 if lat else 13

    m = folium.Map(location=center, zoom_start=zoom, tiles=TILE)

    # Marcador de la propiedad
    color_rec = {
        "comprar": "green", "negociar": "lightgreen",
        "captar": "blue", "vender": "orange",
        "esperar": "gray", "descartar": "red",
    }.get(recomendacion, "blue")

    if lat and lon:
        popup_html = f"""
        <div style='font-family:Arial; min-width:180px'>
            <b style='font-size:13px'>{titulo}</b><br>
            <hr style='margin:4px 0'>
            {"<b>Precio: " + f"{precio_uf:.0f} UF</b><br>" if precio_uf else ""}
            <b>Score: {score_total}/100</b><br>
            <span style='color:{color_rec};text-transform:capitalize'><b>{recomendacion.upper()}</b></span>
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"📍 {titulo}",
            icon=folium.Icon(color=color_rec, icon="home", prefix="fa"),
        ).add_to(m)

    # Círculos de zonas con color por velocidad de venta
    for sk, sd in SECTORES_TEMUCO.items():
        vel = sd.indice_velocidad_venta
        heat_color = _velocidad_to_color(vel)
        vel_label = "Alta" if vel >= 75 else ("Media" if vel >= 50 else "Baja")

        tooltip_text = (
            f"{sd.nombre} | Velocidad venta: {vel_label} ({vel}/100) | "
            f"Días mercado: ~{sd.dias_mercado_promedio} | "
            f"Plusvalía base: {sd.plusvalia_anual_pct}%/año"
        )

        folium.Circle(
            location=[sd.latitud, sd.longitud],
            radius=sd.radio_km * 1000,
            color=heat_color,
            fill=True,
            fill_color=heat_color,
            fill_opacity=0.22,
            tooltip=tooltip_text,
        ).add_to(m)

        folium.Marker(
            location=[sd.latitud, sd.longitud],
            icon=folium.DivIcon(
                html=(
                    f'<div style="font-size:9px;color:#333;background:rgba(255,255,255,0.85);'
                    f'padding:1px 4px;border-radius:3px;white-space:nowrap;border:1px solid {heat_color}">'
                    f'{sd.nombre}</div>'
                ),
                icon_size=(150, 20),
                icon_anchor=(75, 10),
            ),
        ).add_to(m)

    _add_legend_velocidad(m)
    return m._repr_html_()


def generar_mapa_calor(capa: str = "plusvalia") -> str:
    """Genera mapa de calor de Temuco para una capa específica."""
    m = folium.Map(location=TEMUCO_CENTER, zoom_start=13, tiles=TILE)

    heat_data = []
    for sk, sd in SECTORES_TEMUCO.items():
        score = HEATMAP_SCORES.get(sk, {}).get(capa, 50)
        intensity = score / 100.0
        heat_data.append([sd.latitud, sd.longitud, intensity])

    HeatMap(
        heat_data,
        radius=60,
        blur=40,
        gradient={"0.2": "blue", "0.5": "yellow", "0.8": "orange", "1.0": "red"},
        min_opacity=0.3,
    ).add_to(m)

    titles = {
        "plusvalia": "Mapa de Plusvalía — Temuco",
        "liquidez": "Mapa de Liquidez — Temuco",
        "inversion": "Zonas de Inversión — Temuco",
        "captacion": "Zonas de Captación — Temuco",
    }
    title = titles.get(capa, "Mapa Temuco")

    title_html = f"""
    <div style='position:fixed;top:10px;left:50%;transform:translateX(-50%);
        background:white;padding:8px 16px;border-radius:8px;
        box-shadow:0 2px 8px rgba(0,0,0,0.2);z-index:1000;font-family:Arial'>
        <b>{title}</b>
    </div>"""
    m.get_root().html.add_child(folium.Element(title_html))

    return m._repr_html_()


def _velocidad_to_color(indice: int) -> str:
    """Verde=vende rápido, Amarillo=intermedio, Rojo=lento."""
    if indice >= 80:  return "#16a34a"   # verde intenso
    if indice >= 65:  return "#65a30d"   # verde claro
    if indice >= 50:  return "#ca8a04"   # amarillo
    if indice >= 35:  return "#ea580c"   # naranja
    return "#dc2626"                     # rojo


def _score_to_color(score: int) -> str:
    if score >= 80:   return "#16a34a"
    if score >= 65:   return "#65a30d"
    if score >= 50:   return "#ca8a04"
    if score >= 35:   return "#ea580c"
    return "#dc2626"


def _add_legend_velocidad(m: folium.Map) -> None:
    legend_html = """
    <div style='position:fixed;bottom:30px;right:10px;background:white;
        padding:12px 14px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.2);
        font-family:Arial;font-size:11px;z-index:1000;min-width:170px'>
        <b>Velocidad de venta</b><br>
        <span style='font-size:9px;color:#666'>(días en mercado por zona)</span><br><br>
        <span style='color:#16a34a;font-size:14px'>●</span> <b>Alta</b> — vende en &lt;45 días<br>
        <span style='color:#65a30d;font-size:14px'>●</span> <b>Buena</b> — 45-60 días<br>
        <span style='color:#ca8a04;font-size:14px'>●</span> <b>Media</b> — 60-80 días<br>
        <span style='color:#ea580c;font-size:14px'>●</span> <b>Lenta</b> — 80-110 días<br>
        <span style='color:#dc2626;font-size:14px'>●</span> <b>Muy lenta</b> — &gt;110 días<br><br>
        <span style='font-size:9px;color:#888'>Pasa el cursor sobre cada zona<br>para ver detalle</span>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))
