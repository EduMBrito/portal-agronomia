# CHANGELOG — Portal Agronomia IFSertãoPE

Formato: [vX.Y.Z] - YYYY-MM-DD  
Seções: Added, Changed, Fixed, Removed

---

## [Unreleased]

### Changed

- `DocumentoPage` passa a redirecionar (302) direto para o PDF, em vez de tentar renderizar
  uma página de detalhe. O model guarda só metadados — tipo, descrição, as duas datas e o
  flag `ativo` — e a listagem em `/documentos/` já mostra todos eles, então uma página de
  detalhe não teria nada novo na tela. O que a URL própria dá, e por isso ela continua
  existindo, é um link estável e citável: `/documentos/regulamento-tcc/` pode entrar num
  ofício ou numa ementa e segue valendo quando a comissão substituir o arquivo. O 302 é
  proposital — um 301 ficaria no cache do navegador apontando para a versão antiga

### Fixed

- Toda página de documento publicada respondia 500: a `DocumentoPage` tinha URL pública e
  não existia `institucional/documento_page.html`. Defeito anterior ao upgrade para as
  versões LTS, descoberto ao renderizar as páginas de verdade. O `xfail` estrito que o
  documentava em `tests/test_templates.py` deu lugar a três testes do comportamento novo,
  incluindo o que garante que a URL da página sobrevive à troca do arquivo

### Changed

- **Django 5.1 → 5.2 LTS e Wagtail 6.3 → 7.4 LTS.** As duas versões anteriores estavam
  fora de suporte e não recebiam mais correção de segurança: Django 5.1 encerrou em
  03/12/2025 e Wagtail 6.3 LTS em 01/05/2026. O novo par tem suporte até abril/2028 e
  novembro/2027. Nenhuma migração nova foi necessária nos models do projeto; o Wagtail
  aplica as suas próprias. Sem aviso de deprecação restante na suíte

### Fixed

- `templates/ensino/disciplina_page.html` carregava `wagtaildocs_tags`, biblioteca de tags
  que não existe — toda página de disciplina respondia 500. O template não usava nenhuma
  tag dela. Erro anterior ao upgrade, descoberto ao renderizar as páginas de verdade

### Added

- `tests/test_templates.py` — 28 testes que pedem cada URL pública pelo client do Django,
  compilando e renderizando o template. O resto da suíte exercita apenas `get_context`,
  que nunca toca no template, e foi por isso que o erro acima passou despercebido.
  Cobre listagens, filtros (inclusive valor inválido), páginas de detalhe, busca e o
  escape do termo pesquisado
- Um `xfail` estrito documenta um segundo defeito anterior ao upgrade: `DocumentoPage` tem
  URL pública mas não existe `institucional/documento_page.html`, então toda página de
  documento publicada responde 500. Decidir se ela ganha template ou deixa de ser
  navegável — quando resolver, o `xfail` acusa e deve ser removido

### Added

- Management command `importar_lattes <arquivo.xml>` — primeira das duas ferramentas de
  carga em massa para a comissão gestora. Lê o XML exportado do Currículo Lattes e cria ou
  atualiza `DocentePage` (titulação mais alta concluída, instituição, áreas de atuação e
  bio) e `ProjetoPage` (natureza, situação, período, equipe e descrição), sempre como
  rascunho para a comissão revisar e publicar. Idempotente, como o `bootstrap_site`:
  deduplica o docente pelo `lattes_url` e o projeto pelo slug do título
  - `--email` sobrepõe o e-mail do XML, que costuma ser pessoal; obrigatório quando o XML
    não traz nenhum e o campo é requerido na `DocentePage`
  - `--dry-run` mostra o resultado e desfaz tudo no final
  - Projeto cujo coordenador ainda não tem perfil no portal é pulado e relatado com o nome
    do responsável — `ProjetoPage.coordenador` é FK obrigatória e atribuí-la ao dono do XML
    publicaria autoria errada
  - Integrantes sem perfil (estudantes, externos) são listados no relatório final:
    `participantes_docentes` só aceita `DocentePage`
  - Alerta quando o XML está sob `MEDIA_ROOT`, que o Nginx serve sem autenticação em
    produção — o arquivo tem CPF, RG, filiação e telefone. Nada disso entra no banco
