import datetime

import pytest
from django.db.models import ProtectedError

from apps.base.choices import STATUS_PROJETO_CHOICES, TIPO_PROJETO_CHOICES
from tests.conftest import _make_projeto, _make_publicacao

# ---------------------------------------------------------------------------
# Page: ProjetosIndexPage.get_context
# ---------------------------------------------------------------------------

def test_projetos_index_sem_filtro_retorna_todos(
    rf, projetos_index, projeto_pesquisa, projeto_extensao
):
    request = rf.get("/projetos/")
    context = projetos_index.get_context(request)
    ids = [p.pk for p in context["page_obj"].object_list]

    assert projeto_pesquisa.pk in ids
    assert projeto_extensao.pk in ids


def test_projetos_index_filtro_por_tipo_exclui_outros_tipos(
    rf, projetos_index, projeto_pesquisa, projeto_extensao
):
    request = rf.get("/projetos/?tipo=pesquisa")
    context = projetos_index.get_context(request)
    ids = [p.pk for p in context["page_obj"].object_list]

    assert projeto_pesquisa.pk in ids
    assert projeto_extensao.pk not in ids


def test_projetos_index_filtro_por_status_exclui_outros_status(
    rf, projetos_index, projeto_pesquisa, projeto_extensao
):
    request = rf.get("/projetos/?status=concluido")
    context = projetos_index.get_context(request)
    ids = [p.pk for p in context["page_obj"].object_list]

    assert projeto_extensao.pk in ids
    assert projeto_pesquisa.pk not in ids


def test_projetos_index_filtros_tipo_e_status_sao_cumulativos(
    rf, projetos_index, projeto_pesquisa, projeto_extensao
):
    # combinação que não casa com nenhum projeto: pesquisa E concluído
    request = rf.get("/projetos/?tipo=pesquisa&status=concluido")
    context = projetos_index.get_context(request)
    assert list(context["page_obj"].object_list) == []


def test_projetos_index_ordena_por_data_inicio_decrescente(
    rf, projetos_index, projeto_extensao, projeto_pesquisa
):
    request = rf.get("/projetos/")
    context = projetos_index.get_context(request)
    datas = [p.data_inicio for p in context["page_obj"].object_list]

    assert datas == sorted(datas, reverse=True)


def test_projetos_index_nao_lista_projeto_nao_publicado(
    rf, projetos_index, docente, projeto_pesquisa
):
    rascunho = _make_projeto(
        projetos_index, "proj-rascunho", "Projeto Rascunho",
        "pesquisa", "em_andamento", docente, live=False,
    )
    request = rf.get("/projetos/")
    context = projetos_index.get_context(request)
    ids = [p.pk for p in context["page_obj"].object_list]

    assert projeto_pesquisa.pk in ids
    assert rascunho.pk not in ids


def test_projetos_index_selecionados_no_context(rf, projetos_index):
    request = rf.get("/projetos/?tipo=extensao&status=suspenso")
    context = projetos_index.get_context(request)

    assert context["tipo_selecionado"] == "extensao"
    assert context["status_selecionado"] == "suspenso"


def test_projetos_index_sem_filtro_selecionados_sao_none(rf, projetos_index):
    request = rf.get("/projetos/")
    context = projetos_index.get_context(request)

    assert context["tipo_selecionado"] is None
    assert context["status_selecionado"] is None


def test_projetos_index_opcoes_de_filtro_no_context(rf, projetos_index):
    request = rf.get("/projetos/")
    context = projetos_index.get_context(request)

    assert context["tipos"] == TIPO_PROJETO_CHOICES
    assert context["status_opcoes"] == STATUS_PROJETO_CHOICES


def test_projetos_index_pagina_de_nove_em_nove(rf, projetos_index, docente):
    for i in range(11):
        _make_projeto(
            projetos_index, f"proj-{i}", f"Projeto {i}",
            "pesquisa", "em_andamento", docente,
            datetime.date(2025, 1, 1) + datetime.timedelta(days=i),
        )
    context = projetos_index.get_context(rf.get("/projetos/"))
    assert len(context["page_obj"].object_list) == 9

    context = projetos_index.get_context(rf.get("/projetos/?page=2"))
    assert len(context["page_obj"].object_list) == 2


