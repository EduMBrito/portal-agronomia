from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page


class HomePage(Page):
    """Página inicial — raiz da árvore de conteúdo."""

    intro = RichTextField("Introdução", blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = [
        "pessoas.DocentesIndexPage",
        "ensino.DisciplinasIndexPage",
        "pesquisa.ProjetosIndexPage",
        "pesquisa.PublicacoesIndexPage",
        "noticias.PostsIndexPage",
        "institucional.DocumentosIndexPage",
        "institucional.EventosIndexPage",
    ]

    class Meta:
        verbose_name = "Página inicial"
