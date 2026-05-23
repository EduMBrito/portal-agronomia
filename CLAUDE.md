# CLAUDE.md — IFSertãoPE

## Contexto da Instituição

- **Instituição:** Instituto Federal do Sertão Pernambucano (IFSertãoPE)
- **Campus:** Campus Petrolina Zona Rural  ampus agrícola com foco em Ciências Agrárias
- **Desenvolvedor:** Eduardo Brito — Professor de Informática

## Modelo de Trabalho

Eduardo é o **desenvolvedor único** em colaboração com Claude Code:

- Claude **lê, analisa e sugere** — Eduardo **decide e implementa**
- **Nenhum auto-write:** modo de aprovação manual sempre ativo
- Diffs são revisados lado a lado antes de qualquer escrita
- Claude deve perguntar antes de fazer suposições sobre regras de negócio agrícolas/institucionais

---

## Stack Técnico

### Restrições
- ✅ Priorizar ferramentas **open-source e gratuitas**
- ❌ Evitar: Firebase, AWS, Azure, SaaS proprietários
- ❌ Sem licenças pagas

---

## Ambiente de Desenvolvimento

- **OS:** WSL2 (Ubuntu) no Windows 11
- **IDE:** Visual Studio Code + extensão Claude Code
- **Controle de versão:** Git + GitHub (repositórios públicos)
- **Deploy:** Servidores locais do campus (Linux)

---

## Documentação Obrigatória

Todo projeto deve conter:

```
/
├── README.md               ← Visão geral, setup, uso
├── CLAUDE.md               ← Este arquivo (contexto para Claude Code)
├── .gitignore
├── .env.example            ← Variáveis de ambiente sem valores reais
└── docs/
    ├── ARCHITECTURE.md     ← Decisões técnicas e estrutura do sistema
    ├── API.md              ← Endpoints, autenticação, exemplos de request/response
    ├── DATABASE.md         ← Modelo de dados, diagrama ER, migrações
    ├── DEPLOY.md           ← Passo a passo para instalar no servidor do campus
    ├── CONTRIBUTING.md     ← Como contribuir com o projeto
    └── CHANGELOG.md        ← Histórico de versões e mudanças
```

### README.md deve conter
- O que o sistema faz (contexto institucional)
- Pré-requisitos
- Passos de instalação (local e produção)
- Como rodar em desenvolvimento
- Estrutura de pastas
- Licença (MIT ou GPL)
- Link para a documentação completa em `docs/`

### docs/ARCHITECTURE.md
- Diagrama ou descrição da arquitetura (frontend, backend, banco)
- Justificativa das escolhas técnicas
- Fluxo geral da aplicação
- Integrações externas (se houver)
- Decisões e trade-offs registrados

### docs/API.md
- Autenticação (como obter token, headers obrigatórios)
- Lista de endpoints com método, rota, descrição
- Exemplos de request e response (JSON)
- Códigos de erro padronizados
- Versionamento da API

### docs/DATABASE.md
- Diagrama ER (pode ser Mermaid no próprio markdown)
- Descrição de cada tabela e seus campos
- Índices relevantes
- Procedimento de migração
- Seeds para dados iniciais

### docs/DEPLOY.md
- Pré-requisitos do servidor (OS, dependências)
- Variáveis de ambiente necessárias
- Passo a passo de instalação no campus
- Como rodar com Docker Compose (se aplicável)
- Configuração do Nginx
- Backup e restore do banco

### docs/CONTRIBUTING.md
- Git workflow (branches, commits, pull requests)
- Padrão de nomenclatura de branches: `feature/*`, `fix/*`, `docs/*`
- Formato de commit (ex: `feat: adiciona cadastro de animais`)
- Como rodar os testes

### docs/CHANGELOG.md
- Formato: [vX.Y.Z] - YYYY-MM-DD
- Seções: Added, Changed, Fixed, Removed

---

## Boas Práticas

