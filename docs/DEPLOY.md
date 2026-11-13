# DEPLOY.md — Portal Agronomia IFSertãoPE

Instalação e atualização no servidor compartilhado do campus.

**Em produção desde 13/11/2026** em
<https://portalagronomia.zonarural.ifsertao-pe.edu.br> — por enquanto só no DNS
interno do campus; o acesso externo vem depois.

O portal roda em `pve-apps` como duas imagens construídas pela CI: a aplicação
(Gunicorn) e o Nginx que serve estáticos, imagens e documentos. O banco é o
PostgreSQL compartilhado em `pve-db`, e quem termina o TLS é o Caddy do
`pve-proxy`.

O que cada instância precisa fornecer está em
[`INFRAESTRUTURA.md`](INFRAESTRUTURA.md) — este arquivo é o passo a passo.

> **Nada é construído no servidor.** O `pve-apps` hospeda outras aplicações do
> campus; um `docker build` ali rouba CPU e disco de todas elas durante o
> deploy, num Xeon de 2010 com disco mecânico. O caminho de emergência, para
> quando o GHCR estiver inalcançável, está na seção 8.

---

## 1. Pré-requisitos

Fornecido pela infraestrutura:

| Item | Valor |
|---|---|
| Instância de aplicação | `pve-apps` (`172.16.172.11`), Ubuntu Server 24.04 LTS, Docker Engine e Compose v2, já autenticado no GHCR |
| Banco | `pve-db` — `172.16.172.12:5432`, database e usuário `portal_agronomia` (UTF8, pt_BR.UTF-8) |
| Proxy | Caddy em `pve-proxy` (`172.16.172.10`), certificado curinga da RNP para `*.zonarural.ifsertao-pe.edu.br`, encaminhando para `172.16.172.11:8001` com `Host`, `X-Forwarded-For` e `X-Forwarded-Proto` |
| Firewall | `pve-apps` aceita 8000–8099 só vindo de `172.16.172.10` |
| Saída para a internet | necessária no `pve-apps`, para alcançar `ghcr.io` |

As imagens são `ghcr.io/edumbrito/portal-agronomia-web` e
`ghcr.io/edumbrito/portal-agronomia-nginx`, linux/amd64, em pacotes **privados**:
o `pve-apps` precisa de um token com `read:packages`. Se o `pull` responder
`denied`, é o token; se responder `not found`, é a etiqueta.

---

## 2. O diretório no servidor

O servidor **não tem clone do repositório**. O stack vive em
`/opt/stacks/portal-agronomia` e contém só três coisas:

```
/opt/stacks/portal-agronomia/
├── docker-compose.yml   ← cópia do docker-compose.prod.yml do repositório
├── .env                 ← segredos, chmod 600, nunca versionado
└── media/               ← uploads da comissão, dono UID 1000
```

O Compose chega por `scp`, **renomeado** para `docker-compose.yml`. É isso que
permite rodar todos os comandos sem `-f`. Do Mac, a partir da `main` atualizada:

```bash
git switch main && git pull --ff-only
scp docker-compose.prod.yml \
  brito@172.16.172.11:/opt/stacks/portal-agronomia/docker-compose.yml
```

> **Não copie o `docker-compose.yml` da raiz.** É o de desenvolvimento: sobe um
> Postgres próprio, faz `build:` local e não publica a porta 8001.

O diretório de mídia precisa pertencer ao **UID 1000**, que é o usuário
`portal` dentro do container. Se não casar, o upload de imagem falha com
permissão negada:

```bash
mkdir -p /opt/stacks/portal-agronomia/media
sudo chown -R 1000:1000 /opt/stacks/portal-agronomia/media
```

---

## 3. Variáveis de ambiente

O `.env` é criado **no próprio servidor**, com `nano`, para que os segredos não
trafeguem. O [`.env.example`](../.env.example) explica cada campo.

```env
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<50+ caracteres aleatórios>

ALLOWED_HOSTS=portalagronomia.zonarural.ifsertao-pe.edu.br,localhost
WAGTAILADMIN_BASE_URL=https://portalagronomia.zonarural.ifsertao-pe.edu.br
WAGTAIL_SITE_NAME=Portal Agronomia IFSertãoPE

DB_NAME=portal_agronomia
DB_USER=portal_agronomia
DB_PASSWORD=<no gerenciador de senhas>
DB_HOST=172.16.172.12
DB_PORT=5432

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

PORTAL_TAG=<vX.Y.Z ou sha curto de 12 caracteres>
```

