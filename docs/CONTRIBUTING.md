# CONTRIBUTING.md — Portal Agronomia IFSertãoPE

## Modelo de Trabalho

Eduardo Brito (Professor de Informática) é o desenvolvedor único. As contribuições externas seguem o fluxo padrão de pull request descrito abaixo.

## Ambiente de Desenvolvimento

### Pré-requisitos

- Docker Engine 24+ e Docker Compose v2
- Git
- Visual Studio Code (recomendado)
- WSL2 no Windows (ambiente atual de desenvolvimento)

### Setup inicial

```bash
git clone https://github.com/<org>/portal-agronomia.git
cd portal-agronomia

# Copie e configure as variáveis de ambiente
cp .env.example .env

# Suba os containers
docker compose up -d

# Aplique as migrações
docker compose exec web python manage.py migrate

# Monte a árvore de páginas (HomePage + as 7 seções) — obrigatório, idempotente
docker compose exec web python manage.py bootstrap_site

# Crie o superusuário
docker compose exec web python manage.py createsuperuser

# Configure os grupos de permissão
docker compose exec web python manage.py setup_grupos

# (opcional) Conteúdo de exemplo para desenvolver com o portal populado
docker compose exec web python manage.py populate_content
```

Acesse em: http://localhost:8000  
Painel admin: http://localhost:8000/admin/

### Comandos úteis

```bash
# Logs em tempo real
docker compose logs -f web

# Shell Django
docker compose exec web python manage.py shell

# Criar migrações após alterar models
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Recompilar o CSS após mexer em templates (obrigatório antes de commitar)
./scripts/build-css.sh

# Recompilar sozinho a cada save, durante o desenvolvimento
./scripts/build-css.sh --watch

# Linting Python (Ruff)
docker compose exec web ruff check .

# Reiniciar apenas o container web
docker compose restart web
```

## Git Workflow

### Branches

| Padrão | Uso |
|---|---|
| `main` | Branch protegida — apenas via merge de PR revisado |
| `feature/<nome>` | Nova funcionalidade |
| `fix/<nome>` | Correção de bug |
| `docs/<nome>` | Documentação apenas |
| `refactor/<nome>` | Refatoração sem nova feature |

Exemplos:
```
feature/busca-textual
fix/slug-nav-header
docs/api-endpoints
```

### Commits

Formato: `<tipo>: <descrição em português ou inglês>`

| Tipo | Quando usar |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Documentação |
| `refactor` | Refatoração sem mudança de comportamento |
| `style` | Formatação, CSS, sem lógica |
| `test` | Testes |
| `chore` | Dependências, configuração |

Exemplos:
```
feat: adiciona filtro por área de conhecimento em DocentesIndexPage
fix: corrigir URL de adição rápida no dashboard do admin
docs: criar docs/ARCHITECTURE.md e docs/DATABASE.md
refactor: extrair lógica de paginação para mixin reutilizável
```

### Pull Request

1. Crie a branch a partir de `main`
2. Faça commits atômicos e descritivos
3. Abra PR apontando para `main`
4. Descreva o que mudou e por quê
5. Aguarde revisão antes de fazer merge

## Rodando os Testes

```bash
# Testes unitários com pytest
docker compose exec web pytest

# Com cobertura
docker compose exec web pytest --cov=apps --cov-report=term-missing

# Só um módulo
docker compose exec web pytest tests/test_pesquisa.py
```

São 59 testes cobrindo os 7 módulos. Os `models.py` de `core`, `ensino`,
`noticias` e `pesquisa` estão em 100%; `pessoas` em 98% e `institucional` em 87%.

O que ainda não tem teste: `apps/core/wagtail_hooks.py` (36% — os painéis do
dashboard do admin) e os management commands `bootstrap_site`, `setup_grupos` e
`populate_content`, que hoje são validados rodando à mão em banco limpo.

### Como os testes são escritos

As fixtures ficam em `tests/conftest.py` e montam a árvore do Wagtail
(HomePage → IndexPage → páginas de conteúdo). Os testes de listagem chamam
`get_context()` direto com o `rf` (RequestFactory), sem passar pelo HTTP —
é mais rápido e testa a lógica de filtro/ordenação/paginação isoladamente.

Ao escrever um teste novo, confira que ele **falha** quando você quebra de
propósito o comportamento que ele deveria proteger. Teste que passa nos dois
casos não protege nada.

## Linting

O projeto usa o **Ruff apenas como linter**. Configuração em `pyproject.toml`.

```bash
# Verificar
docker compose exec web ruff check .

# Corrigir o que for automatizável (imports fora de ordem, imports não usados…)
docker compose exec web ruff check --fix .
```

Regras ativas: `E`/`W` (pycodestyle), `F` (pyflakes), `I` (ordenação de imports),
`UP` (sintaxe moderna) e `B` (bugbear). Linha de até 100 caracteres. As migrações
são excluídas por serem geradas pelo Django.

### Por que não há formatter automático

O projeto **não** usa Black nem `ruff format`. Ambos reformatariam o idioma de
painéis do Wagtail usado em todos os models:

```python
# como está hoje
MultiFieldPanel([
    FieldPanel("codigo"),
    FieldPanel("carga_horaria"),
], heading="Informações gerais"),
```

O formatter explodiria isso em uma forma bem mais verbosa, reescrevendo 31
arquivos (~875 linhas) e poluindo o `git blame` de todos os models. Como o
código já segue um estilo consistente, optou-se por manter a formatação manual
e usar o Ruff só para o que ele pega de fato: imports não usados, variáveis
mortas, nomes indefinidos e ordenação de imports.

Se um dia o projeto ganhar mais colaboradores, vale reavaliar — formatter
automático rende mais quanto mais gente mexe no código.

## Adicionando um Novo Módulo

1. Criar o app: `docker compose exec web python manage.py startapp nome_modulo apps/nome_modulo`
2. Registrar em `config/settings/base.py` → `LOCAL_APPS`
3. Criar models herdando de `Page` e `SeoMixin` quando apropriado
4. Criar migrações
5. Registrar `subpage_types` e `parent_page_types` no model
6. Criar templates em `templates/nome_modulo/`
7. Atualizar `apps/core/wagtail_hooks.py` com os atalhos do dashboard
8. Atualizar `apps/core/management/commands/setup_grupos.py` com as permissões

## Estrutura de Templates

```
templates/
├── base.html               # layout master
├── includes/
│   ├── header.html
│   ├── footer.html
│   └── pagination.html
├── base/blocks/            # partials de blocos StreamField
├── core/
├── pessoas/
├── ensino/
├── pesquisa/
├── noticias/
└── institucional/
```

Convenção de nome: `<app>/<model_em_snake_case>.html`  
Exemplo: `DocentePage` → `pessoas/docente_page.html`
