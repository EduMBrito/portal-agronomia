from django.utils import timezone
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

    def get_context(self, request, *args, **kwargs):
        from apps.ensino.models import DisciplinaPage
        from apps.institucional.models import EventoPage
        from apps.noticias.models import PostPage
        from apps.pessoas.models import DocentePage
        from apps.pesquisa.models import ProjetoPage

        context = super().get_context(request, *args, **kwargs)
        context["total_docentes"] = DocentePage.objects.live().count()
        context["total_disciplinas"] = DisciplinaPage.objects.live().count()
        context["total_projetos"] = ProjetoPage.objects.live().filter(status="em_andamento").count()
        context["eventos_proximos"] = (
            EventoPage.objects.live()
            .filter(data_inicio__gte=timezone.now())
            .order_by("data_inicio")[:4]
        )
        context["posts_recentes"] = (
            PostPage.objects.live()
            .order_by("-first_published_at")[:3]
        )
        return context
