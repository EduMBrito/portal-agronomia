# INFRAESTRUTURA.md — o que o Portal Agronomia precisa do servidor

Documento de entrega para o projeto de infraestrutura do campus, que provisiona
o Proxmox e as instâncias compartilhadas. Escrito em **11 de setembro de 2026**
e revisado em **12 de setembro de 2026**, depois do primeiro retorno da
infraestrutura — o desenho mudou em três pontos: o Nginx passou a viver dentro
do stack, as imagens passaram a vir do GHCR, e os documentos passaram a ser
entregues por `X-Accel-Redirect`.

Os números marcados como **medido** vieram de execução real: imagem construída,
container subindo contra um PostgreSQL 16, conteúdo de exemplo carregado e 200
requisições nas páginas públicas. Os marcados como **estimado** são projeção e
devem ser tratados como tal.

---

## 1. Resumo — o que alocar

| Instância | O portal usa? | O que precisa |
|---|---|---|
| `pve-proxy` | **sim** | um subdomínio, TLS, três cabeçalhos obrigatórios |
| `pve-apps` | **sim** | 2 contêineres, ~2 GB RAM somados, ~25 GB disco, Docker |
| `pve-db` | **sim** | 1 database + 1 usuário, ~10 conexões |
| `pve-cache` | **não** | nada. Ver seção 6 |
| `pve-backup` | **sim** | 2 itens: o database e o volume de mídia |

O portal é uma aplicação pequena e sem estado, de leitura predominante. O
público são estudantes, docentes e servidores do campus, mais visitantes
externos eventuais. Não há pico previsível, a não ser em divulgação de edital.
Quem escreve é uma comissão de 3 a 5 pessoas.

---

## 2. Forma de entrega

**Duas** imagens Docker, construídas e publicadas pela CI no GHCR
(`ghcr.io/edumbrito/portal-agronomia-web` e `-nginx`), puxadas pelo servidor.

| | Base | Tamanho (medido) | O que faz |
|---|---|---|---|
| `-web` | `python:3.12-slim` | **469 MB** | Gunicorn WSGI, 3 workers sync, porta 8000 |
| `-nginx` | `nginx:1.27` | **299 MB** | serve estáticos, imagens e documentos; proxy para o Gunicorn |

Das 469 MB da aplicação, 205 MB são a camada base do `python:3.12-slim`, que o
servidor baixa uma vez e reaproveita em qualquer outra aplicação que use a mesma
base. O mesmo vale para os 284 MB do `nginx:1.27`.

- **Usuário da aplicação:** `portal`, UID 1000, **não-root** — precisa casar com
  o dono do bind mount de `media/`, senão o upload de imagem falha com permissão
  negada. O Nginx roda no seu próprio contêiner, onde a porta 80 não é
  privilegiada por estar noutro namespace de rede
- **Build:** na CI (GitHub Actions), nunca no servidor. O `pve-apps` é
  compartilhado: um `docker build` ali rouba CPU e disco das outras aplicações
  durante o deploy, e deixa um cache de build que só encolhe com
  `docker builder prune` rodado à mão
- **Versão:** a variável `PORTAL_TAG` no `.env` escolhe a etiqueta. A do sha
  curto nunca é reescrita — é o que torna o rollback uma troca de linha

---

## 3. `pve-proxy` — o que o proxy precisa fazer

### 3.1 Roteamento

Um subdomínio, todo o tráfego encaminhado para **`172.16.172.11:8001`**, que é
a porta publicada pelo contêiner de Nginx do portal — **não** direto para o
Gunicorn. A razão está em 4.2.

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

**Resolvido em 12/09/2026.** Fica com o portal: o Caddy não tem rate limiting
na distribuição padrão — só como plugin de terceiros, que exigiria recompilar
com `xcaddy` e manter um binário customizado. O `nginx.conf` já traz
`set_real_ip_from 172.16.172.10`, com `real_ip_recursive on`.

> **A conferir no primeiro acesso.** Com a porta publicada pelo Docker, a origem
> que chega ao contêiner pode ser o gateway da rede bridge em vez do IP do
> `pve-proxy`, dependendo do `userland-proxy`. Num teste em Docker Desktop o log
> registrou o gateway — mas ali *todo* tráfego passa pela VM, então não vale como
> prova para o Linux, onde o DNAT tende a preservar a origem de tráfego vindo de
> outro host.
>
> `docker compose logs nginx | tail` depois do primeiro acesso resolve a dúvida.
> Se for o gateway, ele entra numa segunda linha `set_real_ip_from`. Não deixamos
> uma faixa ampla por antecipação: confiar em `172.16.0.0/12` seria confiar em
> toda a rede do campus para forjar o cabeçalho.

