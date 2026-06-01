#!/usr/bin/env python3
"""
Script para cargar la nómina de bienes raíces SII en la base de datos local.

CÓMO OBTENER EL ARCHIVO CSV:
────────────────────────────
1. Ir a: https://www.sii.cl/servicios_online/1047-.html
   (SII → Servicios Online → Catastro de Bienes Raíces → Consulta por Rol)

2. Para descarga masiva de la nómina comunal:
   - Ir a: https://www.sii.cl/sobre_el_sii/nominasbienes.html
   - O buscar: "SII nómina bienes raíces por comuna"
   - Seleccionar Región IX (La Araucanía) → Comuna Temuco (09101)
   - Descargar el archivo (CSV o Excel)

3. También disponible vía:
   - datos.gob.cl (portal de datos abiertos del Estado)
   - Buscar: "catastro bienes raíces SII Temuco"

FORMATO ESPERADO DEL CSV:
─────────────────────────
El script detecta automáticamente las columnas. Formatos soportados:
  ROL_MANZANA;ROL_PREDIO;CALLE;NUMERO;DESTINO;SUP_CONSTR;SUP_TERRENO;AV_TOTAL;AV_AFECTO;AV_EXENTO;CONTRIB_ANUAL;ESTADO
  manzana;predio;direccion;destino;sup_construida;av_total;contrib_anual;estado

USO:
────
  python scripts/cargar_nomina.py archivo.csv
  python scripts/cargar_nomina.py archivo.csv --uf 38500
  python scripts/cargar_nomina.py archivo.csv --uf 38500 --delimitador ","
  python scripts/cargar_nomina.py --stats
"""
from __future__ import annotations

import argparse
import sys
import os

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sii_nomina import cargar_csv, estadisticas_nomina, lookup_rol


def cmd_cargar(args):
    print(f"\n{'='*55}")
    print(f"  Cargador Nómina SII — Temuco Inmobiliario 360")
    print(f"{'='*55}")
    print(f"  Archivo:      {args.archivo}")
    print(f"  Valor UF:    ${args.uf:,.0f} CLP")
    print(f"  Delimitador: '{args.delimitador}'")
    print(f"  Encoding:     {args.encoding}")
    print()

    try:
        stats = cargar_csv(
            ruta=args.archivo,
            uf_valor=args.uf,
            delimitador=args.delimitador,
            encoding=args.encoding,
            verbose=True,
        )
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n✗ Error de formato: {e}")
        print("\nConsejo: Verificar delimitador con --delimitador ',' si el archivo usa comas.")
        sys.exit(1)

    print(f"\n{'='*55}")
    print("  Verificación rápida — primeros 3 Roles cargados:")
    print(f"{'='*55}")
    _mostrar_muestra()


def cmd_stats(args):
    stats = estadisticas_nomina()
    if not stats["cargada"]:
        print("\n⚠  Nómina no cargada. Ejecutar primero:")
        print("   python scripts/cargar_nomina.py <archivo.csv>")
        return

    print(f"\n{'='*55}")
    print(f"  Estadísticas Nómina SII — Temuco Inmobiliario 360")
    print(f"{'='*55}")
    print(f"  Total propiedades:  {stats['total']:,}")
    print(f"  Vigentes:           {stats['vigentes']:,}")
    print(f"  Última carga:       {stats['ultima_carga']}")
    print(f"  Fuente:             {stats['fuente_archivo']}")
    print(f"  UF al cargar:      ${stats['uf_carga']:,.0f}" if stats['uf_carga'] else "")
    print(f"\n  Por destino:")
    for destino, cnt in sorted(stats["por_destino"].items(), key=lambda x: -x[1]):
        print(f"    {destino:<30} {cnt:>7,}")


def cmd_buscar(args):
    result = lookup_rol(args.rol)
    if result:
        print(f"\n  Rol {args.rol} encontrado:")
        for k, v in result.items():
            if v is not None and k != "found":
                print(f"    {k:<25} {v}")
    else:
        print(f"\n  Rol '{args.rol}' no encontrado en la nómina local.")
        print("  Si el Rol existe en el SII, puede que la nómina no esté cargada.")


def _mostrar_muestra():
    from sii_nomina import get_engine, PropiedadSII
    from sqlalchemy.orm import Session
    engine = get_engine()
    with Session(engine) as s:
        props = s.query(PropiedadSII).limit(3).all()
        for p in props:
            print(f"  {p.rol} | {p.destino or '?'} | {p.sup_construida or '?'} m² | "
                  f"{p.av_total_uf or '?'} UF | {p.direccion or '?'}")


def main():
    parser = argparse.ArgumentParser(
        description="Cargador de Nómina SII para Temuco Inmobiliario 360",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd")

    # Subcomando: cargar
    p_load = sub.add_parser("cargar", help="Importar CSV de la nómina SII")
    p_load.add_argument("archivo", help="Ruta al archivo CSV descargado del SII")
    p_load.add_argument("--uf", type=float, default=38_000.0,
                        help="Valor UF en CLP para conversión (default: 38000)")
    p_load.add_argument("--delimitador", default=";",
                        help="Separador de columnas (default: ';')")
    p_load.add_argument("--encoding", default="latin-1",
                        help="Encoding del archivo (default: latin-1)")

    # Subcomando: stats
    sub.add_parser("stats", help="Mostrar estadísticas de la nómina cargada")

    # Subcomando: buscar
    p_buscar = sub.add_parser("buscar", help="Buscar un Rol SII en la nómina local")
    p_buscar.add_argument("rol", help="Rol SII a buscar (ej: 799-12)")

    # Argumento posicional directo (atajo: python cargar_nomina.py archivo.csv)
    parser.add_argument("archivo_directo", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("--uf", type=float, default=38_000.0)
    parser.add_argument("--delimitador", default=";")
    parser.add_argument("--encoding", default="latin-1")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    parser.add_argument("--buscar", metavar="ROL", help="Buscar un Rol específico")

    args = parser.parse_args()

    # Despacho
    if args.cmd == "cargar":
        cmd_cargar(args)
    elif args.cmd == "stats":
        cmd_stats(args)
    elif args.cmd == "buscar":
        cmd_buscar(args)
    elif getattr(args, "stats", False):
        cmd_stats(args)
    elif getattr(args, "buscar", None):
        args.rol = args.buscar
        cmd_buscar(args)
    elif getattr(args, "archivo_directo", None):
        args.archivo = args.archivo_directo
        cmd_cargar(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
