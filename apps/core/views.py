from django.core.paginator import Paginator
from django.shortcuts import render
from wagtail.models import Page


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
