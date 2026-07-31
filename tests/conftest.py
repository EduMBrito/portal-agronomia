import datetime

import pytest
from django.utils import timezone
from wagtail.models import Page, Site

from apps.core.models import HomePage
from apps.ensino.models import DisciplinaPage, DisciplinasIndexPage
from apps.institucional.models import EventoPage, EventosIndexPage
from apps.noticias.models import PostPage, PostsIndexPage
from apps.pesquisa.models import (
    ProjetoPage, ProjetosIndexPage, PublicacaoPage, PublicacoesIndexPage,
)
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


@pytest.fixture
def projetos_index(home_page):
    return home_page.add_child(instance=ProjetosIndexPage(
        title="Projetos",
        slug="test-projetos",
        live=True,
    ))


@pytest.fixture
def publicacoes_index(home_page):
    return home_page.add_child(instance=PublicacoesIndexPage(
        title="Publicações",
        slug="test-publicacoes",
        live=True,
    ))


@pytest.fixture
def posts_index(home_page):
    return home_page.add_child(instance=PostsIndexPage(
        title="Notícias",
        slug="test-noticias",
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


@pytest.fixture
def docente(docentes_index):
    """Docente genérico — coordenador de projeto, autor de post e publicação."""
    return _make_docente(docentes_index, "prof-coord", "Prof. Coordenador")


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


# ---------------------------------------------------------------------------
# Projetos
# ---------------------------------------------------------------------------

def _make_projeto(parent, slug, titulo, tipo, status, coordenador,
                  data_inicio=None, live=True):
    return parent.add_child(instance=ProjetoPage(
        title=titulo,
        slug=slug,
        tipo=tipo,
        status=status,
        resumo="Resumo do projeto para o card de listagem.",
        data_inicio=data_inicio or datetime.date(2025, 1, 15),
        coordenador=coordenador,
        live=live,
    ))


@pytest.fixture
def projeto_pesquisa(projetos_index, docente):
    """Pesquisa em andamento, iniciado em 2025 — o mais recente."""
    return _make_projeto(
        projetos_index, "proj-pesquisa", "Déficit Hídrico em Sorgo",
        "pesquisa", "em_andamento", docente, datetime.date(2025, 6, 1),
    )


@pytest.fixture
def projeto_extensao(projetos_index, docente):
    """Extensão concluída, iniciada em 2024 — o mais antigo."""
    return _make_projeto(
        projetos_index, "proj-extensao", "Horta Comunitária",
        "extensao", "concluido", docente, datetime.date(2024, 3, 1),
    )


# ---------------------------------------------------------------------------
# Publicações
# ---------------------------------------------------------------------------

def _make_publicacao(parent, slug, titulo, tipo, data_publicacao, live=True):
    return parent.add_child(instance=PublicacaoPage(
        title=titulo,
        slug=slug,
        tipo=tipo,
        resumo="Resumo da publicação.",
        veiculo="Revista Brasileira de Agronomia",
        data_publicacao=data_publicacao,
        live=live,
    ))


@pytest.fixture
def publicacao_artigo(publicacoes_index):
    return _make_publicacao(
        publicacoes_index, "pub-artigo", "Produtividade do Feijão-Caupi",
        "artigo_periodico", datetime.date(2025, 5, 10),
    )


@pytest.fixture
def publicacao_tese(publicacoes_index):
    return _make_publicacao(
        publicacoes_index, "pub-tese", "Fertilidade de Solos no Sertão",
        "tese", datetime.date(2023, 2, 1),
    )


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------

def _make_post(parent, slug, titulo, autor, data_publicacao=None, live=True):
    page = parent.add_child(instance=PostPage(
        title=titulo,
        slug=slug,
        autor=autor,
        resumo="Resumo do post para o card.",
        corpo=[{"type": "paragrafo", "value": "<p>Conteúdo do post.</p>"}],
        live=live,
    ))
    if data_publicacao:
        # data_publicacao é auto_now_add: o model sempre grava a data de hoje
        # e ignora o valor passado. Só dá para controlá-la por UPDATE direto.
        PostPage.objects.filter(pk=page.pk).update(data_publicacao=data_publicacao)
        page.refresh_from_db()
    return page


@pytest.fixture
def post_recente(posts_index, docente):
    return _make_post(
        posts_index, "post-recente", "Semiárido e Inovação",
        docente, datetime.date(2026, 5, 20),
    )


@pytest.fixture
def post_antigo(posts_index, docente):
    return _make_post(
        posts_index, "post-antigo", "Compostagem Agroecológica",
        docente, datetime.date(2025, 8, 3),
    )
