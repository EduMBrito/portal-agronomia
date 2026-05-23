from django.utils.html import format_html
from wagtail import hooks


@hooks.register("insert_global_admin_css")
def admin_branding_css():
    """Aplica a paleta institucional do IFSertãoPE no painel Wagtail."""
    return format_html("""<style>
      :root {{
        --w-color-primary:      #2D6636;
        --w-color-primary-200:  #D4EDDA;
        --w-color-secondary:    #1A3C6E;
        --w-color-secondary-75: #2E6DB4;
        --w-color-secondary-50: #DBEAFE;
      }}
      .sidebar {{ background-color: #1A3C6E !important; }}
      .sidebar-sub-menu-item.sidebar-sub-menu-item--active {{
        background: #2D6636 !important;
      }}
    </style>""")