- 33 testes em `tests/test_importar_lattes.py` — parser (tradução do vocabulário do CNPq,
  titulação, áreas, datas por ano) e comando de ponta a ponta (rascunho, idempotência,
  `--dry-run`, coordenador ausente, árvore de páginas ausente)

### Fixed

- `resumir()` remove o espaço à esquerda que o `Truncator.chars()` do Django 5.1 devolve —
  ele apareceria no começo do resumo de todo card de listagem de projeto

---

## [0.4.0] - 2026-07-31

Portal autossuficiente e com rede de segurança: nenhuma dependência de CDN
externo, integração contínua e testes nos 7 módulos. É a versão pronta para
o deploy no servidor do campus.

### Added

**Estrutura e conteúdo**
- Management command `bootstrap_site` — cria a HomePage, aponta o Site do Wagtail para ela, remove a página padrão "Welcome to your new Wagtail site!" e cria as sete IndexPages com os slugs esperados pelo menu. Idempotente
- Management command `populate_content` — carga de conteúdo de exemplo para demonstração
- Busca textual em todo o portal (`/busca/`) usando o backend nativo do Wagtail
- Página "Sobre o LADI" (`/sobre/`) e logo no rodapé

**Frontend sem CDN**
- `assets/css/input.css` — fonte do Tailwind com a paleta institucional no bloco `@theme`
- `scripts/build-css.sh` — compila o CSS com o binário standalone do Tailwind (sem Node/npm); aceita `--watch`
- `static/css/tailwind.css` — CSS compilado e versionado (~29 KB minificados)
- `static/js/htmx.min.js` — HTMX 2.0.3 servido localmente

**Qualidade**
- Suíte de testes com pytest + pytest-django — 59 testes cobrindo os 7 módulos
- `tests/test_pesquisa.py` (20 testes) — filtros por tipo e status, cumulatividade, ordenação, paginação (9 e 15), rascunhos fora da listagem pública, relações reversas do perfil de docente e `PROTECT` do coordenador
- `tests/test_noticias.py` (9 testes) — feed cronológico, paginação, rascunhos, `PROTECT` do autor e preenchimento automático de `data_publicacao`
- `pyproject.toml` com a configuração do Ruff — regras `E`, `W`, `F`, `I`, `UP`, `B`, linha de 100 caracteres, migrações excluídas
- `.github/workflows/ci.yml` — CI no GitHub Actions com três jobs paralelos: Ruff, conferência de que o CSS commitado está atualizado, e testes com PostgreSQL 16 + checagem de migrações pendentes

**Produção**
- `config/settings/production.py` — HTTPS, HSTS, cookies seguros, `ManifestStaticFilesStorage`, logging para stdout
- `docker-compose.prod.yml`, `docs/nginx.conf` e `docs/gunicorn.service`
- Pasta `docs/` com ARCHITECTURE.md, API.md, DATABASE.md, DEPLOY.md, CONTRIBUTING.md, CHANGELOG.md

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

## [0.2.0] - 2026-05-23

### Added
- Todos os 21 templates HTML (base.html, includes, 7 módulos completos)
- Integração do Tailwind CSS Play CDN com config da paleta institucional
- HTMX 2.0.3 via CDN
- Paginação em todas as IndexPages
- Filtros por área, período, tipo e status nas listagens
- Contexto com `now` em EventosIndexPage para distinguir eventos passados/futuros

### Changed
- `dockerignore` renomeado para `.dockerignore` (Docker ignorava o arquivo sem o ponto)

---

## [0.1.0] - 2026-05-22

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

[Unreleased]: https://github.com/EduMBrito/portal-agronomia/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/EduMBrito/portal-agronomia/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/EduMBrito/portal-agronomia/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/EduMBrito/portal-agronomia/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/EduMBrito/portal-agronomia/releases/tag/v0.1.0
