# Portal de Produção Acadêmica — Agronomia IFSertãoPE

Construído com **Django 5.1** + **Wagtail 6.3**.

## Estrutura

```
portal-agronomia/
├── apps/
│   ├── base/           # blocks, choices, mixins reutilizáveis
│   ├── core/           # HomePage
│   ├── pessoas/        # DocentePage + AreaConhecimento
│   ├── ensino/         # DisciplinaPage + MaterialDisciplina
│   ├── pesquisa/       # ProjetoPage + PublicacaoPage
│   ├── noticias/       # PostPage
│   └── institucional/  # DocumentoPage + EventoPage
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── templates/
├── static/
└── docs/
```

## Instalação rápida

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edite com suas configurações
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse o admin Wagtail em: http://localhost:8000/admin