```bash
cd /opt/stacks/portal-agronomia
nano .env && chmod 600 .env
python3 -c "import secrets; print(secrets.token_urlsafe(60))"   # SECRET_KEY
docker compose config --quiet                                   # valida arquivo e interpolação
```

> **`PORTAL_TAG` é obrigatória.** Sem ela o Compose recusa subir com
> "required variable PORTAL_TAG is missing a value". Não use `latest` nem
> `main`: mudam de conteúdo sem aviso. A etiqueta de sha curto, publicada a cada
> push na `main`, aparece no log do job "Imagens no GHCR" da CI.

> **`localhost` em `ALLOWED_HOSTS` não é opcional.** É o Host que o healthcheck
> do container usa. Sem ele o Django responde 400, o serviço nunca fica
> saudável e o Nginx não chega a subir — ele espera `service_healthy`.

> **`$` em segredo.** O Compose lê o `.env` também para interpolação. Se a
> senha do banco tiver `$`, ponha o valor entre aspas simples.

---

## 4. Primeira instalação

A ordem importa. O `collectstatic` **não** aparece aqui: os estáticos já vêm
assados na imagem, gerados durante o build da CI.

```bash
cd /opt/stacks/portal-agronomia

docker compose pull

docker compose run --rm web python manage.py migrate --noinput
docker compose run --rm web python manage.py bootstrap_site
docker compose run --rm web python manage.py setup_grupos
docker compose run --rm web python manage.py createsuperuser

docker compose up -d
docker compose ps        # os dois devem ficar "healthy"
```

> **`bootstrap_site`** cria a HomePage, aponta o Site do Wagtail para ela,
> remove a página "Welcome to your new Wagtail site!" e monta as sete seções com
> os slugs que o menu do topo espera. **`setup_grupos`** cria os grupos de
> permissão. Os dois são idempotentes. **Nenhum dos dois cria usuário** — daí o
> `createsuperuser`.

> **Não rode `populate_content` em produção.** Ele carrega docentes, projetos e
> publicações fictícios, feitos para demonstração.

O healthcheck do Nginx atravessa Nginx → Gunicorn → banco. Se ele passa, o
caminho que o `pve-proxy` usa está inteiro.

### Depois da subida

**Hostname do Site.** O `bootstrap_site` deixa o Site como `localhost:80`. Em
`/admin/sites/`, troque para:

| Campo | Valor |
|---|---|
| Hostname | `portalagronomia.zonarural.ifsertao-pe.edu.br` |
| Port | **`443`** |
| Is default site | marcado |

A porta é 443, e não 80, porque o Wagtail monta o `root_url` a partir dela: com
80 o sitemap e os links de e-mail sairiam em `http://`.

**Login no painel.** Entrar em `/admin/` pelo domínio valida de uma vez os
cookies `Secure` e o CSRF por HTTPS.

**IP real do cliente.** Depois de abrir algumas páginas pelo domínio:

```bash
docker compose logs nginx --since 5m | grep -v healthz | tail -5
```

O primeiro campo de cada linha tem de ser o IP da sua máquina, não
`172.16.172.10` nem um gateway `172.17.x.1`/`172.18.x.1` do Docker. Se for um
gateway, o limite de tentativas de login passa a valer para todo mundo num
balde só — ver o comentário do `set_real_ip_from` em [`nginx.conf`](nginx.conf).
O `nginx.conf` vai dentro da imagem: a correção passa pelo repositório e pela
CI, nunca por edição no servidor.

> **Verificado em 13/11/2026:** o Nginx registra o IP real do cliente. A linha
> única `set_real_ip_from 172.16.172.10` basta com a publicação de porta atual.

---

## 5. Atualizações

No Mac, só se o `docker-compose.prod.yml` mudou na versão nova:

```bash
git switch main && git pull --ff-only
scp docker-compose.prod.yml \
  brito@172.16.172.11:/opt/stacks/portal-agronomia/docker-compose.yml
```

No servidor:

```bash
cd /opt/stacks/portal-agronomia
nano .env                     # PORTAL_TAG=<nova etiqueta>

docker compose pull
docker compose run --rm web python manage.py migrate --noinput
docker compose up -d
docker compose ps
```

