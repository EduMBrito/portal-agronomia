# INFRAESTRUTURA.md — o que o Portal Agronomia precisa do servidor

Documento de entrega para o projeto de infraestrutura do campus, que provisiona
o Proxmox e as instâncias compartilhadas. Escrito em **11 de setembro de 2026**
contra o commit `ef71ee6`.

Os números marcados como **medido** vieram de execução real: imagem construída,
container subindo contra um PostgreSQL 16, conteúdo de exemplo carregado e 200
requisições nas páginas públicas. Os marcados como **estimado** são projeção e
devem ser tratados como tal.

---

## 1. Resumo — o que alocar

| Instância | O portal usa? | O que precisa |
|---|---|---|
| `pve-proxy` | **sim** | um subdomínio, TLS, três cabeçalhos obrigatórios |
| `pve-apps` | **sim** | ~2 GB RAM, ~25 GB disco, Docker |
| `pve-db` | **sim** | 1 database + 1 usuário, ~10 conexões |
| `pve-cache` | **não** | nada. Ver seção 6 |
| `pve-backup` | **sim** | 2 itens: o database e o volume de mídia |

O portal é uma aplicação pequena e sem estado, de leitura predominante. O
público são estudantes, docentes e servidores do campus, mais visitantes
externos eventuais. Não há pico previsível, a não ser em divulgação de edital.
Quem escreve é uma comissão de 3 a 5 pessoas.

---

## 2. Forma de entrega

Imagem Docker construída a partir do repositório, servida por Gunicorn.

- **Imagem:** `python:3.12-slim` + dependências, **871 MB** (medido)
- **Processo:** Gunicorn WSGI, 3 workers sync, porta 8000
- **Usuário:** `portal`, UID 1000, **não-root** — precisa casar com o dono dos
  bind mounts, senão upload de imagem e `collectstatic` falham com permissão
  negada
- **Build:** no CI (GitHub Actions), nunca no servidor — o processador de 2010
  não deve gastar ciclo compilando

---

## 3. `pve-proxy` — o que o proxy precisa fazer

### 3.1 Roteamento

Um subdomínio, todo o tráfego encaminhado para a porta **80 do Nginx do portal**
em `pve-apps` — **não** direto para o Gunicorn. A razão está em 4.2.

### 3.2 Cabeçalhos obrigatórios

```
X-Forwarded-Proto: https
X-Forwarded-For:   <ip real do cliente>
Host:              <host original>
```

**`X-Forwarded-Proto` não é opcional.** O portal roda com `SECURE_SSL_REDIRECT`
ligado e `SECURE_PROXY_SSL_HEADER` configurado. Sem esse cabeçalho, o Django não
sabe que a conexão original era HTTPS e responde 301 para `https://`, o proxy
recebe de novo, encaminha de novo em HTTP, e assim por diante — **laço infinito
de redirecionamento**.

Comportamento medido:

| Requisição | Resposta |
|---|---|
| sem `X-Forwarded-Proto` | `301 → https://...` (o laço) |
| com `X-Forwarded-Proto: https` | `200` |

O Caddy envia os três por padrão. O Traefik envia, mas confira se há
`forwardedHeaders.trustedIPs` restringindo.

### 3.3 `X-Forwarded-For` e o limite de tentativas de login

O portal limita tentativas na tela de login pelo IP de origem, no próprio
Nginx (`docs/nginx.conf`). Atrás do proxy central, o Nginx do portal enxerga o
IP **do proxy**, não o do cliente — o que faria toda a internet compartilhar um
único balde de 5 tentativas por minuto e **um atacante trancaria a comissão
inteira para fora**.

Duas saídas, e basta uma:

1. O proxy envia `X-Forwarded-For` e o Nginx do portal ganha
   `set_real_ip_from <ip-do-pve-proxy>; real_ip_header X-Forwarded-For;`.
   É a nossa parte, e depende apenas de saber o IP fixo do `pve-proxy`
2. O limite passa a ser responsabilidade do proxy central, aplicado em
   `/admin/login/` deste subdomínio, e o do portal é removido

**Preferência:** a segunda, se o proxy central já tiver política de rate limit
padronizada para todas as aplicações do campus — um lugar só para ajustar. A
primeira funciona e já está escrita e testada; só falta o IP.

> **Requisito para o projeto de infra:** informar o IP fixo do `pve-proxy`, ou
> confirmar que o rate limit fica centralizado.

### 3.4 Corpo da requisição

`client_max_body_size` (ou equivalente) de **20 MB**. A comissão sobe PDFs de
regulamentos e materiais de disciplina. O Django corta em 10 MB para dados de
formulário, mas upload de arquivo passa por outro caminho e precisa da folga.

### 3.5 O que o proxy **não** deve fazer

- **Não** servir `/static/` nem `/media/` diretamente. Esses diretórios vivem em
  `pve-apps`; montá-los no proxy cruzaria a fronteira entre instâncias sem
  necessidade
- **Não** encaminhar direto para o Gunicorn na porta 8000. Ver 4.2

---

## 4. `pve-apps` — host de aplicação

