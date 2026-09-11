# Portal Agronomia — IFSertãoPE

Portal web do curso de **Agronomia** do Instituto Federal do Sertão Pernambucano, Campus Petrolina Zona Rural. Centraliza a produção acadêmica, materiais didáticos, projetos de pesquisa, publicações científicas e documentos institucionais.

O conteúdo é mantido por uma **comissão gestora**: o docente submete o que deseja publicar e a comissão insere pelo painel administrativo, apoiada por ferramentas de carga em massa (importação de currículo Lattes e colheita de publicações via ORCID).

[![CI](https://github.com/EduMBrito/portal-agronomia/actions/workflows/ci.yml/badge.svg)](https://github.com/EduMBrito/portal-agronomia/actions/workflows/ci.yml)

**Stack:** Django 5.1 · Wagtail 6.3 · PostgreSQL 16 · Tailwind CSS 4.3 · HTMX 2.0 · Docker

CSS e JavaScript são servidos localmente, sem CDN — o portal renderiza por
completo em um servidor sem acesso à internet.

---

## Pré-requisitos

- [Docker Engine 24+](https://docs.docker.com/engine/install/) e Docker Compose v2
- Git

> Desenvolvido em WSL2 (Ubuntu) e em macOS; funciona igualmente em Linux nativo.
> O `scripts/build-css.sh` detecta a plataforma e baixa o binário correspondente.

---

## Instalação (desenvolvimento)

```bash
# 1. Clone o repositório
git clone https://github.com/EduMBrito/portal-agronomia.git
cd portal-agronomia

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env se necessário (os valores padrão funcionam para dev)

# 3. Suba os containers
docker compose up -d

# 4. Aplique as migrações
docker compose exec web python manage.py migrate

# 5. Monte a árvore de páginas (HomePage + as 7 seções)
docker compose exec web python manage.py bootstrap_site

# 6. Crie o superusuário
docker compose exec web python manage.py createsuperuser

# 7. Crie os grupos de permissão
docker compose exec web python manage.py setup_grupos

# 8. (opcional) Carregue conteúdo de exemplo para navegar no portal
docker compose exec web python manage.py populate_content
```

> O passo 5 é obrigatório em uma instalação nova: sem ele o Wagtail responde
> com a página padrão "Welcome to your new Wagtail site!" e o menu do topo
> aponta para seções que ainda não existem. O comando é idempotente.

Acesse:
- Portal público: http://localhost:8000
- Painel admin: http://localhost:8000/admin/

O banco PostgreSQL fica disponível em `localhost:5433` (porta alterada para não conflitar com instalações locais).

---

## Como rodar em desenvolvimento

```bash
# Subir tudo
docker compose up -d

# Ver logs em tempo real
docker compose logs -f web

# Parar
docker compose down

# Shell Django
docker compose exec web python manage.py shell

# Criar migrações após alterar models
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Recompilar o CSS após mexer em templates — commite o resultado
./scripts/build-css.sh

# Ou deixar recompilando sozinho enquanto você edita
./scripts/build-css.sh --watch
```

---

## Estrutura de Pastas

```
portal-agronomia/
├── apps/
│   ├── base/           # blocks.py, choices.py, mixins.py — componentes reutilizáveis
│   ├── core/           # HomePage, dashboard hooks, management commands
│   ├── pessoas/        # DocentePage + AreaConhecimento (snippet)
│   ├── ensino/         # DisciplinaPage + MaterialDisciplina
│   ├── pesquisa/       # ProjetoPage + PublicacaoPage
│   ├── noticias/       # PostPage
│   └── institucional/  # DocumentoPage + EventoPage
├── config/
│   ├── settings/
│   │   ├── base.py     # configurações compartilhadas
│   │   ├── dev.py      # DEBUG=True, debug toolbar
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── assets/
│   └── css/input.css   # fonte do Tailwind — paleta institucional no @theme
├── templates/          # 23 templates HTML organizados por módulo
├── static/             # css/tailwind.css compilado, js/htmx.min.js, imagens
├── tests/              # 59 testes — fixtures em conftest.py
├── scripts/            # setup.sh e build-css.sh
├── media/              # uploads gerenciados pelo Wagtail
├── docs/               # documentação técnica completa
├── .github/workflows/  # integração contínua
├── pyproject.toml      # configuração do Ruff
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── manage.py
```

---

## Módulos

| Módulo | Descrição |
|---|---|
| Docentes | Perfis públicos dos professores com Lattes, ORCID e áreas de atuação |
| Disciplinas | Grade curricular com materiais didáticos por disciplina |
| Projetos | Pesquisa, extensão, TCC, PIBIC e PIBEX com equipe e produtos |
| Publicações | Artigos, livros, TCC, dissertações e teses |
| Posts | Blog institucional — textos submetidos pelos docentes à comissão |
| Documentos | Regulamentos, editais, atas e formulários institucionais |
| Eventos | Seminários, defesas de TCC, workshops e visitas técnicas |

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Decisões técnicas, fluxo da aplicação, módulos |
| [DATABASE.md](docs/DATABASE.md) | Diagrama ER, tabelas, migrações, backup |
| [DEPLOY.md](docs/DEPLOY.md) | Passo a passo para o servidor do campus |
| [API.md](docs/API.md) | URLs públicas, filtros, parâmetros de busca |
| [CONTRIBUTING.md](docs/CONTRIBUTING.md) | Git workflow, testes, lint e CI |
| [SEGURANCA.md](docs/SEGURANCA.md) | Pendências de segurança antes do deploy |
| [CHANGELOG.md](docs/CHANGELOG.md) | Histórico de versões |

---

## Qualidade

```bash
docker compose exec web pytest                 # 59 testes
docker compose exec web ruff check .           # lint
./scripts/build-css.sh                         # recompila o CSS
```

O CI roda os três a cada push e pull request, mais a checagem de migrações
pendentes. Detalhes em [CONTRIBUTING.md](docs/CONTRIBUTING.md).

---

## Licença

MIT © 2026 Eduardo Brito / IFSertãoPE
