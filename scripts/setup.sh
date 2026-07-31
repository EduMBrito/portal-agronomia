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
echo "==> Montando a árvore de páginas..."
python manage.py bootstrap_site
echo "==> Criando grupos de permissão..."
python manage.py setup_grupos
echo "==> Criando superusuário..."
python manage.py createsuperuser
echo ""
echo "Pronto! Rode: python manage.py runserver"
echo "Para carregar conteúdo de exemplo: python manage.py populate_content"
