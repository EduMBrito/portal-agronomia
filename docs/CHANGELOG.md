# CHANGELOG — Portal Agronomia IFSertãoPE

Formato: [vX.Y.Z] - YYYY-MM-DD  
Seções: Added, Changed, Fixed, Removed

---

## [Unreleased]

### Changed — desenho de deploy para o servidor compartilhado (12/09/2026)

Reescrita do caminho de produção depois do retorno do projeto de infraestrutura
do campus. O portal deixa de presumir servidor próprio e passa a conviver com
outras aplicações no `pve-apps`, atrás do Caddy do `pve-proxy` e contra o
PostgreSQL compartilhado do `pve-db`.

- **O Nginx passa a viver dentro do stack**, como serviço do Compose, em vez de
  ser instalado no host. O `Dockerfile` virou multi-estágio: `app` e `nginx`. A
  aplicação não publica mais porta nenhuma — quem conversa com o proxy é o
  Nginx, na `172.16.172.11:8001`
- **O `collectstatic` saiu do deploy** e foi para o build da imagem. O manifesto
  do `ManifestStaticFilesStorage` vai assado junto, e a ordem de operações que
  derrubava todas as páginas com `Missing staticfiles manifest entry` deixou de
  existir como risco
- **As imagens vêm do GHCR**, construídas pela CI a cada push na `main` e a cada
  tag `vX.Y.Z`. O `docker-compose.prod.yml` não tem mais `build:`: construir no
  servidor roubaria CPU e disco das outras aplicações do campus. `PORTAL_TAG` no
  `.env` escolhe a versão, e a etiqueta de sha curto nunca é reescrita — rollback
  é trocar uma linha
- **O Postgres próprio saiu do `docker-compose.prod.yml`.** O banco é o
  compartilhado em `172.16.172.12`
- **Documentos são entregues pelo Nginx, via `X-Accel-Redirect`.** O Wagtail
  continua checando a permissão de coleção e passa a responder vazio com o
  cabeçalho; o arquivo sai do Nginx, sem passar byte a byte pelo Python.
  Implementação própria em `apps/core/sendfile_nginx.py`, ~20 linhas, em vez de
  somar o `django-sendfile2` às dependências
- **`X-Forwarded-Proto` deixa de ser `$scheme`.** O `nginx.conf` repassa o valor
  que o Caddy mandou, com `map` e queda para `$scheme` quando o cabeçalho não
  existe. Com `$scheme` o Django veria "http" atrás do proxy e entraria em laço
  de redirecionamento
- **`set_real_ip_from 172.16.172.10`** com `real_ip_recursive on`, para o limite
  de tentativas de login enxergar o cliente e não o proxy
- **Tetos de memória por contêiner**: `web` 1800 MB, `nginx` 128 MB. Num host
  compartilhado é o que impede que um vazamento no portal derrube a VM das
  outras aplicações. Medido em execução: 208–212 MB e 9,5–12,6 MB
- **A rotina de `pg_dump` saiu do `DEPLOY.md`.** O backup passa a ser das duas
  camadas da infraestrutura — rotina centralizada no `pve-db` e o PBS

### Added

- **Rota `/healthz/`** (`apps/core/views.py`), com healthcheck nos dois
  contêineres. O do Nginx atravessa Nginx → Gunicorn → banco, que é o mesmo
  caminho do `pve-proxy`; o do `web` fica como diagnóstico. Isenta do
  `SECURE_SSL_REDIRECT`, senão receberia 301
- **Job `imagem` na CI**, construindo e publicando as duas imagens no GHCR
  depois que Ruff, CSS e testes passam
- `apps/core/sendfile_nginx.py` e 7 testes novos — 4 do backend de X-Accel
  (inclusive recusar caminho fora de `SENDFILE_ROOT`) e 3 do `/healthz/`

### Fixed

- **A imagem caiu de 889 MB para 469 MB.** O `.bin/`, com os binários do
  compilador Tailwind (~110 MB por arquitetura), entrava na imagem porque estava
  só no `.gitignore` e não no `.dockerignore`. A produção nunca precisou dele: o
  `static/css/tailwind.css` vai pronto e versionado
- **`SESSION_COOKIE_SECURE` e `CSRF_COOKIE_SECURE` viraram configuráveis**, com
  default `True`. Estavam fixos, o que tornaria impossível validar o painel em
  HTTP interno antes do certificado: o cookie de CSRF não é setado e o login
  falha com "CSRF verification failed"

### Security

Fecha os seis itens restantes do `docs/SEGURANCA.md` — o item 1, das versões EOL, saiu no
upgrade para as LTS.

- **`/media/` deixa de ser alias único no Nginx** (item 2). Só `/media/images/` e
  `/media/original_images/` são servidos; o resto devolve 404. Documento passa pela rota
  `/documents/` do Wagtail, que é onde a permissão de coleção é checada — sem isso,
  bastava adivinhar o nome do arquivo para baixar documento de coleção privada, ou o XML
  do Lattes com CPF e telefone
- **`WAGTAILDOCS_SERVE_METHOD = "serve_view"` explícito**, e não herdado do default: é o
  que sustenta a regra acima. Com `redirect`, o Wagtail mandaria o navegador para a URL
  crua em `/media/`, que agora está bloqueada, e todo download quebraria em silêncio
- **SVG fora do `WAGTAILIMAGES_EXTENSIONS`** (item 3). O Wagtail não sanitiza SVG, e um
  arquivo com `<script>` servido do próprio domínio é XSS na origem do portal
- **Limite de tentativas na tela de login** (item 4): `limit_req` no Nginx, 5 por minuto
  por IP com `burst=3 nodelay`. Correspondência exata em `/admin/login/`, para não
  atrapalhar a comissão editando conteúdo. Nenhuma dependência nova
- **`docs/nginx.conf` virou a fonte única** (item 5). O `DEPLOY.md` manda copiá-lo em vez
  de repetir a configuração; enquanto havia duas cópias, uma ficou sem `ssl_protocols`.
  Ganhou também `server_tokens off`
- **Container não roda mais como root** (item 6): usuário `portal`, UID 1000 para bater
  com o dono dos bind mounts. As ferramentas de compilação saíram junto — `psycopg2-binary`
  e `Pillow` são wheels e nada era construído ali. A imagem caiu de 1,18 GB para 871 MB.
  O `CMD` padrão deixou de ser `runserver` e virou Gunicorn
- **`django_extensions` sai da produção** (item 7), para o `dev.py` junto do
  `debug_toolbar`

### Added

- `tests/test_seguranca.py` — 12 testes travando o que é fácil desfazer sem perceber:
  recusa de SVG (subindo um arquivo com `<script>` pelo formulário de imagem do Wagtail),
  método de entrega dos documentos, URL de documento fora de `/media/`, e ausência das
  ferramentas de desenvolvimento no `INSTALLED_APPS` da base

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
