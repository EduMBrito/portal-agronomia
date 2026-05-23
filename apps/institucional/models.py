from django.db import models
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import (
    FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface,
)
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.search import index

from apps.base.choices import TIPO_DOCUMENTO_CHOICES, TIPO_EVENTO_CHOICES
from apps.base.mixins import SeoMixin


class DocumentosIndexPage(Page):
    subpage_types = ["institucional.DocumentoPage"]
    parent_page_types = ["core.HomePage"]

    class Meta:
        verbose_name = "Documentos Institucionais"


class DocumentoPage(SeoMixin, Page):
    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_DOCUMENTO_CHOICES)
    descricao = models.TextField("Descrição", blank=True)
    arquivo = models.ForeignKey(
        "wagtaildocs.Document", on_delete=models.PROTECT,
        related_name="+", verbose_name="Arquivo (PDF)",
    )
    data_publicacao = models.DateField("Data de publicação")
    data_vigencia = models.DateField("Vigência até", null=True, blank=True)
    ativo = models.BooleanField("Ativo / vigente", default=True)

    content_panels = Page.content_panels + [
        FieldPanel("tipo"), FieldPanel("descricao"),
        FieldPanel("arquivo"), FieldPanel("data_publicacao"),
        FieldPanel("data_vigencia"), FieldPanel("ativo"),
    ]

    subpage_types = []
    parent_page_types = ["institucional.DocumentosIndexPage"]

    class Meta:
        verbose_name = "Documento Institucional"
        verbose_name_plural = "Documentos Institucionais"


class EventosIndexPage(Page):
    subpage_types = ["institucional.EventoPage"]
    parent_page_types = ["core.HomePage"]

    class Meta:
        verbose_name = "Agenda de Eventos"


class EventoPage(SeoMixin, Page):
    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_EVENTO_CHOICES)
    descricao = RichTextField("Descrição")
    data_inicio = models.DateTimeField("Data e hora de início")
    data_fim = models.DateTimeField("Data e hora de término", null=True, blank=True)
    local = models.CharField("Local", max_length=300)
    online = models.BooleanField("Evento online", default=False)
    link_online = models.URLField("Link online", blank=True)
    docentes_envolvidos = ParentalManyToManyField(
        "pessoas.DocentePage", blank=True,
        related_name="eventos", verbose_name="Docentes envolvidos",
    )
    projeto_vinculado = models.ForeignKey(
        "pesquisa.ProjetoPage", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="eventos",
        verbose_name="Projeto vinculado",
    )

    search_fields = Page.search_fields + [
        index.SearchField("descricao"),
        index.FilterField("tipo"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("tipo"), FieldPanel("data_inicio"), FieldPanel("data_fim"),
            FieldPanel("local"), FieldPanel("online"), FieldPanel("link_online"),
        ], heading="Informações"),
        FieldPanel("descricao"),
        MultiFieldPanel([
            FieldPanel("docentes_envolvidos"), FieldPanel("projeto_vinculado"),
        ], heading="Vínculos"),
    ]

    subpage_types = []
    parent_page_types = ["institucional.EventosIndexPage"]

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