### 3.4 Corpo da requisição

`client_max_body_size` (ou equivalente) de **20 MB**. A comissão sobe PDFs de
regulamentos e materiais de disciplina. O Django corta em 10 MB para dados de
formulário, mas upload de arquivo passa por outro caminho e precisa da folga.

### 3.5 O que o proxy **não** deve fazer

- **Não** servir `/static/` nem `/media/` diretamente. Esses diretórios vivem em
  `pve-apps`; montá-los no proxy cruzaria a fronteira entre instâncias sem
  necessidade
- **Não** encaminhar direto para o Gunicorn. Ele nem é publicado no host: só o
  contêiner de Nginx expõe porta. Ver 4.2

---

## 4. `pve-apps` — host de aplicação

### 4.1 Recursos

São dois contêineres, cada um com seu `mem_limit` fixado no
`docker-compose.prod.yml`. Num host compartilhado o teto não é zelo: sem ele, um
vazamento no portal derruba a VM inteira, junto com as outras aplicações.

| Contêiner | Medido em execução | Teto fixado |
|---|---|---|
| `web` (Gunicorn) | 203 MB em repouso · 214 MB após 200 requisições · **208–212 MB** com a pilha completa de pé | **1800 MB** |
| `nginx` | **9,5–12,6 MB** | **128 MB** |

| Outros recursos | Medido | Observação |
|---|---|---|
| CPU, em repouso | ~0,03% | picos curtos de 1 núcleo |
| Imagem `-web` | 469 MB | 205 MB são base compartilhada |
| Imagem `-nginx` | 299 MB | 284 MB são base compartilhada |
| `staticfiles/` | 13 MB | vai dentro da imagem, não em volume |
| `media/` (uploads) | 4 KB hoje | **20 GB** em 5 anos (estimado) |

O teto de 1800 MB é folga deliberada sobre os ~210 MB medidos: cobre o
processamento de imagem do Wagtail, que carrega o arquivo em memória ao gerar
renditions, e um eventual quarto worker. Não é consumo esperado, é limite — na
prática o `web` roda a 11% dele e o Nginx a 10% do seu.

> **Disco do `/var/lib/docker`.** Como o `pve-apps` vai hospedar outras
> aplicações, vale dimensionar pensando no conjunto. Imagens que partilham a
> mesma base a guardam uma vez só — por isso padronizamos `python:3.12-slim` e
> `nginx:1.27`. E como nada é construído no servidor, não há cache de build
> crescendo ali.

A estimativa de mídia é a única projeção relevante de crescimento: cerca de 60
disciplinas com material acumulando ao longo dos semestres, mais PDFs de
publicações e documentos institucionais. É o que cresce; o banco não.

### 4.2 O portal traz o próprio Nginx, dentro do stack

Isto é um requisito, não uma preferência. O Nginx é um serviço no
`docker-compose.prod.yml`, não um Nginx instalado no host: cada aplicação do
`pve-apps` publica a sua porta e se resolve sozinha. Dentro do contêiner a porta
80 não é privilegiada, porque é outro namespace de rede — não há conflito com o
usuário não-root da aplicação.

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
| `/documents/<id>/<nome>` | Gunicorn **checa**, Nginx **entrega** | ver 4.3 |
| `/_protegido/` | Nginx, `internal` | destino do `X-Accel-Redirect`; inalcançável de fora |
| resto | Gunicorn | |

Os documentos ficam fisicamente em `media/documents/`. Servir `/media/` como
alias contornaria a checagem de permissão: bastaria adivinhar o nome do arquivo
para baixar documento de coleção privada, regulamento já marcado como inativo,
ou um XML de currículo Lattes esquecido no diretório — que contém CPF, RG,
filiação e telefone.

A configuração está versionada em [`nginx.conf`](nginx.conf) e agora é também
insumo de build: o estágio `nginx` do `Dockerfile` a copia para dentro da
imagem, então não há cópia no servidor para editar à mão. Já reescrita para este
cenário — sem os blocos de TLS, que passaram a ser do `pve-proxy`, escutando
apenas HTTP na rede interna. Validada com `nginx -t` e com o comportamento
medido em contêiner.

### 4.3 Documento: o Wagtail checa, o Nginx entrega

