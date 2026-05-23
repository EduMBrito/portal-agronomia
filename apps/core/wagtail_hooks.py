from django.utils.safestring import mark_safe
from wagtail import hooks
from wagtail.admin.ui.components import Component


class BemVindoPanel(Component):
    """Painel de boas-vindas exibido no topo do dashboard."""
    order = 10

    def render_html(self, parent_context=None):
        return mark_safe("""
        <section style="
          border-left: 4px solid #2D6636;
          background: #D4EDDA;
          padding: 1rem 1.25rem;
          border-radius: 0 0.5rem 0.5rem 0;
          margin-bottom: 1.5rem;
        ">
          <h2 style="color:#1A3C6E; font-size:1rem; font-weight:700; margin:0 0 0.25rem;">
            Portal Agronomia — IFSertãoPE
          </h2>
          <p style="color:#4A5568; font-size:0.875rem; margin:0;">
            Campus Petrolina Zona Rural &mdash; Painel de gerenciamento de conteúdo
          </p>
        </section>
        """)


class ResumoConteudoPanel(Component):
    """Painel com contagem de páginas publicadas por módulo."""
    order = 20

    def render_html(self, parent_context=None):
        from apps.ensino.models import DisciplinaPage
        from apps.institucional.models import DocumentoPage, EventoPage
        from apps.noticias.models import PostPage
        from apps.pesquisa.models import ProjetoPage, PublicacaoPage
        from apps.pessoas.models import DocentePage

        stats = [
            ("Docentes",     DocentePage.objects.live().count()),
            ("Disciplinas",  DisciplinaPage.objects.live().count()),
            ("Projetos",     ProjetoPage.objects.live().filter(status="em_andamento").count()),
            ("Publicações",  PublicacaoPage.objects.live().count()),
            ("Notícias",     PostPage.objects.live().count()),
            ("Eventos",      EventoPage.objects.live().count()),
            ("Documentos",   DocumentoPage.objects.live().count()),
        ]

        cards = "".join(
            f'<div style="text-align:center; padding:0.75rem 0.5rem; background:#fff; '
            f'border-radius:0.5rem; border:1px solid #e5e7eb;">'
            f'<div style="font-size:1.75rem; font-weight:700; color:#1A3C6E; line-height:1;">{count}</div>'
            f'<div style="font-size:0.7rem; color:#4A5568; text-transform:uppercase; '
            f'letter-spacing:0.05em; margin-top:0.25rem;">{label}</div>'
            f'</div>'
            for label, count in stats
        )

        return mark_safe(f"""
        <section style="margin-bottom:1.5rem;">
          <h2 style="font-size:0.75rem; font-weight:700; color:#4A5568; text-transform:uppercase;
                     letter-spacing:0.05em; margin-bottom:0.75rem;">
            Conteúdo publicado
          </h2>
          <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:0.625rem;">
            {cards}
          </div>
        </section>
        """)


class AcoesRapidasPanel(Component):
    """Atalhos para adicionar conteúdo novo."""
    order = 30

    def render_html(self, parent_context=None):
        from apps.ensino.models import DisciplinasIndexPage
        from apps.institucional.models import DocumentosIndexPage, EventosIndexPage
        from apps.noticias.models import PostsIndexPage
        from apps.pesquisa.models import ProjetosIndexPage, PublicacoesIndexPage
        from apps.pessoas.models import DocentesIndexPage

        def _add_url(PageType):
            page = PageType.objects.live().first()
            if page:
                return f"/admin/pages/add/{ PageType._meta.app_label }/{ PageType._meta.model_name }/{ page.pk }/"
            return "#"

        links = [
            ("Docente",      _add_url(DocentesIndexPage)),
            ("Disciplina",   _add_url(DisciplinasIndexPage)),
            ("Projeto",      _add_url(ProjetosIndexPage)),
            ("Publicação",   _add_url(PublicacoesIndexPage)),
            ("Post / Notícia", _add_url(PostsIndexPage)),
            ("Evento",       _add_url(EventosIndexPage)),
            ("Documento",    _add_url(DocumentosIndexPage)),
        ]

        btns = "".join(
            f'<a href="{url}" style="display:inline-block; padding:0.4rem 0.75rem; '
            f'background:#2D6636; color:#fff; border-radius:0.375rem; font-size:0.8rem; '
            f'text-decoration:none; font-weight:500; white-space:nowrap;">'
            f'+ {label}</a>'
            for label, url in links
        )

        return mark_safe(f"""
        <section style="margin-bottom:1.5rem;">
          <h2 style="font-size:0.75rem; font-weight:700; color:#4A5568; text-transform:uppercase;
                     letter-spacing:0.05em; margin-bottom:0.75rem;">
            Adicionar conteúdo
          </h2>
          <div style="display:flex; flex-wrap:wrap; gap:0.5rem;">
            {btns}
          </div>
        </section>
        """)


@hooks.register("construct_homepage_panels")
def adicionar_paineis_dashboard(request, panels):
    panels.insert(0, AcoesRapidasPanel())
    panels.insert(0, ResumoConteudoPanel())
    panels.insert(0, BemVindoPanel())