### Código
- TypeScript com tipagem forte (sem `any` desnecessário)
- Python com type hints (PEP 484)
- Linting: ESLint + Prettier (TS/JS) ou Ruff + Black (Python)
- Testes unitários: Jest (TS) ou Pytest (Python)
- Funções públicas sempre com docstring ou JSDoc

### Git
- Branch `main` protegida — sem push direto
- Branch `develop` para integração
- Feature branches: `feature/nome-da-feature`
- Commits em português ou inglês, sempre descritivos
- Tags semânticas para releases: `v1.0.0`, `v1.1.0`

### Segurança
- Nunca commitar `.env` com credenciais reais
- Validar entradas do usuário sempre (backend e frontend)
- HTTPS obrigatório em produção
- Senhas sempre com hash (bcrypt ou argon2)

---

## Como Pedir Ajuda ao Claude Code

```bash
# Ler e analisar um arquivo sem escrever nada
@src/models/animal.py Qual é o problema nessa model? Me passa uma sugestão.

# Pedir uma nova feature (Claude sugere, você aprova)
Quero adicionar cadastro de lotes de animais. Sugira a estrutura de dados e a rota.

# Refatoração com revisão de diff
Refatore esse serviço para separar a lógica de negócio da camada de dados.

# Documentação
Gere um docs/API.md baseado nos arquivos de rotas em @src/routes/.

# Debug
@logs/error.log e @src/controllers/producao.ts — me ajude a entender esse erro.
```

---
## Visão deste projeto
O portal tem como objetivo centralizar toda a produção intelectual, didática e institucional do curso de Agronomia, tornando acessível ao publico os materiais de disciplinas, publicações científicas, projetos de pesquisa e extensão, posts de docentes e documentos institucionais.

A plataforma será alimentada pelos próprios professores por meio de um painel administrativo intuitivo, dispensando conhecimento técnico para a inserção de conteúdo.

1.1 Objetivos
# Centralizar a produção acadêmica do curso em um único portal publico Oferecer visibilidade institucional para projetos, publicações e docentes
# Facilitar o acesso a materiais de disciplinas por discentes
# Permitir que docentes publiquem conteúdo de forma autônoma
# Registrar e divulgar eventos, seminários e defesas acadêmicas
# Disponibilizar documentos institucionais do curso de forma organizada

## Arquitetura Tecnológica
CMS / Backend - Wagtail (Django)
Banco de dados - PostgreSQL
Servidor web - Nginx + Gunicorn
Frontend - Django Templates + HTMX
Estilização - Tailwind CSS
Autenticação - Django Auth / LDAP
Armazenamento - Sistema de arquivos local

## Organização do projeto Django
core/ - HomePage, configurações globais, menus de navegação
pessoas/ - Docente Page, Docentes IndexPage, Área Conhecimento
ensino/ - Disciplina Page, Disciplina IndexPage, Material Disciplina
pesquisa/ - Projeto Page, Publicacao Page e seus indexes
notícias/ - Posts Page, Posts IndexPage
institucional/ - Documento Page, Evento Paige e seus indexes
base/ - blocks.py, mixins.py, choices.py reutilizaveis

## Infraestrutura de hospedagem
Sistema operacional: Ubuntu Server 22.04 LTS
Servidor web: Nginx como proxy reverso na porta 80/443
Aplicação: Gunicorn como servidor WSGI na porta 8000
Banco de dados: PostgreSQL 15+
Arquivos estáticos: servidos diretamente pelo Nginx
Certificado SSL: Let's Encrypt (recomendado) ou certificado institucional

## Requisitos do Sistema — Módulos Funcionais

###  Módulo de Docentes
Gerenciamento dos perfis públicos dos professores do curso.
→  Cadastro de perfil com foto, titulação, areas de atuação e bio
→  Campos para link ao Lattes e ORCID
→  Listagem pública de todos os docentes com filtro por área
→  Página individual de cada docente com produção vinculada
→  Relação automatica com disciplinas, projetos e publicações

