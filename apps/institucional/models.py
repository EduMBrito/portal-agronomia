from django.core.paginator import Paginator
from django.db import models
from django.shortcuts import redirect
from django.utils import timezone
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
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

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        docs = DocumentoPage.objects.live().order_by("-data_publicacao")

        tipo = request.GET.get("tipo")
        if tipo:
            docs = docs.filter(tipo=tipo)

        paginator = Paginator(docs, 20)
        context["page_obj"] = paginator.get_page(request.GET.get("page", 1))
        context["tipos"] = TIPO_DOCUMENTO_CHOICES
        context["tipo_selecionado"] = tipo
        return context


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

    def serve(self, request, *args, **kwargs):
        """Entrega o PDF direto, em vez de renderizar uma página de detalhe.

        A DocumentoPage guarda apenas metadados — tipo, descrição, as duas datas
        e o flag `ativo` — e a listagem em /documentos/ já mostra todos eles.
        Uma página de detalhe não teria nada novo na tela, só mais um template
        para manter e um clique a mais entre a pessoa e o arquivo.

        O que a URL própria dá, e é por isso que ela existe, é um link estável e
        citável: /documentos/regulamento-tcc/ pode entrar num ofício ou numa
        ementa e continua valendo quando a comissão substituir o PDF por uma
        versão nova — a URL do arquivo muda, a da página não.

        O redirecionamento é temporário (302) justamente por isso: o destino
        muda a cada troca de arquivo, e um 301 ficaria no cache do navegador
        apontando para a versão antiga.
        """
        return redirect(self.arquivo.url)


class EventosIndexPage(Page):
    subpage_types = ["institucional.EventoPage"]
    parent_page_types = ["core.HomePage"]

    class Meta:
        verbose_name = "Agenda de Eventos"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        eventos = EventoPage.objects.live().order_by("-data_inicio")

        tipo = request.GET.get("tipo")
        apenas_futuros = request.GET.get("futuros")
        if tipo:
            eventos = eventos.filter(tipo=tipo)
        if apenas_futuros:
            eventos = eventos.filter(data_inicio__gte=timezone.now()).order_by("data_inicio")

        paginator = Paginator(eventos, 9)
        context["page_obj"] = paginator.get_page(request.GET.get("page", 1))
        context["tipos"] = TIPO_EVENTO_CHOICES
        context["tipo_selecionado"] = tipo
        context["apenas_futuros"] = bool(apenas_futuros)
        context["now"] = timezone.now()
        return context


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
