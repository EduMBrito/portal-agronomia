from django.core.paginator import Paginator
from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.managers import TaggableManager
from wagtail.admin.panels import (
    FieldPanel, InlinePanel, MultiFieldPanel, ObjectList, TabbedInterface,
)
from wagtail.fields import StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index

from apps.base.blocks import BODY_BLOCKS
from apps.base.choices import (
    STATUS_PROJETO_CHOICES, TIPO_PRODUTO_CHOICES,
    TIPO_PROJETO_CHOICES, TIPO_PUBLICACAO_CHOICES,
)
from apps.base.mixins import SeoMixin


class ProjetosIndexPage(Page):
    subpage_types = ["pesquisa.ProjetoPage"]
    parent_page_types = ["core.HomePage"]

    class Meta:
        verbose_name = "Listagem de Projetos"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        projetos = ProjetoPage.objects.live().order_by("-data_inicio")

        tipo = request.GET.get("tipo")
        status = request.GET.get("status")
        if tipo:
            projetos = projetos.filter(tipo=tipo)
        if status:
            projetos = projetos.filter(status=status)

        paginator = Paginator(projetos, 9)
        context["page_obj"] = paginator.get_page(request.GET.get("page", 1))
        context["tipos"] = TIPO_PROJETO_CHOICES
        context["status_opcoes"] = STATUS_PROJETO_CHOICES
        context["tipo_selecionado"] = tipo
        context["status_selecionado"] = status
        return context


class ProjetoPage(SeoMixin, Page):
    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_PROJETO_CHOICES)
    resumo = models.TextField("Resumo", max_length=250)
    descricao = StreamField(BODY_BLOCKS, verbose_name="Descrição", blank=True, use_json_field=True)
    data_inicio = models.DateField("Início")
    data_fim = models.DateField("Término", null=True, blank=True)
    status = models.CharField("Status", max_length=20, choices=STATUS_PROJETO_CHOICES, default="em_andamento")
    coordenador = models.ForeignKey(
        "pessoas.DocentePage", on_delete=models.PROTECT,
        related_name="projetos_coordenados", verbose_name="Coordenador",
    )
    participantes_docentes = ParentalManyToManyField(
        "pessoas.DocentePage", blank=True,
        related_name="projetos_participados", verbose_name="Participantes",
    )
    edital = models.ForeignKey(
        "wagtaildocs.Document", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+", verbose_name="Edital",
    )
    financiador = models.CharField("Financiador", max_length=200, blank=True)
    tags = TaggableManager(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField("resumo"),
        index.FilterField("tipo"),
        index.FilterField("status"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("tipo"), FieldPanel("status"),
            FieldPanel("data_inicio"), FieldPanel("data_fim"),
        ], heading="Classificação"),
        FieldPanel("resumo"),
        FieldPanel("descricao"),
        MultiFieldPanel([
            FieldPanel("coordenador"), FieldPanel("participantes_docentes"),
        ], heading="Equipe"),
        MultiFieldPanel([
            FieldPanel("edital"), FieldPanel("financiador"), FieldPanel("tags"),
        ], heading="Vínculos"),
        InlinePanel("produtos", label="Produtos"),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading="Conteúdo"),
        ObjectList(SeoMixin.promote_panels, heading="SEO"),
    ])

    subpage_types = []
    parent_page_types = ["pesquisa.ProjetosIndexPage"]

    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"


class ProdutoProjeto(Orderable):
    projeto = ParentalKey(ProjetoPage, on_delete=models.CASCADE, related_name="produtos")
    titulo = models.CharField("Título", max_length=200)
    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_PRODUTO_CHOICES)
    arquivo = models.ForeignKey(
        "wagtaildocs.Document", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    url = models.URLField("URL", blank=True)
    data = models.DateField("Data")

    panels = [
        FieldPanel("titulo"), FieldPanel("tipo"),
        FieldPanel("arquivo"), FieldPanel("url"), FieldPanel("data"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Produto"


class PublicacoesIndexPage(Page):
    subpage_types = ["pesquisa.PublicacaoPage"]
    parent_page_types = ["core.HomePage"]

    class Meta:
        verbose_name = "Listagem de Publicações"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        publicacoes = PublicacaoPage.objects.live().order_by("-data_publicacao")

        tipo = request.GET.get("tipo")
        if tipo:
            publicacoes = publicacoes.filter(tipo=tipo)

        paginator = Paginator(publicacoes, 15)
        context["page_obj"] = paginator.get_page(request.GET.get("page", 1))
        context["tipos"] = TIPO_PUBLICACAO_CHOICES
        context["tipo_selecionado"] = tipo
        return context


class PublicacaoPage(SeoMixin, Page):
    tipo = models.CharField("Tipo", max_length=30, choices=TIPO_PUBLICACAO_CHOICES)
    resumo = models.TextField("Resumo")
    corpo = StreamField(BODY_BLOCKS, verbose_name="Conteúdo", blank=True, use_json_field=True)
    autores_internos = ParentalManyToManyField(
        "pessoas.DocentePage", blank=True,
        related_name="publicacoes", verbose_name="Autores internos",
    )
    autores_externos = models.CharField("Autores externos", max_length=500, blank=True)
    veiculo = models.CharField("Veículo de publicação", max_length=300)
    doi = models.CharField("DOI", max_length=100, blank=True)
    issn = models.CharField("ISSN", max_length=20, blank=True)
    arquivo_pdf = models.ForeignKey(
        "wagtaildocs.Document", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+", verbose_name="PDF",
    )
    url_acesso = models.URLField("URL de acesso", blank=True)
    data_publicacao = models.DateField("Data de publicação")
    tags = TaggableManager(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField("resumo"),
        index.SearchField("veiculo"),
        index.FilterField("tipo"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("tipo"), FieldPanel("data_publicacao"),
        ], heading="Classificação"),
        FieldPanel("resumo"),
        FieldPanel("corpo"),
        MultiFieldPanel([
            FieldPanel("autores_internos"), FieldPanel("autores_externos"),
        ], heading="Autoria"),
        MultiFieldPanel([
            FieldPanel("veiculo"), FieldPanel("doi"), FieldPanel("issn"),
            FieldPanel("arquivo_pdf"), FieldPanel("url_acesso"), FieldPanel("tags"),
        ], heading="Publicação"),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading="Conteúdo"),
        ObjectList(SeoMixin.promote_panels, heading="SEO"),
    ])

    subpage_types = []
    parent_page_types = ["pesquisa.PublicacoesIndexPage"]

    class Meta:
        verbose_name = "Publicação"
        verbose_name_plural = "Publicações"