### 4.1 Recursos

| Recurso | Medido | Recomendado |
|---|---|---|
| RAM, em repouso | 203 MB | **2 GB** de teto |
| RAM, após 200 requisições | 214 MB | |
| CPU, em repouso | ~0,03% | picos curtos de 1 núcleo |
| Imagem Docker | 871 MB | |
| `staticfiles/` | 13 MB | |
| `media/` (uploads) | 4 KB hoje | **20 GB** em 5 anos (estimado) |

Os 2 GB de teto são folga deliberada sobre os 214 MB medidos: cobrem o
processamento de imagem do Wagtail, que carrega o arquivo em memória ao gerar
renditions, e um eventual quarto worker. Não é consumo esperado, é limite.

A estimativa de mídia é a única projeção relevante de crescimento: cerca de 60
disciplinas com material acumulando ao longo dos semestres, mais PDFs de
publicações e documentos institucionais. É o que cresce; o banco não.

### 4.2 O portal traz o próprio Nginx

Isto é um requisito, não uma preferência.

Em produção o Django **não serve arquivo estático nem mídia**. Medido, com
`DEBUG=False`:

```
GET /static/css/tailwind.css  ->  404
GET /media/qualquer.pdf       ->  404
```

Então alguém tem de servir. E esse alguém não pode ser um alias simples de
`/media/`, porque a regra de permissão dos documentos depende de **não** servir
o diretório inteiro:

| Rota | Quem serve | Por quê |
|---|---|---|
| `/static/` | Nginx do portal | cache longo, nome com hash |
| `/media/images/`, `/media/original_images/` | Nginx do portal | públicas por natureza |
| **todo o resto de `/media/`** | **ninguém — 404** | ver abaixo |
| `/documents/<id>/<nome>` | Gunicorn | é a rota do Wagtail que **checa a permissão de coleção** |
| resto | Gunicorn | |

Os documentos ficam fisicamente em `media/documents/`. Servir `/media/` como
alias contornaria a checagem de permissão: bastaria adivinhar o nome do arquivo
para baixar documento de coleção privada, regulamento já marcado como inativo,
ou um XML de currículo Lattes esquecido no diretório — que contém CPF, RG,
filiação e telefone.

A configuração está versionada em [`nginx.conf`](nginx.conf), validada com
`nginx -t` e com o comportamento medido em container. Para este cenário ela
perde os blocos de TLS, que passam a ser do `pve-proxy`, e passa a escutar
apenas HTTP na rede interna.

### 4.3 Volumes

| Caminho no container | Precisa persistir? | Backup? |
|---|---|---|
| `/app/media` | **sim** | **sim** — é o único dado que não está no git nem no banco |
| `/app/staticfiles` | não | não — regerado por `collectstatic` |

### 4.4 Ordem de operações no deploy

Esta ordem importa, e errar dá 500 em todas as páginas:

```
1. migrate
2. collectstatic          <- ANTES de subir o Gunicorn
3. gunicorn
```

O portal usa `ManifestStaticFilesStorage`, que lê um manifesto gerado pelo
`collectstatic` na inicialização. Se o Gunicorn subir antes, toda página quebra
com `ValueError: Missing staticfiles manifest entry for 'css/tailwind.css'` — e
rodar o `collectstatic` depois não resolve sem reiniciar o processo.

Foi exatamente o que aconteceu na medição, e é o erro mais provável do primeiro
deploy.

Em instalação nova, mais dois comandos idempotentes depois do `migrate`:
`bootstrap_site` (monta a árvore de páginas) e `setup_grupos` (cria os grupos de
permissão).

---

## 5. `pve-db` — PostgreSQL compartilhado

### 5.1 O que provisionar

- **1 database** e **1 usuário** dedicados, sem compartilhar schema com outra
  aplicação. É regra do campus e também da nossa arquitetura
- **PostgreSQL 15 ou superior.** Testado contra o 16
- Sem extensão nenhuma. O portal usa a busca textual nativa do Wagtail, que é
  SQL comum — não precisa de `pg_trgm` nem `unaccent`
- Acesso pela rede a partir de `pve-apps`: `listen_addresses` e `pg_hba.conf`
  liberando o IP da instância de aplicação

### 5.2 Conexões

**5 conexões simultâneas** (medido, com 3 workers e `CONN_MAX_AGE = 60`). As
conexões são persistentes por 60 segundos, então ficam em `idle` entre
requisições — é esperado e proposital, evita reabrir conexão a cada requisição.

**Reservar 10** no `max_connections` do servidor compartilhado, cobrindo os
comandos de manutenção e uma eventual subida de worker.

### 5.3 Tamanho

| | Medido |
|---|---|
| Database com 34 páginas de exemplo | **13 MB** |
| Soma das tabelas do portal | ~1,2 MB |

A diferença é o piso do PostgreSQL: um database vazio já ocupa cerca de 12 MB de
catálogo. **Os dados do portal são o 1,2 MB.**

Projeção: com o conteúdo real do curso — cerca de 30 docentes, 60 disciplinas,
algumas centenas de publicações e projetos — o database fica **abaixo de 500 MB
por vários anos** (estimado). As maiores tabelas são o índice de busca do
Wagtail e o histórico de revisões de página.

