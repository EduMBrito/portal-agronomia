from wagtail.blocks import (
    BlockQuoteBlock, CharBlock, ChoiceBlock,
    RichTextBlock, StreamBlock, StructBlock,
)
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock


class CaptionedImageBlock(StructBlock):
    image = ImageChooserBlock(label="Imagem")
    caption = CharBlock(required=False, label="Legenda")

    class Meta:
        icon = "image"
        label = "Imagem com legenda"
        template = "base/blocks/captioned_image.html"


class DocumentBlock(StructBlock):
    document = DocumentChooserBlock(label="Arquivo")
    title = CharBlock(required=False, label="Título do link")

    class Meta:
        icon = "doc-full"
        label = "Documento para download"
        template = "base/blocks/document.html"


class CalloutBlock(StructBlock):
    tipo = ChoiceBlock(choices=[
        ("info", "Informação"),
        ("atencao", "Atenção"),
        ("importante", "Importante"),
    ], label="Tipo", default="info")
    texto = RichTextBlock(features=["bold", "italic", "link"], label="Texto")

    class Meta:
        icon = "help"
        label = "Destaque / Aviso"
        template = "base/blocks/callout.html"


BODY_BLOCKS = StreamBlock([
    ("paragrafo", RichTextBlock(label="Parágrafo")),
    ("imagem", CaptionedImageBlock()),
    ("documento", DocumentBlock()),
    ("embed", EmbedBlock(label="Embed (YouTube, Vimeo…)")),
    ("citacao", BlockQuoteBlock(label="Citação")),
    ("destaque", CalloutBlock()),
])
