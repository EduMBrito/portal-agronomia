from django.db import models
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import (
    FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface,
)
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from apps.base.choices import TITULACAO_CHOICES
from apps.base.mixins import SeoMixin


@register_snippet
class AreaConhecimento(models.Model):
    nome = models.CharField("Nome", max_length=100)
    slug = models.SlugField(unique=True)

    panels = [FieldPanel("nome"), FieldPanel("slug")]

    class Meta:
        verbose_name = "Área de Conhecimento"
        verbose_name_plural = "Áreas de Conhecimento"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class DocentesIndexPage(Page):
    intro = RichTextField("Introdução", blank=True)
    content_panels = Page.content_panels + [FieldPanel("intro")]
    subpage_types = ["pessoas.DocentePage"]
    parent_page_types = ["core.HomePage"]

    class Meta:
        verbose_name = "Listagem de Docentes"


class DocentePage(SeoMixin, Page):
    nome_completo = models.CharField("Nome completo", max_length=200)
    foto = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+", verbose_name="Foto",
    )
    email = models.EmailField("E-mail institucional")
    lattes_url = models.URLField("URL do Lattes", blank=True)
    orcid = models.CharField("ORCID", max_length=20, blank=True)
    titulacao = models.CharField("Titulação", max_length=20, choices=TITULACAO_CHOICES)
    instituicao_titulacao = models.CharField("Instituição de titulação", max_length=200)
    areas_conhecimento = ParentalManyToManyField(
        AreaConhecimento, verbose_name="Áreas de conhecimento", blank=True,
    )
    bio = RichTextField("Biografia")

    search_fields = Page.search_fields + [
        index.SearchField("nome_completo"),
        index.SearchField("bio"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("nome_completo"), FieldPanel("foto"),
            FieldPanel("email"), FieldPanel("lattes_url"), FieldPanel("orcid"),
        ], heading="Identificação"),
        MultiFieldPanel([
            FieldPanel("titulacao"), FieldPanel("instituicao_titulacao"),
        ], heading="Formação"),
        MultiFieldPanel([
            FieldPanel("areas_conhecimento"), FieldPanel("bio"),
        ], heading="Atuação"),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading="Conteúdo"),
        ObjectList(SeoMixin.promote_panels, heading="SEO"),
    ])

    subpage_types = []
    parent_page_types = ["pessoas.DocentesIndexPage"]

    class Meta:
        verbose_name = "Perfil de Docente"
        verbose_name_plural = "Perfis de Docentes"

    def __str__(self):
        return self.nome_completo