Do ponto de vista do `shared_buffers` de 32 GB descrito no projeto de infra,
este portal é ruído: cabe inteiro em cache e praticamente não gera I/O. O
dimensionamento do `pve-db` é justificado pelas outras aplicações, não por esta.

---

## 6. `pve-cache` — o portal não usa

**Nenhum requisito hoje.** Não há Redis, Celery, fila ou tarefa assíncrona no
projeto, e a sessão usa o backend de banco do Django.

A regra do projeto é explícita: Redis só com necessidade demonstrada. Cada peça
de infraestrutura é dívida de manutenção para um mantenedor único.

Três coisas mudariam isso, e nenhuma está no horizonte imediato:

1. A **rotina de colheita ORCID + CrossRef**, que é a próxima funcionalidade
   planejada, chama uma API externa. Se ela crescer a ponto de precisar rodar em
   segundo plano em vez de por comando manual, entra Celery — e aí entra Redis
2. Cache de página, se o número de acessos justificar. Não justifica hoje
3. Sessão em Redis, se houver mais de uma instância da aplicação. Só uma está
   prevista

Não alocar nada por antecipação. Quando for o caso, será um pedido explícito
com o problema medido junto.

---

## 7. `pve-backup` — o que salvar

Duas coisas, e só elas:

| Item | Onde | Por quê |
|---|---|---|
| **Database** | `pve-db` | conteúdo do portal, histórico de revisões, usuários |
| **Volume `media/`** | `pve-apps` | PDFs e imagens enviados pela comissão — **não estão no git nem no banco** |

O que **não** precisa de backup, porque é reconstruível:

- A imagem Docker — reconstruída do repositório
- `staticfiles/` — regerado por `collectstatic`
- O código — está no GitHub, público

### Ponto de atenção

Perder o `media/` e manter o banco deixa o portal num estado ruim mas silencioso:
as páginas continuam carregando, e cada link de documento dá erro ao baixar. O
banco guarda a referência, não o arquivo. **Os dois precisam ser restaurados do
mesmo momento**, ou a comissão vai caçar arquivos um a um.

O `docs/DEPLOY.md` traz uma rotina de `pg_dump` própria do portal, que passa a
ser redundante se o Proxmox Backup Server cobrir a instância inteira. Definir
qual das duas vale, para não manter duas rotinas — a pior situação é achar que
existe backup em dois lugares e não haver em nenhum.

> **Pendência nossa, não da infra:** nunca fizemos um restore de teste. Backup
> que não foi restaurado é hipótese. Está registrado no `docs/SEGURANCA.md`.

---

## 8. Variáveis de ambiente

Todas obrigatórias, exceto onde indicado. O modelo está em `.env.example`.

| Variável | Observação |
|---|---|
| `SECRET_KEY` | 50+ caracteres aleatórios. A aplicação **não sobe** sem ela |
| `ALLOWED_HOSTS` | o subdomínio do portal, separado por vírgula. Sem default |
| `WAGTAILADMIN_BASE_URL` | `https://<subdomínio>` — usado em e-mail e notificação |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | do database dedicado em `pve-db` |
| `DB_HOST`, `DB_PORT` | endereço de `pve-db` |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `SECURE_SSL_REDIRECT` | opcional, default `True`. Ver 3.2 antes de mexer |
| `GUNICORN_WORKERS` | opcional, default 3 |
| `DJANGO_LOG_LEVEL` | opcional, default `ERROR` |

O arquivo `.env` no servidor precisa de `chmod 600` e dono do serviço.

Logs vão para stdout e stderr, capturados pelo Docker. Nenhum arquivo de log é
escrito em disco pela aplicação.

---

## 9. O que não pode se perder na migração

Resumo do que este documento pede que sobreviva ao desenho novo. Cada item está
detalhado acima e registrado em `docs/SEGURANCA.md`:

1. **`/media/` não volta a ser alias único.** É o que separa documento público
   de documento restrito
2. **`X-Forwarded-Proto` chega ao Django**, ou o portal entra em laço de
   redirecionamento
3. **O IP real do cliente chega ao limitador de login**, ou o limite tranca a
   comissão em vez do atacante
4. **`collectstatic` roda antes do Gunicorn**
5. **Banco e `media/` são restaurados do mesmo momento**

---

## 10. Contato entre os dois projetos

O que precisamos receber do projeto de infraestrutura:

- IP fixo do `pve-proxy` (para o `set_real_ip_from`), **ou** confirmação de que
  o rate limit de login fica centralizado no proxy
- Subdomínio definitivo
- Endereço, porta e credenciais do database em `pve-db`
- Confirmação de qual camada faz o backup do database: o `pg_dump` do portal ou
  o Proxmox Backup Server

O que entregamos:

- Imagem Docker construída pelo CI
- `docs/nginx.conf` adaptado para HTTP interno, sem os blocos de TLS
- `docs/DEPLOY.md` com o passo a passo, a ser revisado para este desenho
