from wagtail.admin.panels import FieldPanel, MultiFieldPanel


class SeoMixin:
    promote_panels = [
        MultiFieldPanel([
            FieldPanel("slug"),
            FieldPanel("seo_title"),
            FieldPanel("search_description"),
        ], heading="SEO e URL"),
    ]
