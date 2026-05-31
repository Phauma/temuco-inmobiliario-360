"""
Scraper para Portal Inmobiliario (portalinmobiliario.com).
Uso informativo y educativo. Respetar los términos del portal y robots.txt.
Implementado con rate limiting y sin sobrecarga del servidor.
"""
from __future__ import annotations

import asyncio
import re
import httpx
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml;q=0.9,*/*;q=0.8",
}

TIPO_MAP = {
    "casa": "casa",
    "departamento": "departamento",
    "terreno": "terreno",
    "local_comercial": "local-comercial-y-negocio",
    "oficina": "oficina",
    "bodega": "bodega-y-galpon",
    "mixto": "casa",
}


async def buscar_comparables(
    tipo_propiedad: str,
    sector: str,
    precio_max_uf: float | None = None,
    superficie_min: float | None = None,
    max_resultados: int = 6,
) -> list[dict]:
    """
    Busca publicaciones activas en Portal Inmobiliario para una propiedad tipo/sector.
    Retorna lista de comparables con precio, superficie y URL.
    """
    tipo_url = TIPO_MAP.get(tipo_propiedad, "casa")
    sector_url = _normalizar_sector(sector)

    url = (
        f"https://www.portalinmobiliario.com/venta/{tipo_url}/"
        f"region-de-la-araucania/temuco/{sector_url}"
    )

    params = {}
    if precio_max_uf:
        params["price_to"] = int(precio_max_uf * 1.3)
    if superficie_min and superficie_min > 20:
        params["total_area_from"] = int(superficie_min * 0.5)

    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            await asyncio.sleep(1.5)  # rate limiting cortés
            resp = await client.get(url, headers=HEADERS, params=params)
            if resp.status_code != 200:
                return []
            return _parsear_resultados(resp.text, max_resultados)
    except Exception:
        return []


def _parsear_resultados(html: str, max_resultados: int) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    resultados = []

    cards = soup.select("li.results-item") or soup.select("[data-id]")
    for card in cards[:max_resultados]:
        try:
            titulo = card.select_one("h2.item-title, .poly-component__title")
            precio_el = card.select_one(".price-tag-fraction, .poly-price__current")
            area_el = card.select_one("[data-attribute='TOTAL_AREA'], .poly-attributes-list__item")
            ubicacion_el = card.select_one(".item-subtitle, .poly-component__location")

            precio_uf = _extraer_uf(precio_el.get_text() if precio_el else "")
            superficie = _extraer_numero(area_el.get_text() if area_el else "")

            if not precio_uf:
                continue

            resultados.append({
                "descripcion": titulo.get_text(strip=True) if titulo else "Sin título",
                "precio_uf": round(precio_uf, 1),
                "superficie_m2": superficie,
                "precio_m2": round(precio_uf / superficie, 1) if superficie else None,
                "sector": ubicacion_el.get_text(strip=True) if ubicacion_el else "",
                "dias_publicado": None,
            })
        except Exception:
            continue

    return resultados


def _extraer_uf(texto: str) -> float | None:
    texto = texto.upper()
    if "UF" not in texto:
        return None
    nums = re.findall(r"[\d.,]+", texto)
    for n in nums:
        try:
            val = float(n.replace(".", "").replace(",", "."))
            if 10 < val < 500_000:
                return val
        except ValueError:
            continue
    return None


def _extraer_numero(texto: str) -> float | None:
    nums = re.findall(r"[\d]+\.?[\d]*", texto)
    for n in nums:
        try:
            val = float(n)
            if 5 < val < 50_000:
                return val
        except ValueError:
            continue
    return None


def _normalizar_sector(sector: str) -> str:
    replacements = {
        " ": "-", "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ñ": "n", "ü": "u",
    }
    s = sector.lower().strip()
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s or "temuco"
