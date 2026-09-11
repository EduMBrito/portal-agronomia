# DEPLOY.md — Portal Agronomia IFSertãoPE

## Pré-requisitos do Servidor

- Ubuntu Server 22.04 LTS
- Docker Engine 24+ e Docker Compose v2
- Git
- Nginx (instalado no host, fora do Docker)
- Certificado SSL (Let's Encrypt ou institucional)
- Porta 80 e 443 abertas no firewall
- Mínimo 1 GB RAM, 10 GB disco

## 1. Instalação do Docker

```bash
# Dependências
sudo apt update && sudo apt install -y ca-certificates curl gnupg

# Repositório oficial Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list

sudo apt update && sudo apt install -y docker-ce docker-ce-cli docker-compose-plugin

# Adicionar usuário ao grupo docker (evita sudo)
sudo usermod -aG docker $USER
newgrp docker
```

## 2. Clone e Configuração

```bash
cd /opt
sudo git clone https://github.com/<org>/portal-agronomia.git
sudo chown -R $USER:$USER portal-agronomia
cd portal-agronomia
```

## 3. Variáveis de Ambiente

Copie o exemplo e edite com valores reais:

```bash
cp .env.example .env
nano .env
```

Valores obrigatórios em produção:

```env
SECRET_KEY=<chave-longa-aleatória-mínimo-50-chars>
DEBUG=False
ALLOWED_HOSTS=portal.agronomia.ifsertao.edu.br,www.portal.agronomia.ifsertao.edu.br
DB_NAME=portal_agronomia
DB_USER=postgres
DB_PASSWORD=<senha-forte>
DB_HOST=db
DB_PORT=5432
WAGTAIL_SITE_NAME=Portal Agronomia IFSertãoPE
WAGTAILADMIN_BASE_URL=https://portal.agronomia.ifsertao.edu.br
DEFAULT_FROM_EMAIL=noreply@ifsertao.edu.br
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

Gere uma SECRET_KEY segura:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(60))"
```

## 4. Docker Compose para Produção

Crie `docker-compose.prod.yml`:

```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: portal_agronomia_db
    restart: always
    env_file: .env
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    build: .
    container_name: portal_agronomia_web
    restart: always
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.production
    volumes:
      - media_data:/app/media
      - static_data:/app/staticfiles
    ports:
      - "127.0.0.1:8000:8000"   # apenas loopback — Nginx faz o proxy
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
  media_data:
  static_data:
```

## 5. Build e Inicialização

```bash
# Build da imagem
docker compose -f docker-compose.prod.yml build

# Subir serviços em background
docker compose -f docker-compose.prod.yml up -d

# Aplicar migrações
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Montar a árvore de páginas (HomePage + as 7 seções)
docker compose -f docker-compose.prod.yml exec web python manage.py bootstrap_site

# Coletar arquivos estáticos
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Criar superusuário
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Configurar grupos e permissões
docker compose -f docker-compose.prod.yml exec web python manage.py setup_grupos
```

> **`bootstrap_site`:** obrigatório em uma instalação nova. Cria a HomePage, aponta
> o Site do Wagtail para ela, remove a página padrão "Welcome to your new Wagtail
> site!" e cria as sete seções com os slugs que o menu do topo espera. É
> idempotente — reexecutar em um portal já povoado não altera nada.

> **Não rode `populate_content` em produção.** Ele carrega docentes, projetos e
> publicações fictícios, feitos para demonstração.

> **Hostname do Site:** o `bootstrap_site` não mexe no hostname. Em
> `/admin/sites/`, troque `localhost:80` pelo domínio real do campus — o Wagtail
> usa esse valor para gerar URLs absolutas (e-mails de notificação, sitemap).

> **Tailwind:** nada a fazer no servidor. O CSS já vem compilado e versionado em
> `static/css/tailwind.css`; o `collectstatic` acima o coleta junto com o resto.
> O campus não precisa de Node, npm nem acesso a CDN para o portal renderizar.
> Se alterar algum template, rode `./scripts/build-css.sh` na sua máquina e
> commite o CSS regenerado **antes** de fazer o deploy.

## 6. Nginx

Instale o Nginx no host (não no Docker):

```bash
sudo apt install -y nginx
```

O arquivo de configuração está versionado em [`nginx.conf`](nginx.conf) — é a
fonte única, não copie o conteúdo para cá. Ele já traz o bloqueio de `/media/`
para tudo que não seja imagem, o limite de tentativas na tela de login e o
`ssl_protocols`.

```bash
sudo cp docs/nginx.conf /etc/nginx/sites-available/portal-agronomia
sudo nano /etc/nginx/sites-available/portal-agronomia   # trocar server_name e caminhos
```

Três coisas precisam bater com o servidor antes de ativar:

| No arquivo | Trocar por |
|---|---|
| `server_name portal.agronomia.ifsertao.edu.br` | o hostname real |
| `/opt/portal-agronomia/` | o diretório onde o projeto foi clonado |
| caminhos do `ssl_certificate` | onde o Certbot ou o CTI deixou o certificado |

> **Não transformar `/media/` num alias único de novo.** Os documentos ficam em
> `media/documents/` e a permissão de coleção é checada na rota `/documents/`
> do Wagtail. Servir o diretório inteiro contorna essa checagem — era o
> comportamento antigo e está registrado como item 2 do
> [`SEGURANCA.md`](SEGURANCA.md).

Ative e reinicie:

```bash
sudo ln -s /etc/nginx/sites-available/portal-agronomia /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 7. Certificado SSL (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d portal.agronomia.ifsertao.edu.br
```

O Certbot configura a renovação automática. Verifique:

```bash
sudo certbot renew --dry-run
```

## 8. Atualizações

```bash
cd /opt/portal-agronomia

# Puxar novas versões
git pull origin main

# Rebuild e reiniciar
docker compose -f docker-compose.prod.yml build web
docker compose -f docker-compose.prod.yml up -d web

# Aplicar migrações e coletar estáticos se houver mudanças
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## 9. Monitoramento e Logs

```bash
# Logs em tempo real
docker compose -f docker-compose.prod.yml logs -f web

# Status dos containers
docker compose -f docker-compose.prod.yml ps

# Uso de recursos
docker stats
```

## 10. Backup Automatizado

Adicione ao crontab (`crontab -e`):

```cron
# Backup diário às 2h
0 2 * * * docker compose -f /opt/portal-agronomia/docker-compose.prod.yml exec -T db \
  pg_dump -U postgres portal_agronomia | gzip > /opt/backups/portal_$(date +\%Y\%m\%d).sql.gz

# Manter apenas últimos 30 dias
0 3 * * * find /opt/backups -name "portal_*.sql.gz" -mtime +30 -delete
```

```bash
sudo mkdir -p /opt/backups
```
