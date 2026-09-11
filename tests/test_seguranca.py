"""Trava as propriedades de segurança que o deploy depende.

São regras fáceis de desfazer sem perceber — alguém reabilita SVG para colocar
um logo, ou troca a storage e o Wagtail volta a redirecionar documento para
`/media/`. O `docs/nginx.conf` bloqueia `/media/` para tudo que não seja imagem,
então essas duas coisas quebrariam em silêncio, cada uma de um jeito: a primeira
abrindo XSS, a segunda derrubando todo download de documento.

O que mora no Nginx não dá para testar daqui. Está verificado no
`docs/SEGURANCA.md` e no cabeçalho do próprio `docs/nginx.conf`.
"""

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.test import Client
from wagtail.documents import get_document_model

pytestmark = pytest.mark.django_db

SVG_COM_SCRIPT = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
    b'<script>alert(document.cookie)</script></svg>'
)


# ---------------------------------------------------------------------------
# Imagens — SVG não é sanitizado pelo Wagtail
# ---------------------------------------------------------------------------

def test_svg_fora_das_extensoes_aceitas():
    assert "svg" not in settings.WAGTAILIMAGES_EXTENSIONS


def test_upload_de_svg_e_recusado():
    """O Wagtail não sanitiza SVG: um <script> dentro roda na origem do portal."""
    from wagtail.images import get_image_model
    from wagtail.images.forms import get_image_form

    formulario = get_image_form(get_image_model())(
        data={"title": "Logo"},
        files={"file": ContentFile(SVG_COM_SCRIPT, name="logo.svg")},
    )

    assert not formulario.is_valid()
    assert "file" in formulario.errors


@pytest.mark.parametrize("extensao", ["png", "jpg", "jpeg", "gif", "webp"])
def test_formatos_de_imagem_usados_pelo_portal_continuam_aceitos(extensao):
    assert extensao in settings.WAGTAILIMAGES_EXTENSIONS


# ---------------------------------------------------------------------------
# Documentos — a permissão mora na rota do Wagtail, não no Nginx
# ---------------------------------------------------------------------------

def test_documento_e_servido_pela_rota_do_wagtail():
    """`serve_view` garante que a checagem de coleção acontece antes da entrega.

    Com `redirect`, o Wagtail mandaria o navegador direto para `/media/...`, que
    o Nginx bloqueia — e nenhum documento seria baixável em produção.
    """
    assert settings.WAGTAILDOCS_SERVE_METHOD == "serve_view"


def test_url_de_documento_nao_aponta_para_media():
    """É o que os templates usam em `{{ doc.arquivo.url }}`."""
    documento = get_document_model().objects.create(
        title="Regulamento",
        file=ContentFile(b"%PDF-1.4 conteudo", name="regulamento.pdf"),
    )

    assert documento.url.startswith("/documents/")
    assert "/media/" not in documento.url


def test_download_de_documento_funciona():
    documento = get_document_model().objects.create(
        title="Regulamento",
        file=ContentFile(b"%PDF-1.4 conteudo", name="regulamento.pdf"),
    )

    resposta = Client().get(documento.url)

    assert resposta.status_code == 200
    assert b"%PDF" in b"".join(resposta.streaming_content)


# ---------------------------------------------------------------------------
# Apps de desenvolvimento fora da produção
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("app", ["django_extensions", "debug_toolbar"])
def test_ferramenta_de_desenvolvimento_fora_dos_apps_base(app):
    """`production.py` faz `from .base import *` — o que estiver na base vai junto."""
    from config.settings import base

    assert app not in base.INSTALLED_APPS
