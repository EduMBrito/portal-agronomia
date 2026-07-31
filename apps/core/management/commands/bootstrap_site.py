"""Cria a estrutura mínima de páginas do portal.

Roda uma vez logo após o `migrate`, antes do `populate_content`:

    python manage.py migrate
    python manage.py bootstrap_site
    python manage.py populate_content

O comando é idempotente — rodar de novo não duplica nada.
"""


from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import Page, Site

from apps.core.models import HomePage
from apps.ensino.models import DisciplinasIndexPage
from apps.institucional.models import DocumentosIndexPage, EventosIndexPage
from apps.noticias.models import PostsIndexPage
from apps.pesquisa.models import ProjetosIndexPage, PublicacoesIndexPage
from apps.pessoas.models import DocentesIndexPage

HOME_INTRO = (
    "<p>Portal do curso de Agronomia do Instituto Federal do Sertão Pernambucano, "
    "Campus Petrolina Zona Rural. Aqui ficam reunidos os materiais das disciplinas, "
    "a produção científica dos docentes, os projetos em andamento e a agenda "
    "acadêmica do curso.</p>"
)

# Ordem dos itens = ordem do menu em templates/includes/header.html.
# Os slugs precisam bater com os links de lá — só DocentesIndexPage e
# DisciplinasIndexPage têm o campo `intro`; nas demais ele fica vazio.
INDEX_PAGES = [
    (
        DocentesIndexPage, "Docentes", "docentes",
        "<p>Corpo docente do curso de Agronomia. Use o filtro por área de "
        "conhecimento para localizar professores por especialidade.</p>",
    ),
    (
        DisciplinasIndexPage, "Disciplinas", "disciplinas",
        "<p>Materiais didáticos organizados por disciplina e por período da "
        "grade curricular, do 1º ao 10º.</p>",
    ),
    (ProjetosIndexPage, "Projetos", "projetos", ""),
    (PublicacoesIndexPage, "Publicações", "publicacoes", ""),
    (PostsIndexPage, "Notícias", "noticias", ""),
    (EventosIndexPage, "Eventos", "eventos", ""),
    (DocumentosIndexPage, "Documentos", "documentos", ""),
]


class Command(BaseCommand):
    help = "Cria a HomePage e as sete páginas de listagem do portal."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== bootstrap_site ===\n"))

        self.stdout.write(self.style.MIGRATE_HEADING("Página inicial"))
        homepage = self._criar_homepage()

        self.stdout.write(self.style.MIGRATE_HEADING("\nSeções"))
        for page_type, titulo, slug, intro in INDEX_PAGES:
            self._criar_index(homepage, page_type, titulo, slug, intro)

        self.stdout.write(self.style.SUCCESS(
            "\n✓ Estrutura criada. Rode `populate_content` para carregar "
            "dados de exemplo.\n"
        ))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ok(self, texto: str) -> None:
        self.stdout.write(f"  ✓ {texto}")

    def _skip(self, slug: str) -> None:
        self.stdout.write(f"  → já existe: {slug}")

    # ------------------------------------------------------------------
    # Página inicial
    # ------------------------------------------------------------------

    def _criar_homepage(self) -> HomePage:
        """Cria a HomePage sob a Root e a coloca como raiz do Site padrão."""
        homepage = HomePage.objects.first()
        if homepage:
            self._skip(homepage.slug)
            self._apontar_site(homepage)
            return homepage

        root = Page.get_first_root_node()

        # O Wagtail cria de fábrica a página "Welcome to your new Wagtail site!",
        # que ocupa o slug "home". Liberamos o slug antes de criar a nossa.
        welcome = Page.objects.child_of(root).filter(slug="home").first()
        if welcome:
            welcome.slug = "welcome-wagtail"
            welcome.save()

        homepage = root.add_child(instance=HomePage(
            title="Portal Agronomia",
            slug="home",
            intro=HOME_INTRO,
        ))
        homepage.save_revision().publish()
        self._ok(homepage.title)

        # O Site precisa apontar para a nova raiz ANTES de apagar a página
        # padrão: Site.root_page é FK com on_delete=CASCADE e o Site iria junto.
        self._apontar_site(homepage)

        if welcome:
            welcome.delete()
            self._ok("página padrão do Wagtail removida")

        return homepage

    def _apontar_site(self, homepage: HomePage) -> None:
        """Repontua o Site padrão para a HomePage, para que ela responda em /."""
        site = Site.objects.filter(is_default_site=True).first()
        if not site:
            self.stdout.write(self.style.WARNING(
                "  ✗ nenhum Site padrão configurado — crie um em /admin/sites/."
            ))
            return

        if site.root_page_id == homepage.pk:
            self.stdout.write(f"  → Site '{site.hostname}' já aponta para a HomePage")
            return

        site.root_page = homepage
        site.save()
        self._ok(f"Site '{site.hostname}' apontado para a HomePage")

    # ------------------------------------------------------------------
    # Páginas de listagem
    # ------------------------------------------------------------------

    def _criar_index(
        self,
        homepage: HomePage,
        page_type: type[Page],
        titulo: str,
        slug: str,
        intro: str = "",
    ) -> Page | None:
        """Cria uma IndexPage filha da HomePage, se ainda não existir."""
        existente = page_type.objects.first()
        if existente:
            self._skip(existente.slug)
            return existente

        # Sem esta checagem o Wagtail renomearia o slug em silêncio
        # (docentes → docentes-1) e o link do menu quebraria.
        if homepage.get_children().filter(slug=slug).exists():
            self.stdout.write(self.style.WARNING(
                f"  ✗ o slug '{slug}' já está ocupado por outra página."
                f" {titulo} não foi criada."
            ))
            return None

        campos = {"title": titulo, "slug": slug}
        if intro:
            campos["intro"] = intro

        pagina = homepage.add_child(instance=page_type(**campos))
        pagina.save_revision().publish()
        self._ok(f"{titulo}  →  /{slug}/")
        return pagina
