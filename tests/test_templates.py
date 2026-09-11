"""Renderiza de ponta a ponta todas as páginas públicas.

O resto da suíte exercita `get_context`, que nunca toca no template. Isso deixou
passar dois erros 500 que só apareciam no navegador: um `{% load %}` de uma
biblioteca de tags inexistente e uma página sem template — os dois corrigidos
em setembro de 2026.

Estes testes pedem a URL pelo client do Django, então o template é compilado e
renderizado de verdade.
"""

import datetime

import pytest
from django.core.files.base import ContentFile
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


@pytest.fixture
def documento(documentos_index):
    arquivo = get_document_model().objects.create(
        title="Regulamento",
        file=ContentFile(b"%PDF-1.4 conteudo de teste", name="regulamento-teste.pdf"),
    )
    return documentos_index.add_child(instance=DocumentoPage(
        title="Regulamento do Curso",
        slug="regulamento-do-curso",
        tipo="regulamento",
        arquivo=arquivo,
        data_publicacao=datetime.date(2026, 1, 1),
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


def test_documento_redireciona_para_o_arquivo(documento):
    """DocumentoPage não tem página de detalhe: entrega o PDF direto."""
    resposta = Client().get(documento.url)

    assert resposta.status_code == 302
    assert resposta.headers["Location"] == documento.arquivo.url


def test_documento_redireciona_temporariamente(documento):
    """302 e não 301: o destino muda quando a comissão troca o arquivo."""
    resposta = Client().get(documento.url)

    assert resposta.status_code == 302
    assert not resposta.headers.get("Cache-Control", "").startswith("max-age")


def test_url_do_documento_sobrevive_a_troca_do_arquivo(documento):
    """É o motivo de a página existir: link citável que aponta sempre à versão vigente."""
    url_da_pagina = documento.url
    url_antiga = documento.arquivo.url

    documento.arquivo = get_document_model().objects.create(
        title="Regulamento v2",
        file=ContentFile(b"%PDF-1.4 versao nova", name="regulamento-v2.pdf"),
    )
    documento.save()

    resposta = Client().get(url_da_pagina)
    assert resposta.status_code == 302
    assert resposta.headers["Location"] != url_antiga
    assert resposta.headers["Location"] == documento.arquivo.url


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
