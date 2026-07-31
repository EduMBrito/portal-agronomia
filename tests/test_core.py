import pytest

from apps.pessoas.models import DocentePage

# ---------------------------------------------------------------------------
# View: busca
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_busca_sem_query_retorna_200(client):
    response = client.get("/busca/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_busca_query_vazia_preserva_string_vazia_no_context(client):
    response = client.get("/busca/?q=")
    assert response.context["query"] == ""


@pytest.mark.django_db
def test_busca_query_vazia_retorna_zero_resultados(client):
    response = client.get("/busca/?q=")
    assert len(response.context["page_obj"].object_list) == 0


@pytest.mark.django_db
def test_busca_preserva_termo_no_context(client, home_page):
    response = client.get("/busca/?q=agronomia")
    assert response.context["query"] == "agronomia"


# ---------------------------------------------------------------------------
# Model: HomePage.get_context
# ---------------------------------------------------------------------------

def test_homepage_context_zerado_sem_conteudo(rf, home_page):
    request = rf.get("/")
    context = home_page.get_context(request)

    assert context["total_docentes"] == 0
    assert context["total_disciplinas"] == 0
    assert context["total_projetos"] == 0
    assert list(context["eventos_proximos"]) == []
    assert list(context["posts_recentes"]) == []


def test_homepage_context_conta_docente_publicado(rf, home_page, docentes_index):
    docentes_index.add_child(instance=DocentePage(
        title="Prof. Contexto",
        slug="prof-contexto",
        nome_completo="Prof. Contexto",
        email="contexto@ifsertao.edu.br",
        titulacao="doutorado",
        instituicao_titulacao="UFPE",
        bio="<p>Bio.</p>",
        live=True,
    ))
    request = rf.get("/")
    context = home_page.get_context(request)
    assert context["total_docentes"] == 1


def test_homepage_context_nao_conta_docente_nao_publicado(rf, home_page, docentes_index):
    docentes_index.add_child(instance=DocentePage(
        title="Prof. Rascunho",
        slug="prof-rascunho",
        nome_completo="Prof. Rascunho",
        email="rascunho@ifsertao.edu.br",
        titulacao="mestrado",
        instituicao_titulacao="UNIVASF",
        bio="<p>Bio.</p>",
        live=False,
    ))
    request = rf.get("/")
    context = home_page.get_context(request)
    assert context["total_docentes"] == 0
