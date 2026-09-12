# DEPLOY.md — Portal Agronomia IFSertãoPE

Instalação e atualização no servidor compartilhado do campus.

O portal roda em `pve-apps` como duas imagens construídas pela CI: a aplicação
(Gunicorn) e o Nginx que serve estáticos, imagens e documentos. O banco é o
PostgreSQL compartilhado em `pve-db`, e quem termina o TLS é o Caddy do
`pve-proxy`.

O que cada instância precisa fornecer está em
[`INFRAESTRUTURA.md`](INFRAESTRUTURA.md) — este arquivo é o passo a passo.

> **Nada é construído no servidor.** O `pve-apps` hospeda outras aplicações do
> campus; um `docker build` ali rouba CPU e disco de todas elas durante o
> deploy, num Xeon de 2010 com disco mecânico. O caminho de emergência, para
> quando o GHCR estiver inalcançável, está na seção 9.

---

## 1. Pré-requisitos

Fornecido pela infraestrutura:

| Item | Valor |
|---|---|
| Instância de aplicação | `pve-apps`, Ubuntu Server 22.04 LTS, Docker Engine 24+ e Compose v2 |
| Banco | `pve-db` — `172.16.172.12:5432`, database e usuário `portal_agronomia` |
| Proxy | Caddy em `pve-proxy` (`172.16.172.10`), encaminhando para `172.16.172.11:8001` |
| Saída para a internet | necessária no `pve-apps`, para alcançar `ghcr.io` |

Do nosso lado, só o que está neste repositório.

---

## 2. Preparar o diretório no servidor

O clone serve **apenas** para ter o `docker-compose.prod.yml` versionado. Nada
é construído a partir dele.

```bash
sudo mkdir -p /opt/stacks
sudo git clone https://github.com/EduMBrito/portal-agronomia.git \
  /opt/stacks/portal-agronomia
sudo chown -R $USER:$USER /opt/stacks/portal-agronomia
cd /opt/stacks/portal-agronomia
```

O diretório de mídia precisa pertencer ao **UID 1000**, que é o usuário
`portal` dentro do container. Se não casar, o upload de imagem falha com
permissão negada:

```bash
mkdir -p media
sudo chown -R 1000:1000 media
id -u            # normalmente 1000 — se for, dá para usar rsync sem sudo
```

---

## 3. Variáveis de ambiente

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

O `.env.example` explica cada campo. Os que não têm default e travam a subida:

```env
SECRET_KEY=<50+ caracteres aleatórios>
ALLOWED_HOSTS=<subdomínio>,localhost
WAGTAILADMIN_BASE_URL=https://<subdomínio>
DB_NAME=portal_agronomia
DB_USER=portal_agronomia
DB_PASSWORD=<no gerenciador de senhas>
DB_HOST=172.16.172.12
DB_PORT=5432
PORTAL_TAG=latest
```

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(60))"   # SECRET_KEY
```

> **`localhost` em `ALLOWED_HOSTS` não é opcional.** É o Host que o healthcheck
> do container usa. Sem ele o Django responde 400, o serviço nunca fica
> saudável e o Nginx não chega a subir — ele espera `service_healthy`.

---

## 4. Primeira instalação

A ordem importa. O `collectstatic` **não** aparece aqui: os estáticos já vêm
assados na imagem, gerados durante o build da CI.

```bash
cd /opt/stacks/portal-agronomia

docker compose -f docker-compose.prod.yml pull

docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml run --rm web python manage.py bootstrap_site
docker compose -f docker-compose.prod.yml run --rm web python manage.py setup_grupos

docker compose -f docker-compose.prod.yml up -d

docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

> **`bootstrap_site`** cria a HomePage, aponta o Site do Wagtail para ela,
> remove a página "Welcome to your new Wagtail site!" e monta as sete seções com
> os slugs que o menu do topo espera. **`setup_grupos`** cria os grupos de
> permissão. Os dois são idempotentes: reexecutar num portal povoado não altera
> nada.

> **Não rode `populate_content` em produção.** Ele carrega docentes, projetos e
> publicações fictícios, feitos para demonstração.

> **Hostname do Site.** O `bootstrap_site` não mexe nisso. Em `/admin/sites/`,
> troque `localhost:80` pelo subdomínio real — o Wagtail usa esse valor para
> gerar URLs absolutas em e-mails de notificação e no sitemap.

> **Tailwind: nada a fazer no servidor.** O CSS vai compilado e versionado em
> `static/css/tailwind.css`, e a CI confere se está em dia com os templates. O
> campus não precisa de Node, npm nem CDN. Se alterar um template, rode
> `./scripts/build-css.sh` na sua máquina e commite o CSS regenerado.

