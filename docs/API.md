# API.md — Portal Agronomia IFSertãoPE

## Visão Geral

O portal não expõe uma REST API pública. O acesso ao conteúdo é feito por meio de páginas HTML renderizadas pelo Wagtail. Esta documentação cobre:

1. URLs públicas do portal (leitura)
2. Wagtail Admin API (uso interno do CMS)
3. Busca textual nativa do Wagtail

## URLs Públicas

Todas as rotas são servidas pelo Wagtail Page Router. Os slugs são configurados no painel admin.

### Estrutura de Rotas

| URL | Page Type | Descrição |
|---|---|---|
| `/` | `HomePage` | Página inicial com estatísticas e destaques |
| `/docentes/` | `DocentesIndexPage` | Listagem de docentes |
| `/docentes/<slug>/` | `DocentePage` | Perfil individual |
| `/disciplinas/` | `DisciplinasIndexPage` | Grade curricular agrupada por período |
| `/disciplinas/<slug>/` | `DisciplinaPage` | Disciplina com materiais |
| `/projetos/` | `ProjetosIndexPage` | Listagem de projetos |
| `/projetos/<slug>/` | `ProjetoPage` | Projeto com produtos |
| `/publicacoes/` | `PublicacoesIndexPage` | Repositório de publicações |
| `/publicacoes/<slug>/` | `PublicacaoPage` | Publicação individual |
| `/noticias/` | `PostsIndexPage` | Feed de posts |
| `/noticias/<slug>/` | `PostPage` | Post completo |
| `/documentos/` | `DocumentosIndexPage` | Documentos institucionais |
| `/documentos/<slug>/` | `DocumentoPage` | Documento com download |
| `/eventos/` | `EventosIndexPage` | Agenda de eventos |
| `/eventos/<slug>/` | `EventoPage` | Evento individual |

> Os slugs acima são os slugs padrão configurados durante a criação da árvore de páginas. Podem ser alterados no painel admin em Settings → Pages.

### Parâmetros de Filtro (Query String)

#### `GET /docentes/?area=<slug>`
Filtra docentes por área de conhecimento.

| Parâmetro | Tipo | Exemplo |
|---|---|---|
| `area` | string (slug) | `?area=agronomia-tropical` |
| `page` | int | `?page=2` |

#### `GET /disciplinas/?periodo=<n>`
Filtra disciplinas por período da grade.

| Parâmetro | Tipo | Exemplo |
|---|---|---|
| `periodo` | int (1–10) | `?periodo=3` |

#### `GET /projetos/?tipo=<tipo>&status=<status>`

| Parâmetro | Valores possíveis |
|---|---|
| `tipo` | `pesquisa`, `extensao`, `ensino`, `tcc`, `pibic`, `pibex` |
| `status` | `em_andamento`, `concluido`, `suspenso`, `submetido` |
| `page` | int |

#### `GET /publicacoes/?tipo=<tipo>`

| Parâmetro | Valores possíveis |
|---|---|
| `tipo` | `artigo_periodico`, `artigo_anais`, `capitulo_livro`, `livro`, `relatorio_tecnico`, `tcc`, `dissertacao`, `tese` |
| `page` | int |

#### `GET /documentos/?tipo=<tipo>`

| Parâmetro | Valores possíveis |
|---|---|
| `tipo` | `regulamento`, `formulario`, `edital`, `ata`, `resolucao`, `manual`, `outro` |
| `page` | int |

#### `GET /eventos/?tipo=<tipo>&futuros=1`

| Parâmetro | Valores possíveis |
|---|---|
| `tipo` | `seminario`, `defesa_tcc`, `defesa_projeto`, `workshop`, `aula_aberta`, `visita_tecnica`, `outro` |
| `futuros` | `1` (apenas eventos futuros) |
| `page` | int |

## Busca Textual

O Wagtail expõe busca em:

```
GET /search/?query=<termo>
```

A busca é configurada em `config/settings/base.py` usando o backend PostgreSQL do Wagtail. Os models indexados são aqueles com `search_fields` definidos (`DocentePage`, `DisciplinaPage`, `ProjetoPage`, `PublicacaoPage`, `PostPage`, `EventoPage`).

## Wagtail Admin

### Autenticação

O admin Wagtail não usa token — requer sessão autenticada via login em `/admin/login/`.

### URLs do Painel Administrativo

| URL | Descrição |
|---|---|
| `/admin/` | Dashboard |
| `/admin/pages/` | Árvore de páginas |
| `/admin/pages/add/<app>/<model>/<parent_pk>/` | Criar página filha |
| `/admin/images/` | Biblioteca de imagens |
| `/admin/documents/` | Biblioteca de documentos |
| `/admin/snippets/pessoas/areaconhecimento/` | Áreas de Conhecimento |

### Wagtail API v2 (opcional)

O Wagtail inclui uma API REST opcional. Para habilitá-la, adicione a `INSTALLED_APPS`:

```python
"wagtail.api.v2",
```

E registre os endpoints em `config/urls.py`. A API suporta filtragem, paginação e fields customizados. Não está habilitada por padrão neste projeto.

## Download de Documentos

Arquivos armazenados como `wagtaildocs.Document` são servidos via:

```
GET /documents/<id>/<filename>
```

A URL exata é gerada pelo método `document.url` no template.

## Paginação

Todas as listagens usam a paginação nativa do Django (`Paginator`). A resposta HTML inclui o componente `templates/includes/pagination.html`. Os parâmetros são:

| Parâmetro | Descrição |
|---|---|
| `page` | Número da página (começa em 1) |

Tamanhos de página por módulo:

| Módulo | Itens/página |
|---|---|
| Docentes | 12 |
| Projetos | 9 |
| Publicações | 15 |
| Posts | 9 |
| Documentos | 20 |
| Eventos | 9 |