---

## 6. Rollback

Trocar `PORTAL_TAG` no `.env` pela etiqueta anterior e repetir `pull` + `up -d`.
A etiqueta de sha curto nunca é reescrita.

> **Rollback de imagem não desfaz migração.** Se a versão que você está
> abandonando aplicou uma migração destrutiva, voltar a imagem deixa o código
> velho contra um banco novo. Nesse caso o caminho é restaurar o banco do
> backup, não só trocar a etiqueta. Vale conferir o que a migração fez antes de
> decidir.

---

## 7. Logs e diagnóstico

```bash
docker compose logs -f web      # Gunicorn e Django
docker compose logs -f nginx    # acessos e erros
docker compose ps               # saúde dos dois
docker stats portal_agronomia_web portal_agronomia_nginx   # memória contra o teto
```

Nenhum log é escrito em disco pela aplicação: tudo vai para stdout e stderr, e o
Docker captura.

| Sintoma | Causa provável |
|---|---|
| `required variable PORTAL_TAG is missing a value` | falta `PORTAL_TAG` no `.env` |
| `pull` com `not found` | etiqueta inexistente no GHCR |
| `pull` com `denied` | token do servidor sem acesso aos pacotes |
| `web` nunca fica `healthy` | banco inalcançável, ou `localhost` fora do `ALLOWED_HOSTS` |
| Laço de redirecionamento | o `X-Forwarded-Proto: https` não está chegando do Caddy |
| "CSRF verification failed" no login | acesso por HTTP com os cookies `Secure` |

---

## 8. Emergência — sem GHCR

Se o registry estiver inalcançável e for preciso subir mesmo assim, dá para
construir no servidor com os nomes que o Compose espera. **É exceção**, não
procedimento: gasta CPU e disco compartilhados com as outras aplicações.

Como o servidor não tem clone, o código vem num checkout temporário, **fora**
do diretório do stack:

```bash
git clone --depth 1 https://github.com/EduMBrito/portal-agronomia.git /tmp/portal-build
cd /tmp/portal-build
docker build --target app   -t ghcr.io/edumbrito/portal-agronomia-web:emergencia .
docker build --target nginx -t ghcr.io/edumbrito/portal-agronomia-nginx:emergencia .
cd / && rm -rf /tmp/portal-build

cd /opt/stacks/portal-agronomia
# PORTAL_TAG=emergencia no .env, depois up -d
docker builder prune      # não deixar o cache de build ocupando disco
```

Se o GitHub também estiver fora, o código pode ir do Mac por `scp` de um
`git archive`.

---

## 9. Backup

**A rotina de `pg_dump` própria do portal foi retirada.** O backup é
responsabilidade da infraestrutura, em duas camadas: a rotina centralizada no
`pve-db`, que varre todos os databases, e o Proxmox Backup Server cobrindo as
instâncias. Manter uma terceira rotina aqui criaria a pior situação possível —
achar que existe backup em dois lugares e não haver em nenhum.

Três coisas precisam estar cobertas, e só elas:

| Item | Onde |
|---|---|
| Database `portal_agronomia` | `pve-db` |
| Volume `media/` | `pve-apps`, em `/opt/stacks/portal-agronomia/media` |
| `.env` | `pve-apps`, em `/opt/stacks/portal-agronomia/.env` — ou os segredos no gerenciador de senhas |

O que **não** precisa: as imagens (reconstruíveis pela CI), o `staticfiles/`
(vai dentro da imagem), o código (está no GitHub) e o `docker-compose.yml`
(cópia do repositório).

### A janela entre os dois

O banco guarda a referência ao documento, não o arquivo. Restaurar só o banco
deixa o portal num estado ruim e silencioso: as páginas carregam e cada link de
documento dá erro ao baixar.

Combinado com a infraestrutura: o dump do `pve-db` e o job do PBS rodam com
pouca distância entre si, e **uma defasagem de até uma hora é aceitável** —
desde que esteja escrita, que é o propósito deste parágrafo.

> **Pendência nossa, não da infra:** nunca fizemos um restore de teste. Backup
> que não foi restaurado é hipótese. Está registrado no
> [`SEGURANCA.md`](SEGURANCA.md).
