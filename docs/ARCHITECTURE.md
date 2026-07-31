# ARCHITECTURE.md — Portal Agronomia IFSertãoPE

## Visão Geral

Portal web do curso de Agronomia do Campus Petrolina Zona Rural do IFSertãoPE. Centraliza produção acadêmica, materiais didáticos, projetos de pesquisa, publicações científicas e documentos institucionais em um CMS gerenciado pelos próprios docentes.

## Stack

| Camada | Tecnologia | Versão |
|---|---|---|
| CMS / Backend | Wagtail (Django) | 6.3 / 5.1 |
| Banco de dados | PostgreSQL | 16 |
| Servidor WSGI | Gunicorn | — |
| Proxy reverso | Nginx | — |
| Frontend | Django Templates + HTMX | 2.0.3 |
| Estilização | Tailwind CSS (CLI standalone, compilado local) | 4.3 |
| Containerização | Docker + Docker Compose | — |
| Linguagem | Python | 3.12 |

## Estrutura de Pastas

```
portal-agronomia/
├── apps/
│   ├── base/           # blocks.py, choices.py, mixins.py — reutilizáveis
│   ├── core/           # HomePage, configurações globais, dashboard hooks
│   ├── pessoas/        # DocentePage + AreaConhecimento (snippet)
│   ├── ensino/         # DisciplinaPage + MaterialDisciplina
│   ├── pesquisa/       # ProjetoPage + PublicacaoPage
│   ├── noticias/       # PostPage
│   └── institucional/  # DocumentoPage + EventoPage
├── config/
│   ├── settings/
│   │   ├── base.py     # configurações compartilhadas
│   │   ├── dev.py      # DEBUG=True, debug_toolbar, INTERNAL_IPS automático
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── templates/          # todos os templates HTML (23 arquivos)
├── static/             # arquivos estáticos do projeto
├── media/              # uploads (gerenciado pelo Wagtail)
├── docs/               # esta pasta
├── docker-compose.yml
├── Dockerfile
└── manage.py
```

## Arquitetura de Páginas (Wagtail Page Tree)

O Wagtail organiza o conteúdo em uma árvore de páginas. Cada nó é uma instância de um Page type específico:

```
Root
└── HomePage  (core)
    ├── DocentesIndexPage      → DocentePage (N)
    ├── DisciplinasIndexPage   → DisciplinaPage (N)
    │                              └── MaterialDisciplina (Orderable inline)
    ├── ProjetosIndexPage      → ProjetoPage (N)
    │                              └── ProdutoProjeto (Orderable inline)
    ├── PublicacoesIndexPage   → PublicacaoPage (N)
    ├── PostsIndexPage         → PostPage (N)
    ├── DocumentosIndexPage    → DocumentoPage (N)
    └── EventosIndexPage       → EventoPage (N)
```

Cada IndexPage define `subpage_types` e `parent_page_types` para restringir onde cada tipo pode ser criado.

## Fluxo da Aplicação

```
Usuário (browser)
    │
    ▼
Nginx :80/:443  ──── arquivos estáticos/media ──── /staticfiles/ /media/
    │
    ▼
Gunicorn :8000
    │
    ▼
Django / Wagtail
    ├── /admin/      → Wagtail Admin (CMS)
    ├── /django-admin/ → Django Admin
    ├── /documents/  → Download de documentos Wagtail
    └── /*           → Wagtail Page Router → Page.serve() → Template
```

## Módulos e Responsabilidades

### `apps/base`
Sem modelos de negócio. Contém:
- `blocks.py` — `BODY_BLOCKS`: lista de StreamField blocks reutilizados por ProjetoPage, PublicacaoPage e PostPage (RichText, ImageChooser, DocumentChooser, EmbedBlock, CalloutBlock)
- `choices.py` — todas as listas de choices organizadas por domínio
- `mixins.py` — `SeoMixin`: adiciona meta_description e og_image a qualquer Page
- `wagtail_hooks.py` — branding CSS institucional (paleta de cores no admin)

### `apps/core`
- `HomePage` — página raiz, agrega estatísticas e conteúdo recente no contexto
- `wagtail_hooks.py` — três painéis do dashboard admin: BemVindoPanel, ResumoConteudoPanel, AcoesRapidasPanel
- `management/commands/setup_grupos.py` — cria grupos Coordenador, Docente, Técnico com permissões Wagtail

