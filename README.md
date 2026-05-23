# Portal Agronomia — IFSertãoPE

Portal web do curso de **Agronomia** do Instituto Federal do Sertão Pernambucano, Campus Petrolina Zona Rural. Centraliza a produção acadêmica, materiais didáticos, projetos de pesquisa, publicações científicas e documentos institucionais em um painel administrado pelos próprios docentes.

**Stack:** Django 5.1 · Wagtail 6.3 · PostgreSQL 16 · HTMX · Tailwind CSS · Docker

---

## Pré-requisitos

- [Docker Engine 24+](https://docs.docker.com/engine/install/) e Docker Compose v2
- Git

> Desenvolvimento realizado em WSL2 (Ubuntu) no Windows 11. Funciona igualmente em Linux nativo e macOS.

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

# 5. Crie o superusuário
docker compose exec web python manage.py createsuperuser

# 6. Crie os grupos de permissão
docker compose exec web python manage.py setup_grupos
```

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
├── templates/          # 23 templates HTML organizados por módulo
├── static/             # arquivos estáticos do projeto
├── media/              # uploads gerenciados pelo Wagtail
├── docs/               # documentação técnica completa
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
| Posts | Blog institucional alimentado pelos docentes |
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
| [CONTRIBUTING.md](docs/CONTRIBUTING.md) | Git workflow, padrão de commits, testes |
| [CHANGELOG.md](docs/CHANGELOG.md) | Histórico de versões |

---

## Licença

MIT © 2026 Eduardo Brito / IFSertãoPE
