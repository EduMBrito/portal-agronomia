"""Entrega de documentos pelo Nginx, via ``X-Accel-Redirect``.

O Wagtail checa a permissão de coleção em ``/documents/<id>/<nome>`` e chama
``wagtail.utils.sendfile``, que importa o módulo apontado por
``SENDFILE_BACKEND`` e delega a entrega a ele. Este módulo devolve uma resposta
vazia com o cabeçalho ``X-Accel-Redirect``: o Nginx intercepta, entrega o
arquivo ele mesmo, e o worker do Gunicorn é liberado sem copiar o arquivo byte
a byte pelo Python.

A checagem de permissão continua acontecendo — ela é anterior a este ponto. O
``location`` de destino é ``internal`` no Nginx, então ninguém chega nele
digitando a URL.

É uma alternativa ao ``django-sendfile2``. Vinte linhas próprias custam menos
manutenção, para um mantenedor único, do que mais uma dependência no
``requirements.txt``.
"""

from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse


def sendfile(request, filename, **kwargs):
    """Responde vazio, com ``X-Accel-Redirect`` apontando para o arquivo.

    Args:
        request: a requisição em curso; não é usada, mas faz parte do contrato
            que o ``wagtail.utils.sendfile`` espera do backend.
        filename: caminho absoluto do arquivo no sistema de arquivos, como o
            Wagtail o entrega. Precisa estar sob ``SENDFILE_ROOT``.
        **kwargs: ``mimetype`` e afins, que o Wagtail reescreve na resposta
            depois de nós; ignorados aqui de propósito.

    Returns:
        HttpResponse: corpo vazio. Quem preenche é o Nginx.

    Raises:
        ImproperlyConfigured: se o arquivo estiver fora de ``SENDFILE_ROOT``.
            Seria configuração errada, não entrada de usuário — melhor falhar
            alto do que devolver um caminho que o Nginx não sabe servir.
    """
    raiz = Path(settings.SENDFILE_ROOT).resolve()
    caminho = Path(filename).resolve()

    try:
        relativo = caminho.relative_to(raiz)
    except ValueError as erro:
        raise ImproperlyConfigured(
            f"{caminho} está fora de SENDFILE_ROOT ({raiz}): o Nginx não tem "
            f"location que alcance esse caminho."
        ) from erro

    resposta = HttpResponse()
    resposta["X-Accel-Redirect"] = quote(f"{settings.SENDFILE_URL.rstrip('/')}/{relativo}")
    return resposta
