from django.core.paginator import Paginator
from django.db import models
from taggit.managers import TaggableManager
from wagtail.admin.panels import (
    FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface,
)
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from apps.base.blocks import BODY_BLOCKS
from apps.base.mixins import SeoMixin


class PostsIndexPage(Page):
    subpage_types = ["noticias.PostPage"]
    parent_page_types = ["core.HomePage"]

    class Meta:
        verbose_name = "Feed de Posts"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        posts = PostPage.objects.live().order_by("-data_publicacao")
        paginator = Paginator(posts, 9)
        context["page_obj"] = paginator.get_page(request.GET.get("page", 1))
        return context


class PostPage(SeoMixin, Page):
    autor = models.ForeignKey(
        "pessoas.DocentePage", on_delete=models.PROTECT,
        related_name="posts", verbose_name="Autor",
    )
    capa = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+", verbose_name="Imagem de capa",
    )
    resumo = models.TextField("Resumo", max_length=200)
    corpo = StreamField(BODY_BLOCKS, verbose_name="Conteúdo", use_json_field=True)
    data_publicacao = models.DateField("Data de publicação", auto_now_add=True)
    tags = TaggableManager(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField("resumo"),
        index.SearchField("corpo"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("autor"), FieldPanel("capa"),
        ], heading="Autoria"),
        FieldPanel("resumo"),
        FieldPanel("corpo"),
        FieldPanel("tags"),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading="Conteúdo"),
        ObjectList(SeoMixin.promote_panels, heading="SEO"),
    ])

    subpage_types = []
    parent_page_types = ["noticias.PostsIndexPage"]

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"