Confirme que os dois containers ficaram saudáveis:

```bash
docker compose -f docker-compose.prod.yml ps
```

O healthcheck do Nginx atravessa Nginx → Gunicorn → banco. Se ele passa, o
caminho que o `pve-proxy` usa está inteiro.

---

## 5. Validação interna, antes do subdomínio

Enquanto a TI não define o subdomínio e não há certificado, dá para validar o
portal pelo IP. Três ajustes temporários no `.env`:

```env
ALLOWED_HOSTS=172.16.172.10,localhost
WAGTAILADMIN_BASE_URL=http://172.16.172.10

SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

Os três últimos têm default `True` e precisam voltar ao default assim que o
certificado existir. Sem eles em `False`, duas coisas acontecem em HTTP puro: o
Django responde 301 para `https://` e o Caddy devolve a requisição em HTTP,
criando um laço; e o cookie de CSRF não é setado, então **o login do painel
falha** com "CSRF verification failed".

> **Não carregue conteúdo real nesta fase.** O `WAGTAILADMIN_BASE_URL` fica com
> o IP, e toda URL absoluta gerada agora — e-mail de notificação, sitemap —
> nasce apontando para um endereço que morre quando o domínio existir.

---

## 6. Atualizações

```bash
cd /opt/stacks/portal-agronomia
git pull origin main          # só para o docker-compose.prod.yml

# Fixe a versão no .env, ou deixe `latest` para a última tag vX.Y.Z publicada
nano .env                     # PORTAL_TAG=v0.5.0

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml up -d
```

---

## 7. Rollback

Trocar `PORTAL_TAG` no `.env` e repetir `pull` + `up -d`. A etiqueta de sha
curto que a CI publica nunca é reescrita, ao contrário de `latest` e `main`:

```env
PORTAL_TAG=235fb52abc12
```

> **Rollback de imagem não desfaz migração.** Se a versão que você está
> abandonando aplicou uma migração destrutiva, voltar a imagem deixa o código
> velho contra um banco novo. Nesse caso o caminho é restaurar o banco do
> backup, não só trocar a etiqueta. Vale conferir o que a migração fez antes de
> decidir.

---

## 8. Logs e diagnóstico

```bash
docker compose -f docker-compose.prod.yml logs -f web      # Gunicorn e Django
docker compose -f docker-compose.prod.yml logs -f nginx    # acessos e erros
docker compose -f docker-compose.prod.yml ps               # saúde dos dois
docker stats portal_agronomia_web portal_agronomia_nginx   # memória contra o teto
```

Nenhum log é escrito em disco pela aplicação: tudo vai para stdout e stderr, e o
Docker captura.

**Conferir o IP real do cliente.** No primeiro acesso vindo do `pve-proxy`, veja
o que o Nginx registrou:

```bash
docker compose -f docker-compose.prod.yml logs nginx | tail
```

Se aparecer um `172.x` que não seja `172.16.172.10`, é o gateway da rede bridge
do Docker, e ele precisa entrar numa segunda linha `set_real_ip_from` em
[`nginx.conf`](nginx.conf) — senão o limite de tentativas de login passa a valer
para a internet inteira somada, num balde só.

---

## 9. Emergência — sem GHCR

Se o registry estiver inalcançável e for preciso subir mesmo assim, dá para
construir no servidor com os nomes que o Compose espera. **É exceção**, não
procedimento: gasta CPU e disco compartilhados com as outras aplicações.

```bash
docker build --target app   -t ghcr.io/edumbrito/portal-agronomia-web:emergencia .
docker build --target nginx -t ghcr.io/edumbrito/portal-agronomia-nginx:emergencia .
# PORTAL_TAG=emergencia no .env, depois up -d
```

Isso exige o código-fonte completo no servidor — o clone da seção 2 já serve.
Depois, `docker builder prune` para não deixar o cache de build ocupando disco.

---

## 10. Backup

**A rotina de `pg_dump` própria do portal foi retirada.** O backup é
responsabilidade da infraestrutura, em duas camadas: a rotina centralizada no
`pve-db`, que varre todos os databases, e o Proxmox Backup Server cobrindo as
instâncias. Manter uma terceira rotina aqui criaria a pior situação possível —
achar que existe backup em dois lugares e não haver em nenhum.

Duas coisas precisam estar cobertas, e só elas:

| Item | Onde |
|---|---|
| Database `portal_agronomia` | `pve-db` |
| Volume `media/` | `pve-apps`, em `/opt/stacks/portal-agronomia/media` |

O que **não** precisa: as imagens (reconstruíveis pela CI), o `staticfiles/`
(vai dentro da imagem) e o código (está no GitHub).

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