### Módulo de Disciplinas
Repositório de materiais didáticos por disciplina da grade curricular.
→  Cadastro de disciplinas com código, carga horária e ementa
→  Vinculação ao docente responsável
→  Upload e organização de materiais (slides, PDFs, videos, links)
→  Filtro por período da grade curricular (1o ao 10o)
→  Pagina publica com todos os materiais disponíveis da disciplina

### Módulo de Projetos
Registro e divulgação de projetos de pesquisa, extensão, ensino e TCC.
→  Tipos suportados: Pesquisa, Extensão, Ensino, TCC, PIBIC, PIBEX
→  Cadastro com coordenador, equipe participante, período e status
→  Upload do edital de aprovacao e informações de financiamento
→  Registro de produtos do projeto (artigos, relatórios, softwares)
→  Filtro por tipo, status e área de conhecimento
→  Vinculação a eventos relacionados ao projeto

### Módulo de Publicações
Repositório de produção científica dos docentes do curso.
→  Tipos: artigo em periódico, capítulo de livro, anais, TCC, dissertação, tese
→  Cadastro com autores internos (vinculados ao sistema) e externos
→  Campos para DOI, ISSN, veículo de publicação e data
→  Upload de PDF e link de acesso externo
→  Filtragem por tipo, autor, área e ano
→  Integração do DOI para exibição de metadados

### Módulo de Posts
Blog institucional alimentado pelos próprios docentes.
→  Publicação de textos de opinião, relatos e artigos de divulgação
→  Editor rico com suporte a imagens, embeds (YouTube) e documentos
→  Autoria vinculada ao perfil do docente no sistema
→  Sistema de tags para organização temática
→  Feed cronológico com listagem e paginação

### Módulo de Documentos Institucionais
Repositório de documentos oficiais do curso.
→  Tipos: regulamento, formulário, edital, ata, resolucao, manual
→  Upload de PDFs com descrição e data de publicação
→  Campo de vigência para indicar documentos atualizados
→  Flag "ativo/inativo" para controle de versões
→  Listagem pública organizada por tipo de documento

### Repositório de documentos oficiais do curso.
→  Tipos: regulamento, formulário, edital, ata, resolucao, manual
→  Upload de PDFs com descrição e data de publicação
→  Campo de vigência para indicar documentos atualizados
→  Flag "ativo/inativo" para controle de versões
→  Listagem pública organizada por tipo de documento

###  Módulo de Eventos
Agenda acadêmica do curso com divulgação de atividades.
→  Tipos: seminario, defesa de TCC, workshop, aula aberta, visita técnica
→  Suporte a eventos presenciais e online (com link de acesso)
→  Vinculação a docentes envolvidos e a projetos relacionados
→  Exibição em agenda cronológica na homepage
→  Distinção visual entre eventos futuros e realizados

### Requisitos não-funcionais
Autenticação e autorização por papeis (Admin, Coordenador, Docente, Tecnico)
Interface administrativa responsiva, usável em tablets e celulares
Suporte a busca textual em todo o conteúdo do portal
Paginação em todas as listagens com volume alto de itens
Imagens otimizadas automaticamente pelo Wagtail
URLs amigáveis (slugs) geradas automaticamente para cada página
Manutenção do historico de revisoes de cada pagina (recurso nativo do Wagtail)
Compatibilidade com as versões atuais dos principais navegadores

## Arquitetura de Modelos de Dados

### Snippet: AreaConhecimento
nome - CharField(100) — nome da area
slug - SlugField — gerado automaticamente

### Page: DocentePage
nome_completo - CharField(200)
foto - ForeignKey → Image (Wagtail)
email - EmailField
lattes_url - URLField (opcional)
orcid - CharField(20, opcional)
titulacao - CharField — choices (graduacao a pos-doutorado)
instituicao_titulacao - CharField(200)
areas_conhecimento - ManyToMany → AreaConhecimento
bio - RichTextField

