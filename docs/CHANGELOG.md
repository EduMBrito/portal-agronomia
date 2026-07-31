# CHANGELOG — Portal Agronomia IFSertãoPE

Formato: [vX.Y.Z] - YYYY-MM-DD  
Seções: Added, Changed, Fixed, Removed

---

## [Unreleased]

### Added
- Management command `bootstrap_site` — cria a HomePage, aponta o Site do Wagtail para ela, remove a página padrão "Welcome to your new Wagtail site!" e cria as sete IndexPages com os slugs esperados pelo menu. Idempotente
- Busca textual em todo o portal (`/busca/`) usando o backend nativo do Wagtail
- Suíte de testes com pytest + pytest-django (30 testes: core, ensino, institucional, pessoas)
- `config/settings/production.py` — HTTPS, HSTS, cookies seguros, `ManifestStaticFilesStorage`, logging para stdout
- `docker-compose.prod.yml`, `docs/nginx.conf` e `docs/gunicorn.service`
- Management command `populate_content` — carga de conteúdo de exemplo para demonstração
- Página "Sobre o LADI" (`/sobre/`) e logo no rodapé
- Pasta `docs/` com ARCHITECTURE.md, API.md, DATABASE.md, DEPLOY.md, CONTRIBUTING.md, CHANGELOG.md

### Changed
- Sequência de instalação no README.md, `docs/DEPLOY.md`, `docs/CONTRIBUTING.md` e `scripts/setup.sh` — inclui `bootstrap_site` entre `migrate` e `createsuperuser`

---

## [0.3.0] - 2026-05-23

### Added
- Dashboard admin personalizado com três painéis: BemVindoPanel, ResumoConteudoPanel, AcoesRapidasPanel
- Branding institucional no Wagtail admin (paleta verde/azul IFSertãoPE via CSS custom properties)
- Management command `setup_grupos` — cria grupos Coordenador, Docente e Técnico com permissões Wagtail 6
- Suporte ao padrão de permissões do Wagtail 6 (`GroupPagePermission` com FK para `Permission`)

### Fixed
- URLs de adição rápida no `AcoesRapidasPanel` — usavam `model_name` do IndexPage em vez do tipo filho, gerando 302 silencioso
- Comparação de datas em `eventos_index_page.html` — substituído `{% with %}` inválido por `context["now"]` passado pelo model
- Posicionamento das URLs do debug_toolbar antes do catchall do Wagtail em `config/urls.py`

---

## [0.2.0] - 2026-05-22

### Added
- Todos os 23 templates HTML (base.html, includes, 7 módulos completos)
- Integração do Tailwind CSS Play CDN com config da paleta institucional
- HTMX 2.0.3 via CDN
- Paginação em todas as IndexPages
- Filtros por área, período, tipo e status nas listagens
- Contexto com `now` em EventosIndexPage para distinguir eventos passados/futuros

### Changed
- `dockerignore` renomeado para `.dockerignore` (Docker ignorava o arquivo sem o ponto)

---

## [0.1.0] - 2026-05-20

### Added
- Estrutura inicial do projeto Django 5.1 + Wagtail 6.3
- Docker Compose com PostgreSQL 16 (porta 5433 no host) e web (porta 8000)
- `apps/base`: blocks.py (BODY_BLOCKS), choices.py, mixins.py (SeoMixin)
- 7 apps com todos os models e migrações:
  - `core`: HomePage
  - `pessoas`: AreaConhecimento (snippet), DocentesIndexPage, DocentePage
  - `ensino`: DisciplinasIndexPage, DisciplinaPage, MaterialDisciplina
  - `pesquisa`: ProjetosIndexPage, ProjetoPage, ProdutoProjeto, PublicacoesIndexPage, PublicacaoPage
  - `noticias`: PostsIndexPage, PostPage
  - `institucional`: DocumentosIndexPage, DocumentoPage, EventosIndexPage, EventoPage
- `config/settings` em três camadas: base, dev, production
- Debug Toolbar com INTERNAL_IPS automático para Docker Gateway
- `.gitignore` com exclusão de `*:Zone.Identifier` (artefatos WSL2)
- `.env.example` com todas as variáveis necessárias

---

[Unreleased]: https://github.com/EduMBrito/portal-agronomia/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/EduMBrito/portal-agronomia/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/EduMBrito/portal-agronomia/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/EduMBrito/portal-agronomia/releases/tag/v0.1.0
