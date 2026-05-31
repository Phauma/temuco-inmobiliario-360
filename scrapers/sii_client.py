"""
Cliente para consultas públicas al SII (Servicio de Impuestos Internos).
Consulta de avalúo fiscal y contribuciones por rol de propiedad.
Fuente pública: www4.sii.cl - Consulta de bienes raíces.
"""
from __future__ import annotations

import re
import httpx
from bs4 import BeautifulSoup


SII_BASE = "https://www4.sii.cl/padronesinternetui/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TemucoPropSearch/1.0)",
    "Accept-Language": "es-CL,es;q=0.9",
}


async def consultar_avaluo(rol: str, comuna: str = "TEMUCO") -> dict | None:
    """
    Consulta avalúo fiscal y datos del bien raíz por rol SII.
    Rol formato: '799-12' o '0799-0012'.
    Retorna dict con avalúo, destino, superficie, contribuciones.
    """
    rol_norm = _normalizar_rol(rol)
    if not rol_norm:
        return None

    manzana, predio = rol_norm

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            # Primer paso: obtener token de sesión
            resp_home = await client.get(SII_BASE, headers=HEADERS)
            if resp_home.status_code != 200:
                return None

            # Búsqueda por rol
            data = {
                "RUT_BIE": "",
                "COD_COMUNA": _get_codigo_comuna(comuna),
                "NUM_MANZANA": manzana,
                "NUM_PREDIO": predio,
                "btnBuscarPorRol": "Buscar",
            }
            resp = await client.post(
                SII_BASE + "consultaInformacionBienRaizUI.html",
                data=data,
                headers=HEADERS,
            )
            if resp.status_code != 200:
                return None

            return _parsear_resultado_sii(resp.text, rol)
    except Exception:
        return None


def _parsear_resultado_sii(html: str, rol_original: str) -> dict | None:
    soup = BeautifulSoup(html, "lxml")

    try:
        tablas = soup.find_all("table")
        resultado = {"rol": rol_original}

        for tabla in tablas:
            filas = tabla.find_all("tr")
            for fila in filas:
                celdas = fila.find_all(["td", "th"])
                if len(celdas) < 2:
                    continue
                key = celdas[0].get_text(strip=True).lower()
                val = celdas[1].get_text(strip=True)

                if "avalúo" in key or "avaluo" in key:
                    resultado["avaluo_fiscal_uf"] = _extraer_uf(val)
                elif "destino" in key:
                    resultado["destino"] = val
                elif "superficie" in key and "construida" in key:
                    resultado["superficie_construida_m2"] = _extraer_numero(val)
                elif "superficie" in key and "terreno" in key:
                    resultado["superficie_terreno_m2"] = _extraer_numero(val)
                elif "contribucion" in key or "contribución" in key:
                    resultado["contribuciones_anuales_uf"] = _extraer_uf(val)
                elif "propietario" in key:
                    resultado["propietario"] = val

        return resultado if len(resultado) > 1 else None
    except Exception:
        return None


def _normalizar_rol(rol: str) -> tuple[str, str] | None:
    rol = rol.strip().replace(" ", "")
    if "-" not in rol:
        return None
    partes = rol.split("-")
    if len(partes) != 2:
        return None
    try:
        manzana = str(int(partes[0])).zfill(4)
        predio = str(int(partes[1])).zfill(4)
        return manzana, predio
    except ValueError:
        return None


def _get_codigo_comuna(comuna: str) -> str:
    codigos = {
        "TEMUCO": "094",
        "PADRE LAS CASAS": "096",
        "LAUTARO": "056",
        "VILCUN": "103",
    }
    return codigos.get(comuna.upper(), "094")


def _extraer_uf(texto: str) -> float | None:
    nums = re.findall(r"[\d.,]+", texto.replace("$", "").replace("UF", ""))
    for n in nums:
        try:
            val = float(n.replace(".", "").replace(",", "."))
            if 1 < val < 1_000_000:
                return val
        except ValueError:
            continue
    return None


def _extraer_numero(texto: str) -> float | None:
    nums = re.findall(r"\d+\.?\d*", texto)
    for n in nums:
        try:
            val = float(n)
            if val > 0:
                return val
        except ValueError:
            continue
    return None