# ---------------------------------------------------------------------------
# Page: PublicacoesIndexPage.get_context
# ---------------------------------------------------------------------------

def test_publicacoes_index_sem_filtro_retorna_todas(
    rf, publicacoes_index, publicacao_artigo, publicacao_tese
):
    request = rf.get("/publicacoes/")
    context = publicacoes_index.get_context(request)
    ids = [p.pk for p in context["page_obj"].object_list]

    assert publicacao_artigo.pk in ids
    assert publicacao_tese.pk in ids


def test_publicacoes_index_filtro_por_tipo_exclui_outros_tipos(
    rf, publicacoes_index, publicacao_artigo, publicacao_tese
):
    request = rf.get("/publicacoes/?tipo=tese")
    context = publicacoes_index.get_context(request)
    ids = [p.pk for p in context["page_obj"].object_list]

    assert publicacao_tese.pk in ids
    assert publicacao_artigo.pk not in ids


def test_publicacoes_index_ordena_por_data_publicacao_decrescente(
    rf, publicacoes_index, publicacao_tese, publicacao_artigo
):
    request = rf.get("/publicacoes/")
    context = publicacoes_index.get_context(request)
    datas = [p.data_publicacao for p in context["page_obj"].object_list]

    assert datas == sorted(datas, reverse=True)


def test_publicacoes_index_nao_lista_publicacao_nao_publicada(
    rf, publicacoes_index, publicacao_artigo
):
    rascunho = _make_publicacao(
        publicacoes_index, "pub-rascunho", "Publicação Rascunho",
        "livro", datetime.date(2026, 1, 1), live=False,
    )
    request = rf.get("/publicacoes/")
    context = publicacoes_index.get_context(request)
    ids = [p.pk for p in context["page_obj"].object_list]

    assert publicacao_artigo.pk in ids
    assert rascunho.pk not in ids


def test_publicacoes_index_tipo_selecionado_no_context(rf, publicacoes_index):
    request = rf.get("/publicacoes/?tipo=capitulo_livro")
    context = publicacoes_index.get_context(request)
    assert context["tipo_selecionado"] == "capitulo_livro"


def test_publicacoes_index_sem_filtro_tipo_selecionado_e_none(rf, publicacoes_index):
    request = rf.get("/publicacoes/")
    context = publicacoes_index.get_context(request)
    assert context["tipo_selecionado"] is None


def test_publicacoes_index_pagina_de_quinze_em_quinze(rf, publicacoes_index):
    for i in range(17):
        _make_publicacao(
            publicacoes_index, f"pub-{i}", f"Publicação {i}",
            "artigo_periodico", datetime.date(2025, 1, 1) + datetime.timedelta(days=i),
        )
    context = publicacoes_index.get_context(rf.get("/publicacoes/"))
    assert len(context["page_obj"].object_list) == 15

    context = publicacoes_index.get_context(rf.get("/publicacoes/?page=2"))
    assert len(context["page_obj"].object_list) == 2


# ---------------------------------------------------------------------------
# Relações reversas usadas em templates/pessoas/docente_page.html
# ---------------------------------------------------------------------------

def test_docente_expoe_projetos_que_coordena(docente, projeto_pesquisa):
    assert projeto_pesquisa.pk in [p.pk for p in docente.projetos_coordenados.live()]


def test_docente_expoe_publicacoes_de_que_e_autor(docente, publicacao_artigo):
    publicacao_artigo.autores_internos.add(docente)
    publicacao_artigo.save()

    assert publicacao_artigo.pk in [p.pk for p in docente.publicacoes.live()]


def test_projeto_coordenado_protege_docente_contra_exclusao(docente, projeto_pesquisa):
    """coordenador é on_delete=PROTECT: docente com projeto não pode sumir."""
    with pytest.raises(ProtectedError):
        docente.delete()
