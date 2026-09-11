FROM python:3.12-slim

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
# os bind mounts de ./media e ./staticfiles em produção pertencem a ele. Se o
# usuário do servidor tiver outro UID, ajustar aqui, senão o upload de imagem e
# o collectstatic falham com permissão negada.
RUN groupadd --gid 1000 portal \
    && useradd --uid 1000 --gid 1000 --create-home portal

# Copia o restante do projeto
COPY --chown=portal:portal . .

# Diretórios escritos em tempo de execução: uploads do Wagtail e collectstatic.
RUN mkdir -p /app/media /app/staticfiles && chown portal:portal /app/media /app/staticfiles

USER portal

# Porta que o Django vai expor
EXPOSE 8000

# Gunicorn como padrão, não o runserver: se alguém subir esta imagem sem o
# `command` do compose, é melhor que caia num servidor de produção do que num
# servidor de desenvolvimento com autoreload. O docker-compose.yml sobrescreve
# com o runserver para o ambiente local.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