### DisciplinaPage + Orderable: MaterialDisciplina
codigo - CharField(20) — ex: AGR-301
carga_horaria - PositiveIntegerField
periodo - PositiveSmallIntegerField (1 a 10)
ementa - RichTextField
docente_responsavel - ForeignKey → DocentePage (opcional)
materiais - InlinePanel → MaterialDisciplina

#### Campos do Orderable MaterialDisciplina
titulo - CharField(200)
tipo - choices: slides, pdf, video, link, planilha, outro
arquivo - ForeignKey → Document Wagtail (opcional)
url_externa - URLField (opcional)
descricao - TextField (opcional)
data_publicacao - DateField

### Page: ProjetoPage + Orderable: ProdutoProjeto
tipo - choices: pesquisa, extensao, ensino, TCC, PIBIC, PIBEX
resumo - TextField(250) — para cards de listagem
descricao - StreamField — blocos ricos
data_inicio - DateField
data_fim - DateField (opcional)
status - choices: em andamento, concluido, suspenso, submetido
coordenador - ForeignKey → DocentePage
participantes_docentes - ManyToMany → DocentePage
edital - ForeignKey → Document (opcional)
financiador - CharField(200, opcional)
tags - TaggableManager (django-taggit)
produtos - InlinePanel → ProdutoProjeto

### Page: PublicacaoPage
tipo - choices: artigo periodico, artigo anais, capitulo, livro, TCC, dissertacao, tese
resumo - TextField
corpo - StreamField — blocos ricos
autores_internos - ManyToMany → DocentePage
autores_externos - CharField(500) — nomes livres separados por virgula
veiculo - CharField(300) — nome da revista ou evento
doi - CharField(100, opcional)
issn - CharField(20, opcional)
arquivo_pdf - ForeignKey → Document (opcional)
url_acesso - URLField (opcional)
data_publicacao - DateField
tags - TaggableManager

### Page: PostPage
autor - ForeignKey → DocentePage
capa - ForeignKey → Image (opcional)
resumo - TextField(200) — para cards
corpo - StreamField: RichText, Image, Embed, Document
data_publicacao - DateField (automatico)
tags - TaggableManager

### DocumentoPage
tipo - choices: regulamento, formulario, edital, ata, resolucao, manual, outro
descricao - TextField (opcional)
arquivo - ForeignKey → Document Wagtail (obrigatorio)
data_publicacao - DateField
data_vigencia - DateField (opcional)
ativo - BooleanField (padrao: True)

### EventoPage
tipo - choices: seminario, defesa TCC, workshop, aula aberta, visita tecnica
descricao - RichTextField
data_inicio - DateTimeField
data_fim - DateTimeField (opcional)
local - CharField(300)
online - BooleanField
link_online - URLField (opcional)
docentes_envolvidos - ManyToMany → DocentePage
projeto_vinculado - ForeignKey → ProjetoPage (opcional)
tags - TaggableManager

### Mapa de relacionamentos
DocentePage - DisciplinaPage - ForeignKey (1:N) — docente responsavel
DocentePage - ProjetoPage - ForeignKey (1:N) — coordenador
DocentePage - ProjetoPage - ManyToMany — participante
DocentePage - PublicacaoPage - ManyToMany — autor interno
DocentePage - PostPage - ForeignKey (1:N) — autor
DocentePage - EventoPage - ManyToMany — envolvido
DocentePage - AreaConhecimento - ManyToMany — area de atuacao
DisciplinaPage - MaterialDisciplina - ParentalKey (1:N) — inline
ProjetoPage - ProdutoProjeto - ParentalKey (1:N) — inline
EventoPage - ProjetoPage - ForeignKey (N:1) — projeto vinculado

### Permissoes por papel de usuario
Administrador - Total — usuarios, grupos, configs - Todos os modelos e configuracoes
Coordenador - Publicar qualquer conteudo - Todos os Page types
Docente - Criar e editar o proprio conteudo - PostPage, PublicacaoPage, ProjetoPage (proprios)
Tecnico - Gestao institucional - DocumentoPage e EventoPage
Publico - Somente leitura - Nenhum (apenas visualizacao)

