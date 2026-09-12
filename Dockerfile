# ---------------------------------------------------------------------------
# Estágio `app` — a aplicação Django servida por Gunicorn
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS app

# Sem gcc nem os -dev de libpq, libjpeg e zlib: psycopg2-binary e Pillow são
# distribuídos como wheels manylinux já compilados, então nada é construído
# aqui. Tirar o compilador da imagem de produção reduz a superfície de ataque e
# encolhe a imagem. Se um dia entrar uma dependência que precise compilar, o
# caminho é um estágio de build separado — não devolver o gcc à imagem final.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências Python primeiro (aproveita cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Usuário sem privilégio: uma falha de execução remota no app não vira root no
# container. UID 1000 de propósito — é o primeiro usuário não-root do Ubuntu, e
# o bind mount de ./media em produção pertence a ele. Se o usuário do servidor
# tiver outro UID, ajustar aqui, senão o upload de imagem falha com permissão
# negada.
RUN groupadd --gid 1000 portal \
    && useradd --uid 1000 --gid 1000 --create-home portal

# Copia o restante do projeto
COPY --chown=portal:portal . .

# media/ é escrito em tempo de execução (uploads do Wagtail); staticfiles/ é
# escrito logo abaixo, no build. Os dois são criados aqui para já nascerem com
# o dono certo, antes do USER.
RUN mkdir -p /app/media /app/staticfiles && chown portal:portal /app/media /app/staticfiles

USER portal

# Estáticos assados na imagem, não gerados no servidor.
#
# O ManifestStaticFilesStorage lê, ao iniciar, um manifesto que o collectstatic
# escreve. Gerando aqui, o manifesto vira parte da imagem e a ordem de
# operações do deploy deixa de importar: não há mais como o Gunicorn subir
# antes do collectstatic e derrubar todas as páginas com "Missing staticfiles
# manifest entry", que era o erro mais provável do primeiro deploy.
#
# As três variáveis são falsas e valem só para este RUN. O collectstatic não
# abre conexão com o banco nem resolve host nenhum; elas existem porque o
# settings de produção exige as três para ser importado.
RUN DJANGO_SETTINGS_MODULE=config.settings.production \
    SECRET_KEY=apenas-para-o-build-nao-e-segredo \
    ALLOWED_HOSTS=localhost \
    WAGTAILADMIN_BASE_URL=http://localhost \
    python manage.py collectstatic --noinput --clear

# Porta que o Django vai expor
EXPOSE 8000

# Gunicorn como padrão, não o runserver: se alguém subir esta imagem sem o
# `command` do compose, é melhor que caia num servidor de produção do que num
# servidor de desenvolvimento com autoreload. O docker-compose.yml sobrescreve
# com o runserver para o ambiente local.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]


# ---------------------------------------------------------------------------
# Estágio `nginx` — serve estáticos e imagens, faz proxy para o Gunicorn
# ---------------------------------------------------------------------------
#
# O Nginx passa a viver dentro do stack, e não mais no host: o pve-apps hospeda
# várias aplicações, e cada uma publica uma porta própria. Dentro do container
# a porta 80 não é privilegiada — é outro namespace de rede — então o usuário
# não-root do estágio `app` não conflita com isso.
#
# Imagem Debian e não Alpine, para acompanhar o python:3.12-slim e não
# introduzir uma segunda distro no projeto.
FROM nginx:1.27 AS nginx

# Os estáticos vêm prontos do estágio da aplicação: mesma origem, mesmo
# manifesto, nenhum volume compartilhado e nada gerado em tempo de execução.
COPY --from=app /app/staticfiles /app/staticfiles

# conf.d/*.conf é incluído dentro do http{} pela imagem oficial, que é onde o
# limit_req_zone precisa estar. O arquivo entra inteiro, sem separar.
COPY docs/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
