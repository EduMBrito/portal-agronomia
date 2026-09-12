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
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.test import Client, override_settings
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


# ---------------------------------------------------------------------------
# Entrega de documento pelo Nginx — a permissão continua sendo do Wagtail
# ---------------------------------------------------------------------------
#
# O X-Accel-Redirect tira o arquivo do caminho do Python, mas não pode tirar a
# checagem de coleção junto. Estes testes travam as duas coisas: que o caminho
# gerado cai dentro do `location internal` do Nginx, e que ele nunca aponta
# para fora de SENDFILE_ROOT — o que daria ao Nginx um caminho que ele não
# serve, ou pior, um que ele serve sem checagem nenhuma.

def test_x_accel_aponta_para_o_location_interno(tmp_path):
    from apps.core.sendfile_nginx import sendfile

    raiz = tmp_path / "media"
    (raiz / "documents").mkdir(parents=True)
    arquivo = raiz / "documents" / "regulamento.pdf"
    arquivo.write_bytes(b"%PDF-1.4")

    with override_settings(SENDFILE_ROOT=str(raiz), SENDFILE_URL="/_protegido"):
        resposta = sendfile(None, str(arquivo))

    assert resposta["X-Accel-Redirect"] == "/_protegido/documents/regulamento.pdf"
    assert resposta.content == b""


def test_x_accel_escapa_nome_de_arquivo_com_espaco_e_acento(tmp_path):
    """Nome de arquivo vem da comissão, não de nós. `Ata da reunião.pdf` acontece."""
    from apps.core.sendfile_nginx import sendfile

    raiz = tmp_path / "media"
    (raiz / "documents").mkdir(parents=True)
    arquivo = raiz / "documents" / "Ata da reunião.pdf"
    arquivo.write_bytes(b"%PDF-1.4")

    with override_settings(SENDFILE_ROOT=str(raiz), SENDFILE_URL="/_protegido"):
        resposta = sendfile(None, str(arquivo))

    assert resposta["X-Accel-Redirect"] == (
        "/_protegido/documents/Ata%20da%20reuni%C3%A3o.pdf"
    )


def test_x_accel_recusa_caminho_fora_de_sendfile_root(tmp_path):
    """Falhar alto: um caminho fora da raiz é configuração errada, não entrada."""
    from apps.core.sendfile_nginx import sendfile

    raiz = tmp_path / "media"
    raiz.mkdir()
    fora = tmp_path / "etc" / "passwd"
    fora.parent.mkdir()
    fora.write_bytes(b"raiz:x:0:0")

    with override_settings(SENDFILE_ROOT=str(raiz), SENDFILE_URL="/_protegido"):
        with pytest.raises(ImproperlyConfigured):
            sendfile(None, str(fora))


def test_download_delega_ao_nginx_sem_perder_a_checagem_de_permissao():
    """O corpo vem vazio: quem entrega o arquivo é o Nginx, não o Gunicorn."""
    from wagtail.utils.sendfile import _get_sendfile

    documento = get_document_model().objects.create(
        title="Regulamento",
        file=ContentFile(b"%PDF-1.4 conteudo", name="regulamento.pdf"),
    )

    try:
        with override_settings(
            SENDFILE_BACKEND="apps.core.sendfile_nginx",
            SENDFILE_ROOT=settings.MEDIA_ROOT,
            SENDFILE_URL="/_protegido",
        ):
            resposta = Client().get(documento.url)
    finally:
        # O wagtail.utils.sendfile guarda o backend em cache de processo.
        _get_sendfile.clear()

    assert resposta.status_code == 200
    assert resposta["X-Accel-Redirect"].startswith("/_protegido/documents/")
    assert resposta.content == b""
