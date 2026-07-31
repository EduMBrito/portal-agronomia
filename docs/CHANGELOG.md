# CHANGELOG — Portal Agronomia IFSertãoPE

Formato: [vX.Y.Z] - YYYY-MM-DD  
Seções: Added, Changed, Fixed, Removed

---

## [Unreleased]

### Added
- Management command `bootstrap_site` — cria a HomePage, aponta o Site do Wagtail para ela, remove a página padrão "Welcome to your new Wagtail site!" e cria as sete IndexPages com os slugs esperados pelo menu. Idempotente
- Busca textual em todo o portal (`/busca/`) usando o backend nativo do Wagtail
- Suíte de testes com pytest + pytest-django — 59 testes cobrindo os 7 módulos
- `tests/test_pesquisa.py` (20 testes) — filtros por tipo e status, cumulatividade, ordenação, paginação (9 e 15), rascunhos fora da listagem pública, relações reversas do perfil de docente e `PROTECT` do coordenador
- `tests/test_noticias.py` (9 testes) — feed cronológico, paginação, rascunhos, `PROTECT` do autor e preenchimento automático de `data_publicacao`
- `config/settings/production.py` — HTTPS, HSTS, cookies seguros, `ManifestStaticFilesStorage`, logging para stdout
- `docker-compose.prod.yml`, `docs/nginx.conf` e `docs/gunicorn.service`
- Management command `populate_content` — carga de conteúdo de exemplo para demonstração
- Página "Sobre o LADI" (`/sobre/`) e logo no rodapé
- Pasta `docs/` com ARCHITECTURE.md, API.md, DATABASE.md, DEPLOY.md, CONTRIBUTING.md, CHANGELOG.md

- `assets/css/input.css` — fonte do Tailwind com a paleta institucional no bloco `@theme`
- `scripts/build-css.sh` — compila o CSS com o binário standalone do Tailwind (sem Node/npm); aceita `--watch`
- `static/css/tailwind.css` — CSS compilado e versionado (~32 KB minificados)
- `static/js/htmx.min.js` — HTMX 2.0.3 servido localmente, sem CDN

- `pyproject.toml` com a configuração do Ruff — regras `E`, `W`, `F`, `I`, `UP`, `B`, linha de 100 caracteres, migrações excluídas
- `.github/workflows/ci.yml` — CI no GitHub Actions com três jobs paralelos: Ruff, conferência de que o CSS commitado está atualizado, e testes com PostgreSQL 16 + checagem de migrações pendentes

### Fixed
- `scripts/build-css.sh` — o binário do Tailwind era cacheado só por versão; alternar entre WSL2 e macOS no mesmo checkout reaproveitaria o executável do outro sistema. A plataforma agora entra no nome do arquivo
- `apps/institucional/models.py` — `ObjectList` e `TabbedInterface` importados e nunca usados
- `apps/core/management/commands/populate_content.py` — três variáveis atribuídas e nunca usadas
- `tests/test_pessoas.py` — `pytest.raises(Exception)` trocado por `IntegrityError`; a forma genérica passaria mesmo se o erro fosse outro
- `apps/core/management/commands/bootstrap_site.py` — `Optional[Page]` trocado por `Page | None`
- Ordenação de imports em 24 arquivos e 8 linhas acima de 100 caracteres

### Changed
- Ruff adotado **apenas como linter**, sem formatter automático — Black e `ruff format` reescreveriam o idioma de painéis do Wagtail em 31 arquivos. Decisão registrada no CLAUDE.md e no `docs/CONTRIBUTING.md`
- `pytest-cov` adicionado ao `requirements-dev.txt` — o `docs/CONTRIBUTING.md` já documentava `pytest --cov`, mas o pacote nunca havia sido instalado e o comando falhava
- **Tailwind CSS: Play CDN substituído por build local (v3.4 → v4.3.3).** Configuração migrada de `tailwind.config.js` inline para `@theme` em CSS
- **HTMX: carregado de `static/js/` em vez do unpkg.com.** Com isto e o Tailwind local, o portal não faz mais nenhuma requisição a CDN externo — requisito para o servidor do campus
- Utilities renomeadas conforme a escala da v4: `shadow-sm` → `shadow-xs` (30x), `rounded` → `rounded-sm` (54x), `outline-none` → `outline-hidden` (3x). Valores computados são idênticos aos da v3
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
