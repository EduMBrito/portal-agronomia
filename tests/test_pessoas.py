import pytest

from apps.pessoas.models import AreaConhecimento


# ---------------------------------------------------------------------------
# Snippet: AreaConhecimento
# ---------------------------------------------------------------------------

def test_area_conhecimento_str():
    area = AreaConhecimento(nome="Fitotecnia", slug="fitotecnia")
    assert str(area) == "Fitotecnia"


def test_area_conhecimento_slug_unico(area):
    with pytest.raises(Exception):
        AreaConhecimento.objects.create(nome="Outra", slug=area.slug)


# ---------------------------------------------------------------------------
# Page: DocentesIndexPage.get_context
# ---------------------------------------------------------------------------

def test_docentes_index_sem_filtro_retorna_todos(rf, docentes_index, dois_docentes):
    request = rf.get("/docentes/")
    context = docentes_index.get_context(request)
    assert context["page_obj"].paginator.count == 2


def test_docentes_index_filtro_area_retorna_apenas_docente_vinculado(
    rf, docentes_index, docente_com_area, docente_sem_area, area
):
    request = rf.get(f"/docentes/?area={area.slug}")
    context = docentes_index.get_context(request)
    assert context["page_obj"].paginator.count == 1
    assert context["page_obj"].object_list[0].pk == docente_com_area.pk


def test_docentes_index_area_inexistente_retorna_zero(rf, docentes_index, dois_docentes):
    request = rf.get("/docentes/?area=nao-existe")
    context = docentes_index.get_context(request)
    assert context["page_obj"].paginator.count == 0


def test_docentes_index_areas_disponiveis_no_context(rf, docentes_index, area):
    request = rf.get("/docentes/")
    context = docentes_index.get_context(request)
    assert area in context["areas"]


def test_docentes_index_area_selecionada_no_context(rf, docentes_index, area):
    request = rf.get(f"/docentes/?area={area.slug}")
    context = docentes_index.get_context(request)
    assert context["area_selecionada"] == area.slug


def test_docentes_index_sem_filtro_area_selecionada_e_none(rf, docentes_index):
    request = rf.get("/docentes/")
    context = docentes_index.get_context(request)
    assert context["area_selecionada"] is None
