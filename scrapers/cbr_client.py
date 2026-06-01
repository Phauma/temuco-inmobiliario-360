"""
Cliente scraper — Conservador de Bienes Raíces de Temuco (Primer CBR).
Fuente pública: cbrtemuco.cl/WebCBRT/webCBRT/busqueda

Lo que el índice público entrega:
  ✓ Fojas / Número / Año de cada inscripción
  ✓ Tipo de acto (COMPRAVENTA, HERENCIA, ADJUDICACION, HIPOTECA, …)
  ✓ Nombre del titular inscrito
  ✓ Descripción del inmueble (dirección/loteo)
  ✗ Precio de cierre — NO está en el índice; requiere copia pagada de la escritura

Flujo:
  1. Buscar por apellido del titular → lista de inscripciones
  2. Ordenar por año desc, filtrar COMPRAVENTA más reciente
  3. Obtener detalle → dirección e historial de cancelaciones
"""
from __future__ import annotations

import re
import asyncio
from datetime import datetime

import httpx
from bs4 import BeautifulSoup


CBR_BASE = "https://www.cbrtemuco.cl/WebCBRT/webCBRT"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9",
    "Referer": f"{CBR_BASE}/busqueda",
}

# Tipos de acto que corresponden a transferencia de dominio
TIPOS_TRANSFERENCIA = {
    "COMPRAVENTA", "HERENCIA", "ADJUDICACION", "DONACION",
    "PERMUTA", "DACION EN PAGO", "APORTE", "REMATE",
}


async def buscar_transferencias(
    apellido_paterno: str,
    nombres: str = "",
    apellido_materno: str = "",
    max_resultados: int = 20,
) -> dict:
    """
    Busca inscripciones de propiedad en el CBR de Temuco para un titular.

    Retorna dict con:
      inscripciones: lista ordenada por año desc (todas)
      ultima_compraventa: la más reciente con tipo COMPRAVENTA
      advertencia: nota sobre limitación de datos
    """
    apellido_paterno = apellido_paterno.strip().upper()
    nombres = nombres.strip().upper()
    apellido_materno = apellido_materno.strip().upper()

    if not apellido_paterno:
        return {"error": "Apellido paterno requerido.", "inscripciones": []}

    try:
        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            # Establecer sesión
            await client.get(f"{CBR_BASE}/busqueda")

            # Búsqueda por nombre
            resp = await client.post(
                f"{CBR_BASE}/buscarTituloApellido",
                data={
                    "formnombres":         nombres,
                    "formapellidoPaterno": apellido_paterno,
                    "formapellidoMaterno": apellido_materno,
                },
            )
            if resp.status_code != 200:
                return {"error": f"CBR respondió {resp.status_code}.", "inscripciones": []}

            inscripciones, form_ids = _parsear_lista(resp.text)

            if not inscripciones:
                return {
                    "encontrado": False,
                    "inscripciones": [],
                    "mensaje": f"Sin inscripciones para '{apellido_paterno} {nombres}' en CBR Temuco.",
                    "advertencia": _advertencia_precio(),
                }

            # Ordenar por año desc, limitar
            inscripciones.sort(key=lambda x: x["año"], reverse=True)
            inscripciones = inscripciones[:max_resultados]

            # Obtener detalle de la compraventa más reciente
            ultima_cv = next(
                (i for i in inscripciones if i["tipo"] in TIPOS_TRANSFERENCIA),
                None,
            )
            detalle = None
            if ultima_cv and ultima_cv.get("titulo_id"):
                detalle = await _obtener_detalle(client, ultima_cv["titulo_id"])
                if detalle:
                    ultima_cv.update(detalle)

            return {
                "encontrado": True,
                "inscripciones": inscripciones,
                "ultima_compraventa": ultima_cv,
                "total_inscripciones": len(inscripciones),
                "advertencia": _advertencia_precio(),
                "fuente": "CBR Temuco — Primer Conservador",
                "fecha_consulta": datetime.now().strftime("%d/%m/%Y %H:%M"),
            }

    except httpx.TimeoutException:
        return {"error": "Tiempo de espera agotado consultando CBR.", "inscripciones": []}
    except Exception as e:
        return {"error": f"Error al consultar CBR: {e}", "inscripciones": []}


