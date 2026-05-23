#!/usr/bin/env bash
set -e
echo "==> Criando ambiente virtual..."
python3 -m venv .venv
source .venv/bin/activate
echo "==> Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "ATENÇÃO: edite o arquivo .env antes de continuar!"
  exit 1
fi
echo "==> Rodando migrações..."
python manage.py migrate
echo "==> Criando superusuário..."
python manage.py createsuperuser
echo "Pronto! Rode: python manage.py runserver"