## Identidade Visual e Paleta de Cores

### Cores primarias — identidade institucional
Verde Escuro    #2D6636 - Cabecalho, botoes de acao principal, navegacao
Verde Base      #3A7D44 - Links ativos, icones, bordas de destaque
Verde Medio     #5AAB66 - Estados de hover, badges de status ativo
Verde Claro     #D4EDDA - Fundos de secao, tags, informativos verdes

### Cores secundarias — identidade do curso
Azul Noite      #122D52 - Sidebar, rodape, menus secundarios
Azul Escuro     #1A3C6E - Titulos de secao, enfase tipografica
Azul Medio      #2E6DB4 - Links secundarios, icones informativos
Azul Claro      #DBEAFE - Fundos de cards informativos, tags azuis

### Cores neutras e semanticas 
Cinza Esverdeado  #E8EDE9 - Fundo geral da pagina — tom de terra/campo
Quase Preto     #1A1A1A - Texto principal corrido
Cinza Texto     #4A5568 - Texto secundario, metadados, legendas
Vermelho IF     #C0392B - Alertas, notificacoes, erros — uso restrito

### Regras de aplicacao
Verde Escuro (#2D6636) e a cor primaria — deve aparecer no cabecalho e botoes de chamada para acao
Azul Escuro (#1A3C6E) e a cor de titulos — nunca compite com o verde em elementos interativos
O fundo geral (#E8EDE9) tem leve tom esverdeado para remeter ao contexto rural e agronomico
Vermelho (#C0392B) aparece exclusivamente em estados de erro, alerta e notificacao
Texto sobre fundo verde deve usar sempre branco (#FFFFFF)
Texto sobre fundo azul escuro deve usar sempre branco (#FFFFFF)
Cards e paineis usam sempre fundo branco (#FFFFFF) sobre o fundo cinza da pagina

## Tipografia
Fonte base - System font stack — compatibilidade maxima com servidores institucionais
Titulos H1 - Bold 2rem — cor Azul Escuro (#1A3C6E)
Titulos H2 - Bold 1.5rem — cor Verde Escuro (#2D6636)
Titulos H3 - Bold 1.2rem — cor Azul Escuro (#1A3C6E)
Texto corrido - Regular 1rem — cor #1A1A1A — line-height 1.7
Metadados - Regular 0.85rem — cor #4A5568
Badges e tags - Bold 0.7rem — cor dependente do contexto

## Ordem de Implementacao Sugerida

### Fase 1 — Fundacao (Semana 1-2)
Configuracao do ambiente Django + Wagtail + PostgreSQL
Criacao do app base/ com blocks.py e choices.py
Snippet AreaConhecimento
HomePage e estrutura da arvore de paginas

### Fase 2 — Pessoas e Ensino (Semana 3-4)
DocentePage + DocentesIndexPage (M01)
DisciplinaPage + MaterialDisciplina + DisciplinasIndexPage (M02)
Configuracao de grupos e permissoes por papel

### Fase 3 — Pesquisa e Publicacoes (Semana 5-6)
ProjetoPage + ProdutoProjeto + ProjetosIndexPage (M03)
PublicacaoPage + PublicacoesIndexPage (M04)

### Fase 4 — Conteudo e Institucional (Semana 7-8)
PostPage + PostsIndexPage (M05)
DocumentoPage + DocumentosIndexPage (M06)
EventoPage + EventosIndexPage (M07)

### Fase 5 — Refinamento e Producao (Semana 9-10)
Identidade visual — aplicacao da paleta de cores via CSS
Busca textual integrada (recurso nativo do Wagtail)
Ajustes no painel admin com base no feedback dos docentes
Configuracao do servidor de producao — Nginx + Gunicorn + SSL
Carga inicial de conteudo com os professores


**Última atualização:** 23 de maio de 2026
**Versão:** 3.0