def _parsear_lista(html: str) -> tuple[list[dict], list[str]]:
    """Parsea la tabla de resultados del CBR."""
    soup = BeautifulSoup(html, "lxml")
    inscripciones = []
    form_ids = []

    tabla = soup.find("table")
    if not tabla:
        return [], []

    filas = tabla.find_all("tr")[1:]  # saltar encabezado
    for fila in filas:
        celdas = fila.find_all("td")
        if len(celdas) < 5:
            continue
        try:
            fojas  = celdas[0].get_text(strip=True)
            nro    = celdas[1].get_text(strip=True)
            año    = int(celdas[2].get_text(strip=True))
            nombre = celdas[3].get_text(strip=True)
            tipo   = celdas[4].get_text(strip=True).upper()

            # Extraer titulo_id del formulario de detalle
            form = fila.find("form")
            titulo_id = None
            if form:
                inp = form.find("input", {"name": "titulosId"})
                if inp:
                    titulo_id = inp.get("value")
                    form_ids.append(titulo_id)

            inscripciones.append({
                "fojas":      fojas,
                "numero":     nro,
                "año":        año,
                "nombre":     nombre,
                "tipo":       tipo,
                "titulo_id":  titulo_id,
                "es_transferencia": tipo in TIPOS_TRANSFERENCIA,
            })
        except (ValueError, IndexError):
            continue

    return inscripciones, form_ids


async def _obtener_detalle(client: httpx.AsyncClient, titulo_id: str) -> dict | None:
    """Obtiene el detalle de una inscripción: dirección y estado de vigencia."""
    try:
        resp = await client.post(
            f"{CBR_BASE}/tituloDetallesPorNombre",
            data={"titulosId": titulo_id},
        )
        if resp.status_code != 200:
            return None
        return _parsear_detalle(resp.text)
    except Exception:
        return None


def _parsear_detalle(html: str) -> dict:
    """Extrae dirección y estado de vigencia del detalle de inscripción."""
    soup = BeautifulSoup(html, "lxml")
    resultado = {}

    # Buscar descripción del inmueble (dirección/loteo)
    texto_completo = soup.get_text(separator=" ", strip=True)

    # Patrones de dirección comunes en CBR Temuco
    patrones_dir = [
        r"(SITIO\s+[\w\s,\.]+?TEMUCO[\w\s,\.]*?)(?:\s{2,}|\.|Fojas)",
        r"(LOTE\s+[\w\s,\.]+?TEMUCO[\w\s,\.]*?)(?:\s{2,}|\.|Fojas)",
        r"(CALLE\s+[\w\s,\.]+?TEMUCO[\w\s,\.]*?)(?:\s{2,}|\.|Fojas)",
        r"(PREDIO\s+[\w\s,\.]+?TEMUCO[\w\s,\.]*?)(?:\s{2,}|\.|Fojas)",
        r"(PARCELA\s+[\w\s,\.]+?)(?:\s{2,}|\.|Fojas)",
    ]
    for pat in patrones_dir:
        m = re.search(pat, texto_completo, re.IGNORECASE)
        if m:
            resultado["descripcion_inmueble"] = m.group(1).strip()[:250]
            break

    # Buscar en párrafos específicos
    for p in soup.find_all(["p", "div", "td"]):
        t = p.get_text(strip=True)
        if ("SITIO" in t or "CALLE" in t or "LOTE" in t or "PREDIO" in t) and "TEMUCO" in t and len(t) < 300:
            resultado["descripcion_inmueble"] = t[:250]
            break

    # Estado de vigencia (cancelado por otro título / vigente)
    if "Ninguno" in texto_completo and "posible que este título se encuentre vigente" in texto_completo:
        resultado["vigencia"] = "Posiblemente vigente"
    elif "cancelan a esta inscripción" in texto_completo:
        resultado["vigencia"] = "Cancelada por inscripción posterior"
    else:
        resultado["vigencia"] = "Sin información de vigencia"

    return resultado


def _advertencia_precio() -> str:
    return (
        "El índice público del CBR no incluye el precio de cierre. "
        "Para obtener el precio declarado en escritura, solicitar 'Copia de Inscripción' "
        "directamente en el CBR de Temuco (Vicuña Mackenna 361) o en cbrtemuco.cl."
    )


# ── Función de conveniencia para uso síncrono ─────────────────────────────────

def buscar_transferencias_sync(
    apellido_paterno: str,
    nombres: str = "",
    apellido_materno: str = "",
) -> dict:
    """Versión síncrona para scripts."""
    return asyncio.run(buscar_transferencias(apellido_paterno, nombres, apellido_materno))