A rota `/documents/<id>/<nome>` continua sendo do Wagtail, porque é onde a
permissão de coleção é verificada. Mas, depois de aprovar, ele não despeja o
arquivo pelo Python: devolve uma resposta vazia com `X-Accel-Redirect`, e o
Nginx entrega o arquivo do disco.

```
navegador → Nginx → Gunicorn  (checa a coleção, responde vazio + cabeçalho)
navegador ← Nginx ←            (Nginx lê /app/media e entrega)
```

Medido: `200`, bytes íntegros, `ETag` no formato do Nginx (mtime+tamanho em
hex), `Accept-Ranges: bytes` — e `302` para a tela de login quando o documento
está em coleção restrita. A checagem não se perdeu.

O destino é `location /_protegido/ { internal; alias /app/media/; }`, e
`internal` o torna inalcançável de fora: medido `404`.

> **Ressalva honesta sobre o ganho.** O motivo não é liberar worker preso: com
> `proxy_buffering` ligado, que é o padrão, o Nginx já drenava a resposta e
> alimentava o cliente lento sozinho. O ganho é não copiar o arquivo byte a byte
> pelo Python, e não gerar arquivo temporário em `/var/cache/nginx` — escrita no
> RAID-6 — para respostas grandes. Com estáticos, imagens e documentos saindo
> direto do Nginx, o que sobra para o Gunicorn é HTML de alguns KB, que cabe nos
> buffers de memória.

É implementação própria, em `apps/core/sendfile_nginx.py`, ~20 linhas, em vez de
somar o `django-sendfile2` ao `requirements.txt`. Coberta por quatro testes,
inclusive o de recusar caminho fora de `SENDFILE_ROOT`.

### 4.4 Volumes

| Caminho | Onde | Precisa persistir? | Backup? |
|---|---|---|---|
| `/app/media` | nos **dois** contêineres | **sim** | **sim** — único dado fora do git e do banco |
| `/app/staticfiles` | dentro da imagem | não é volume | não — vai assado na imagem |

O mesmo bind mount é montado duas vezes: o Gunicorn precisa **escrever**
(uploads do Wagtail), o Nginx só **ler** (`/media/images/` e o destino do
`X-Accel-Redirect`). Por isso o do Nginx é `:ro` — fecha a porta para ele servir
documento por engano.

### 4.5 Ordem de operações no deploy

```
1. docker compose pull
2. migrate                       (+ bootstrap_site e setup_grupos, em instalação nova)
3. docker compose up -d
```

**O `collectstatic` saiu do deploy.** Ele roda no build da imagem, na CI, e o
manifesto do `ManifestStaticFilesStorage` vai assado junto. Antes essa era a
armadilha do primeiro deploy: subir o Gunicorn antes do `collectstatic` quebrava
toda página com `ValueError: Missing staticfiles manifest entry for
'css/tailwind.css'`, e rodar o comando depois não resolvia sem reiniciar o
processo. Aconteceu na medição de 11/09. Agora não há ordem a errar — verificado
num contêiner novo, que resolveu `css/tailwind.css` para
`css/tailwind.0459d3b467c2.css` sem nunca ter rodado `collectstatic`.

`bootstrap_site` (monta a árvore de páginas) e `setup_grupos` (cria os grupos de
permissão) são idempotentes, como o resto.

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

Do ponto de vista do `shared_buffers` do `pve-db` — **12 GB**, corrigido pela
infraestrutura em 12/09/2026; a versão anterior deste documento repetia os 32 GB
de um rascunho, que provocariam picos de latência nos checkpoints sobre RAID-6 —
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

**Resolvido em 12/09/2026.** A rotina de `pg_dump` própria do portal foi
retirada do `DEPLOY.md`. O backup fica em duas camadas da infraestrutura: a
rotina centralizada no `pve-db`, que varre todos os databases, e o PBS cobrindo
as instâncias. Uma terceira rotina nossa criaria a pior situação — achar que
existe backup em dois lugares e não haver em nenhum.

Combinado que o dump e o job do PBS rodam com pouca distância entre si, e que
**uma defasagem de até uma hora é aceitável**, desde que registrada. Está no
[`DEPLOY.md`](DEPLOY.md), seção 10.

> **Pendência nossa, não da infra:** nunca fizemos um restore de teste. Backup
> que não foi restaurado é hipótese. Está registrado no `docs/SEGURANCA.md`.

---

## 8. Variáveis de ambiente

Todas obrigatórias, exceto onde indicado. O modelo está em `.env.example`.

