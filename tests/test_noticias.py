import datetime

import pytest
from django.db.models import ProtectedError

from tests.conftest import _make_post

# ---------------------------------------------------------------------------
# Page: PostsIndexPage.get_context
# ---------------------------------------------------------------------------

def test_posts_index_sem_posts_retorna_lista_vazia(rf, posts_index):
    request = rf.get("/noticias/")
    context = posts_index.get_context(request)
    assert list(context["page_obj"].object_list) == []


def test_posts_index_lista_posts_publicados(
    rf, posts_index, post_recente, post_antigo
):
    request = rf.get("/noticias/")
    context = posts_index.get_context(request)
    ids = [p.pk for p in context["page_obj"].object_list]

    assert post_recente.pk in ids
    assert post_antigo.pk in ids


def test_posts_index_nao_lista_post_nao_publicado(
    rf, posts_index, docente, post_recente
):
    rascunho = _make_post(
        posts_index, "post-rascunho", "Post Rascunho", docente, live=False,
    )
    request = rf.get("/noticias/")
    context = posts_index.get_context(request)
    ids = [p.pk for p in context["page_obj"].object_list]

    assert post_recente.pk in ids
    assert rascunho.pk not in ids


def test_posts_index_ordena_por_data_publicacao_decrescente(
    rf, posts_index, post_antigo, post_recente
):
    request = rf.get("/noticias/")
    context = posts_index.get_context(request)
    lista = list(context["page_obj"].object_list)

    assert [p.pk for p in lista] == [post_recente.pk, post_antigo.pk]


def test_posts_index_pagina_de_nove_em_nove(rf, posts_index, docente):
    for i in range(11):
        _make_post(
            posts_index, f"post-{i}", f"Post {i}", docente,
            datetime.date(2025, 1, 1) + datetime.timedelta(days=i),
        )
    context = posts_index.get_context(rf.get("/noticias/"))
    assert len(context["page_obj"].object_list) == 9

    context = posts_index.get_context(rf.get("/noticias/?page=2"))
    assert len(context["page_obj"].object_list) == 2


def test_posts_index_page_fora_do_intervalo_devolve_ultima_pagina(
    rf, posts_index, post_recente
):
    """Paginator.get_page não levanta 404 — devolve a última página válida."""
    context = posts_index.get_context(rf.get("/noticias/?page=99"))
    assert context["page_obj"].number == 1


# ---------------------------------------------------------------------------
# Model: PostPage
# ---------------------------------------------------------------------------

def test_post_recebe_data_publicacao_automatica(posts_index, docente):
    """data_publicacao é auto_now_add — preenchida sem intervenção do docente."""
    post = _make_post(posts_index, "post-auto", "Post Automático", docente)
    assert post.data_publicacao == datetime.date.today()


def test_post_protege_autor_contra_exclusao(docente, post_recente):
    """autor é on_delete=PROTECT: docente com post não pode ser apagado."""
    with pytest.raises(ProtectedError):
        docente.delete()


def test_docente_expoe_posts_de_que_e_autor(docente, post_recente):
    assert post_recente.pk in [p.pk for p in docente.posts.live()]
