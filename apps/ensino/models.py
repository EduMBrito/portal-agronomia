from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import (
    FieldPanel, InlinePanel, MultiFieldPanel, ObjectList, TabbedInterface,
)
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index

from apps.base.choices import TIPO_MATERIAL_CHOICES
from apps.base.mixins import SeoMixin


class DisciplinasIndexPage(Page):
    intro = RichTextField("Introdução", blank=True)
    content_panels = Page.content_panels + [FieldPanel("intro")]
    subpage_types = ["ensino.DisciplinaPage"]
    parent_page_types = ["core.HomePage"]

    class Meta:
        verbose_name = "Grade de Disciplinas"


class DisciplinaPage(SeoMixin, Page):
    codigo = models.CharField("Código", max_length=20)
    carga_horaria = models.PositiveIntegerField("Carga horária (h)")
    periodo = models.PositiveSmallIntegerField("Período (1–10)")
    ementa = RichTextField("Ementa")
    docente_responsavel = models.ForeignKey(
        "pessoas.DocentePage", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="disciplinas",
        verbose_name="Docente responsável",
    )

    search_fields = Page.search_fields + [
        index.SearchField("codigo"),
        index.SearchField("ementa"),
        index.FilterField("periodo"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("codigo"),
            FieldPanel("carga_horaria"),
            FieldPanel("periodo"),
        ], heading="Informações gerais"),
        FieldPanel("ementa"),
        FieldPanel("docente_responsavel"),
        InlinePanel("materiais", label="Materiais"),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading="Conteúdo"),
        ObjectList(SeoMixin.promote_panels, heading="SEO"),
    ])

    subpage_types = []
    parent_page_types = ["ensino.DisciplinasIndexPage"]

    class Meta:
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"


class MaterialDisciplina(Orderable):
    disciplina = ParentalKey(
        DisciplinaPage, on_delete=models.CASCADE, related_name="materiais",
    )
    titulo = models.CharField("Título", max_length=200)
    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_MATERIAL_CHOICES)
    arquivo = models.ForeignKey(
        "wagtaildocs.Document", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+", verbose_name="Arquivo",
    )
    url_externa = models.URLField("URL externa", blank=True)
    descricao = models.TextField("Descrição", blank=True)
    data_publicacao = models.DateField("Data de publicação")

    panels = [
        FieldPanel("titulo"), FieldPanel("tipo"),
        FieldPanel("arquivo"), FieldPanel("url_externa"),
        FieldPanel("descricao"), FieldPanel("data_publicacao"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Material"
