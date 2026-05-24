import pytest
from django.utils import timezone
from wagtail.models import Page, Site

from apps.core.models import HomePage
from apps.ensino.models import DisciplinaPage, DisciplinasIndexPage
from apps.institucional.models import EventoPage, EventosIndexPage
from apps.pessoas.models import AreaConhecimento, DocentePage, DocentesIndexPage


# ---------------------------------------------------------------------------
# Árvore de páginas
# ---------------------------------------------------------------------------

@pytest.fixture
def home_page(db):
    root = Page.objects.get(depth=1)
    home = root.add_child(instance=HomePage(
        title="Portal Agronomia",
        slug="test-portal",
        live=True,
    ))
    Site.objects.filter(is_default_site=True).update(root_page=home)
    return home


@pytest.fixture
def docentes_index(home_page):
    return home_page.add_child(instance=DocentesIndexPage(
        title="Docentes",
        slug="test-docentes",
        live=True,
    ))


@pytest.fixture
def disciplinas_index(home_page):
    return home_page.add_child(instance=DisciplinasIndexPage(
        title="Disciplinas",
        slug="test-disciplinas",
        live=True,
    ))


@pytest.fixture
def eventos_index(home_page):
    return home_page.add_child(instance=EventosIndexPage(
        title="Eventos",
        slug="test-eventos",
        live=True,
    ))


# ---------------------------------------------------------------------------
# Snippets
# ---------------------------------------------------------------------------

@pytest.fixture
def area(db):
    return AreaConhecimento.objects.create(nome="Fitotecnia", slug="fitotecnia")


# ---------------------------------------------------------------------------
# Docentes
# ---------------------------------------------------------------------------

def _make_docente(parent, slug, nome):
    return parent.add_child(instance=DocentePage(
        title=nome,
        slug=slug,
        nome_completo=nome,
        email=f"{slug}@ifsertao.edu.br",
        titulacao="mestrado",
        instituicao_titulacao="UNIVASF",
        bio="<p>Biografia.</p>",
        live=True,
    ))


@pytest.fixture
def docente_com_area(docentes_index, area):
    page = _make_docente(docentes_index, "prof-area", "Prof. Com Área")
    docente = DocentePage.objects.get(pk=page.pk)
    # ParentalManyToManyField acumula em memória; .save() persiste no banco
    docente.areas_conhecimento.add(area)
    docente.save()
    return docente


@pytest.fixture
def docente_sem_area(docentes_index):
    return _make_docente(docentes_index, "prof-sem-area", "Prof. Sem Área")


@pytest.fixture
def dois_docentes(docente_com_area, docente_sem_area):
    return docente_com_area, docente_sem_area


# ---------------------------------------------------------------------------
# Disciplinas
# ---------------------------------------------------------------------------

def _make_disciplina(parent, slug, titulo, periodo, codigo):
    return parent.add_child(instance=DisciplinaPage(
        title=titulo,
        slug=slug,
        codigo=codigo,
        carga_horaria=60,
        periodo=periodo,
        ementa="<p>Ementa.</p>",
        live=True,
    ))


@pytest.fixture
def disciplina_p1(disciplinas_index):
    return _make_disciplina(disciplinas_index, "agr101", "Botânica", 1, "AGR-101")


@pytest.fixture
def disciplina_p3(disciplinas_index):
    return _make_disciplina(disciplinas_index, "agr301", "Solos I", 3, "AGR-301")


# ---------------------------------------------------------------------------
# Eventos
# ---------------------------------------------------------------------------

def _make_evento(parent, slug, titulo, tipo, data_inicio):
    return parent.add_child(instance=EventoPage(
        title=titulo,
        slug=slug,
        tipo=tipo,
        descricao="<p>Descrição.</p>",
        data_inicio=data_inicio,
        local="Auditório Principal",
        live=True,
    ))


@pytest.fixture
def evento_futuro(eventos_index):
    dt = timezone.now() + timezone.timedelta(days=10)
    return _make_evento(eventos_index, "ev-futuro", "Seminário Futuro", "seminario", dt)


@pytest.fixture
def evento_passado(eventos_index):
    dt = timezone.now() - timezone.timedelta(days=10)
    return _make_evento(eventos_index, "ev-passado", "Workshop Passado", "workshop", dt)


@pytest.fixture
def evento_seminario(eventos_index):
    dt = timezone.now() + timezone.timedelta(days=5)
    return _make_evento(eventos_index, "ev-seminario", "Seminário Teste", "seminario", dt)


@pytest.fixture
def evento_workshop(eventos_index):
    dt = timezone.now() + timezone.timedelta(days=7)
    return _make_evento(eventos_index, "ev-workshop", "Workshop Teste", "workshop", dt)
