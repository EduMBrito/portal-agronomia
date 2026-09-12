import pytest

from apps.pessoas.models import DocentePage

# ---------------------------------------------------------------------------
# View: healthz
# ---------------------------------------------------------------------------
#
# É o que o healthcheck do container consulta. Se a rota sumir ou mudar de
# caminho, o Compose passa a considerar o serviço eterna e silenciosamente
# insalubre, e o Nginx nunca sobe — ele espera `service_healthy`.

@pytest.mark.django_db
def test_healthz_responde_200_com_banco_de_pe(client):
    resposta = client.get("/healthz/")

    assert resposta.status_code == 200
    assert resposta.content == b"ok\n"


@pytest.mark.django_db
def test_healthz_nao_vaza_informacao(client):
    """A rota é pública: não pode devolver versão, configuração nem erro do banco."""
    corpo = client.get("/healthz/").content.decode().lower()

    assert "django" not in corpo
    assert "wagtail" not in corpo
    assert "postgres" not in corpo


@pytest.mark.django_db
def test_healthz_responde_503_quando_o_banco_nao_responde(client, monkeypatch):
    """O PostgreSQL vive noutra instância — a rede entre as duas pode cair sozinha."""
    from django.db import OperationalError

    from apps.core import views

    def recusa():
        raise OperationalError("conexão recusada")

    monkeypatch.setattr(views.connection, "ensure_connection", recusa)

    resposta = client.get("/healthz/")

    assert resposta.status_code == 503


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
