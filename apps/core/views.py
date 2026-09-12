from django.core.paginator import Paginator
from django.db import OperationalError, connection
from django.http import HttpResponse
from django.shortcuts import render
from wagtail.models import Page


def healthz(request):
    """Sinal de saúde para o healthcheck do Docker.

    Responde 200 se o processo está de pé e o banco responde, e 503 se o banco
    não responde — o que é a falha que importa aqui, já que o PostgreSQL vive
    noutra instância e a rede entre as duas pode cair sozinha.

    O corpo é uma palavra de propósito: a rota não exige autenticação, então
    não pode devolver versão, configuração nem mensagem de erro do banco.
    """
    try:
        connection.ensure_connection()
    except OperationalError:
        return HttpResponse("sem banco\n", status=503, content_type="text/plain")

    return HttpResponse("ok\n", content_type="text/plain")


def sobre(request):
    return render(request, "core/sobre.html")


def busca(request):
    query = request.GET.get("q", "").strip()
    results = Page.objects.none()
    if query:
        results = Page.objects.live().specific().search(query)
    paginator = Paginator(results, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    return render(request, "core/busca.html", {
        "query": query,
        "page_obj": page_obj,
    })
