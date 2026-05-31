#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ ! -f ".env" ]; then
  echo "⚠️  Archivo .env no encontrado. Copiando desde .env.example..."
  cp .env.example .env
  echo "✏️  Edita el archivo .env y agrega tu ANTHROPIC_API_KEY antes de continuar."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "📦 Creando entorno virtual..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "📥 Instalando dependencias..."
pip install -q -r requirements.txt

echo "🚀 Iniciando Temuco Inmobiliario 360 en http://localhost:8000"
python app.py
