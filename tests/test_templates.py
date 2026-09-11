"""Renderiza de ponta a ponta todas as páginas públicas.

O resto da suíte exercita `get_context`, que nunca toca no template. Isso deixou
passar dois erros 500 que só apareciam no navegador: um `{% load %}` de uma
biblioteca de tags inexistente e uma página sem template.

Estes testes pedem a URL pelo client do Django, então o template é compilado e
renderizado de verdade.
"""

import datetime

import pytest
from django.core.files.base import ContentFile
from django.template.exceptions import TemplateDoesNotExist
from django.test import Client
from wagtail.documents import get_document_model

from apps.institucional.models import DocumentoPage, DocumentosIndexPage

pytestmark = pytest.mark.django_db


@pytest.fixture
def documentos_index(home_page):
    return home_page.add_child(instance=DocumentosIndexPage(
        title="Documentos",
        slug="test-documentos",
        live=True,
    ))


# ---------------------------------------------------------------------------
# Listagens
# ---------------------------------------------------------------------------

def test_home_renderiza(home_page):
    assert Client().get(home_page.url).status_code == 200


@pytest.mark.parametrize("nome_do_index", [
    "docentes_index",
    "disciplinas_index",
    "projetos_index",
    "publicacoes_index",
    "posts_index",
    "eventos_index",
    "documentos_index",
])
def test_listagem_renderiza(request, nome_do_index):
    index = request.getfixturevalue(nome_do_index)

    assert Client().get(index.url).status_code == 200


@pytest.mark.parametrize("querystring", [
    "?area=fitotecnia",
    "?periodo=1",
    "?tipo=pesquisa",
    "?status=em_andamento",
    "?tipo=pesquisa&status=em_andamento",
    "?page=99",          # página fora do intervalo cai na última, não quebra
    "?tipo=<script>",    # valor inválido não pode derrubar a listagem
])
def test_listagem_com_filtro_renderiza(projetos_index, projeto_pesquisa, querystring):
    assert Client().get(projetos_index.url + querystring).status_code == 200


# ---------------------------------------------------------------------------
# Páginas de detalhe
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nome_da_pagina", [
    "docente_com_area",
    "disciplina_p1",
    "projeto_pesquisa",
    "publicacao_artigo",
    "post_recente",
    "evento_futuro",
])
def test_detalhe_renderiza(request, nome_da_pagina):
    """Pega `{% load %}` de biblioteca inexistente, que só estoura na compilação."""
    pagina = request.getfixturevalue(nome_da_pagina)

    assert Client().get(pagina.url).status_code == 200


@pytest.mark.xfail(
    raises=TemplateDoesNotExist,
    strict=True,
    reason=(
        "DocumentoPage tem URL pública mas não tem institucional/documento_page.html."
        " Toda página de documento publicada responde 500. Quando o template existir"
        " (ou a página deixar de ser navegável), remover este xfail."
    ),
)
def test_detalhe_documento_renderiza(documentos_index):
    arquivo = get_document_model().objects.create(
        title="Regulamento",
        file=ContentFile(b"%PDF-1.4 conteudo de teste", name="regulamento-teste.pdf"),
    )
    pagina = documentos_index.add_child(instance=DocumentoPage(
        title="Regulamento do Curso",
        slug="regulamento-do-curso",
        tipo="regulamento",
        arquivo=arquivo,
        data_publicacao=datetime.date(2026, 1, 1),
        live=True,
    ))

    assert Client().get(pagina.url).status_code == 200


# ---------------------------------------------------------------------------
# Busca e páginas avulsas
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("querystring", ["", "?q=", "?q=sorgo", "?q=<script>alert(1)</script>"])
def test_busca_renderiza(home_page, querystring):
    assert Client().get(f"/busca/{querystring}").status_code == 200


def test_busca_escapa_o_termo_pesquisado(home_page):
    """O termo volta para a página em três lugares — nenhum pode sair cru."""
    resposta = Client().get("/busca/?q=<script>alert(1)</script>")
    corpo = resposta.content.decode()

    assert "<script>alert(1)</script>" not in corpo
    assert "&lt;script&gt;" in corpo


def test_sobre_renderiza(home_page):
    assert Client().get("/sobre/").status_code == 200