### `apps/pessoas`
- `AreaConhecimento` — snippet (sem URL pública), usado como tag de classificação
- `DocentesIndexPage` — listagem com filtro por área e paginação (12/página)
- `DocentePage` — perfil público do docente

### `apps/ensino`
- `DisciplinasIndexPage` — grade agrupada por período com filtro
- `DisciplinaPage` — inclui `MaterialDisciplina` (Orderable inline)

### `apps/pesquisa`
- `ProjetosIndexPage` — filtro por tipo + status, paginação (9/página)
- `ProjetoPage` — inclui `ProdutoProjeto` (Orderable inline)
- `PublicacoesIndexPage` — filtro por tipo, paginação (15/página)
- `PublicacaoPage` — campos DOI, ISSN, autores internos (M2M) e externos (CharField livre)

### `apps/noticias`
- `PostsIndexPage` — feed cronológico, paginação (9/página)
- `PostPage` — autor vinculado a DocentePage, StreamField rico, tags

### `apps/institucional`
- `DocumentosIndexPage` — filtro por tipo, paginação (20/página)
- `DocumentoPage` — arquivo obrigatório (Wagtail Document), flag ativo/inativo
- `EventosIndexPage` — filtro por tipo + flag próximos, paginação (9/página)
- `EventoPage` — suporte a evento online/presencial, vínculo com ProjetoPage

## Decisões Técnicas

### Por que Wagtail?
- CMS Django maduro, open-source, sem custo de licença
- Painel admin intuitivo — docentes sem experiência técnica conseguem publicar
- Histórico de revisões nativo, permissões por página, sistema de imagens otimizadas
- StreamField permite conteúdo rico sem banco de dados rígido

### Por que PostgreSQL?
- Recomendado pelo Wagtail para full-text search nativo
- Suporte robusto a JSON (StreamField armazena JSON)

### Por que Docker?
- Eduardo mantém múltiplos projetos Python/PostgreSQL na mesma máquina (WSL2)
- Isolamento total: PostgreSQL na porta 5433 do host (evita conflito com porta 5432 de outros projetos)

### Tailwind compilado localmente
O CSS é gerado pelo **binário standalone** do Tailwind CLI (`scripts/build-css.sh`),
não pelo Play CDN. Três motivos:

- O Play CDN compila o CSS em runtime no browser — inadequado para produção
- O servidor do campus não deve depender de CDN externo para renderizar o portal
- O binário standalone dispensa Node e npm, tanto aqui quanto no servidor

A paleta institucional fica em `assets/css/input.css`, no bloco `@theme` — na v4
a configuração é feita em CSS, não mais em `tailwind.config.js`. A saída
(`static/css/tailwind.css`, ~32 KB minificados) é **versionada no Git**, então o
deploy não precisa de etapa de build: o `collectstatic` coleta o arquivo pronto.
Em troca, é preciso rodar `./scripts/build-css.sh` e commitar o resultado sempre
que um template mudar.

### HTMX
Adicionado para futuras interações sem full-page reload (ex: filtros AJAX em listagens). Atualmente o middleware `django_htmx` está registrado mas os templates ainda usam navegação tradicional.

## Grupos e Permissões

| Grupo | Escopo de publicação |
|---|---|
| Administrador | Total — Django + Wagtail completo |
| Coordenador | Publica qualquer conteúdo em toda a árvore |
| Docente | Cria e edita Posts, Publicações e Projetos (sem publicar) |
| Técnico | Cria, edita e publica Documentos e Eventos |
| Público | Somente leitura (sem acesso ao admin) |

Grupos criados pelo management command: `python manage.py setup_grupos`

## Paleta de Cores Institucional

| Nome | Hex | Uso |
|---|---|---|
| Verde Escuro | `#2D6636` | Cabeçalho, botões primários |
| Verde Base | `#3A7D44` | Links ativos, ícones |
| Verde Claro | `#D4EDDA` | Fundos de seção |
| Azul Noite | `#122D52` | Sidebar, rodapé |
| Azul Escuro | `#1A3C6E` | Títulos |
| Cinza Campo | `#E8EDE9` | Fundo geral da página |