| Variável | Observação |
|---|---|
| `SECRET_KEY` | 50+ caracteres aleatórios. A aplicação **não sobe** sem ela |
| `ALLOWED_HOSTS` | o subdomínio do portal **mais `localhost`**, separado por vírgula. Sem default |
| `WAGTAILADMIN_BASE_URL` | `https://<subdomínio>` — usado em e-mail e notificação |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | do database dedicado em `pve-db` |
| `DB_HOST`, `DB_PORT` | `172.16.172.12` e `5432` |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `PORTAL_TAG` | etiqueta das imagens no GHCR. Opcional, default `latest` |
| `SECURE_SSL_REDIRECT` | opcional, default `True`. Ver 3.2 antes de mexer |
| `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` | opcionais, default `True`. Ver abaixo |
| `GUNICORN_WORKERS` | opcional, default 3 |
| `DJANGO_LOG_LEVEL` | opcional, default `ERROR` |

> **`localhost` em `ALLOWED_HOSTS` não é opcional.** É o Host que o healthcheck
> do contêiner usa. Sem ele o Django responde 400, o serviço nunca fica saudável
> e o Nginx não chega a subir — ele espera `service_healthy`. Não abre nada: só
> vale para requisição originada dentro do contêiner.

> **Os três cookies/redirect, só na validação interna.** Os três têm default
> `True` e é assim que devem ficar em produção. Enquanto o Caddy encaminha em
> HTTP puro, antes do certificado, os três precisam ir a `False` — senão, além do
> laço de redirecionamento da seção 3.2, o cookie de CSRF não é setado e **o
> login do painel falha** com "CSRF verification failed". Foi a infraestrutura
> que levantou o primeiro; o segundo apareceu ao revisar o `production.py`.

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
4. ~~`collectstatic` roda antes do Gunicorn~~ — **resolvido**: o `collectstatic`
   passou para o build da imagem, e a ordem deixou de existir como risco
5. **Banco e `media/` são restaurados do mesmo momento**
6. **O `web` não publica porta.** Quem conversa com o `pve-proxy` é o contêiner
   de Nginx, na `172.16.172.11:8001`
7. **Os dois `mem_limit` continuam fixados.** Num host compartilhado é o que
   impede que um vazamento no portal derrube a VM das outras aplicações

---

## 10. Contato entre os dois projetos

### Recebido em 12/09/2026

| O que se pediu | Resposta |
|---|---|
| IP fixo do `pve-proxy` | `172.16.172.10`, e o rate limit fica **com o portal** — o Caddy não tem rate limiting na distribuição padrão |
| Database em `pve-db` | `172.16.172.12:5432`, database e usuário `portal_agronomia`, PostgreSQL 16.15, cluster em UTF8 / pt_BR.UTF-8 |
| Backup do database | Rotina centralizada no `pve-db` varrendo todos os databases, mais o PBS cobrindo as instâncias. O `pg_dump` do portal **sai** |
| Porta no `pve-apps` | `172.16.172.11:8001`, dentro da faixa 8000–8099 já liberada no UFW |
| Subdomínio | **pendente com a TI — é o bloqueio** |

### Entregue

- Duas imagens no GHCR, construídas pela CI a cada push na `main` e a cada tag
  `vX.Y.Z` — `ghcr.io/edumbrito/portal-agronomia-{web,nginx}`
- `docker-compose.prod.yml` sem `build:`, sem banco próprio, com os dois
  `mem_limit` e os dois healthchecks
- [`nginx.conf`](nginx.conf) para HTTP interno, sem TLS, com
  `set_real_ip_from 172.16.172.10` e o `location internal` do `X-Accel-Redirect`
- [`DEPLOY.md`](DEPLOY.md) reescrito para este desenho, com rollback por
  etiqueta e sem a rotina de `pg_dump`

### Ainda em aberto

- **O subdomínio.** Sem ele não se fecha `ALLOWED_HOSTS` nem
  `WAGTAILADMIN_BASE_URL`. Dá para validar internamente pelo IP, mas **nenhum
  conteúdo real deve entrar antes** — toda URL absoluta gerada nessa fase nasce
  apontando para um endereço que morre depois
- **Quanto de disco tem o `/var/lib/docker` do `pve-apps`**, já que ele vai
  guardar as imagens de todas as aplicações
- **Confirmar que o `media/` do portal fica em volume separado** da raiz do
  Docker
- **Restore de teste.** Pendência nossa: nunca foi feito
