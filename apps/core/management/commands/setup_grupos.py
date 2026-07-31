"""
Cria os grupos de usuários e configura permissões no Wagtail.

Uso:
    docker compose exec web python manage.py setup_grupos

Grupos criados:
    Coordenador — publica qualquer conteúdo em todo o portal
    Docente     — cria e edita posts, publicações e projetos
    Técnico     — gerencia documentos e eventos institucionais
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from wagtail.models import Collection, GroupCollectionPermission, GroupPagePermission, Page


def _perm_page(codename: str) -> Permission:
    ct = ContentType.objects.get_for_model(Page)
    return Permission.objects.get(content_type=ct, codename=codename)


def _perm(app_label: str, codename: str) -> Permission:
    return Permission.objects.get(
        content_type__app_label=app_label,
        codename=codename,
    )


def _set_page_perms(group: Group, page: Page, codenames: list[str]) -> None:
    for codename in codenames:
        perm = _perm_page(codename)
        obj, created = GroupPagePermission.objects.get_or_create(
            group=group, page=page, permission=perm,
        )
        if created:
            pass  # silencioso — criado pelo get_or_create


def _set_collection_perms(group: Group, collection: Collection, codenames: list[str]) -> None:
    for codename in codenames:
        # codenames: choose_image, add_image / choose_document, add_document
        app, model = codename.split("_", 1)
        app_label = "wagtailimages" if "image" in model else "wagtaildocs"
        try:
            perm = Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename,
            )
            GroupCollectionPermission.objects.get_or_create(
                group=group, collection=collection, permission=perm,
            )
        except Permission.DoesNotExist:
            pass


class Command(BaseCommand):
    help = "Cria grupos de usuários (Coordenador, Docente, Técnico) com permissões"

    def handle(self, *args, **kwargs):
        access_admin = _perm("wagtailadmin", "access_admin")
        root_collection = Collection.objects.filter(depth=1).first()

        self._coordenador(access_admin, root_collection)
        self._docente(access_admin, root_collection)
        self._tecnico(access_admin, root_collection)

        self.stdout.write(self.style.SUCCESS("Grupos configurados com sucesso."))

    # ── Coordenador ────────────────────────────────────────────────────────────

    def _coordenador(self, access_admin, collection):
        grupo, _ = Group.objects.get_or_create(name="Coordenador")
        grupo.permissions.add(access_admin)

        from apps.core.models import HomePage
        home = HomePage.objects.live().first()
        if home:
            _set_page_perms(grupo, home, [
                "add_page", "change_page", "publish_page",
                "bulk_delete_page", "lock_page", "unlock_page",
            ])
            self.stdout.write(f"  Coordenador: permissões completas em '{home}'")
        else:
            self.stdout.write(self.style.WARNING(
                "  Coordenador: HomePage não encontrada — crie a árvore primeiro."
            ))

        if collection:
            _set_collection_perms(grupo, collection, [
                "add_image", "change_image", "choose_image",
                "add_document", "change_document", "choose_document",
            ])

    # ── Docente ────────────────────────────────────────────────────────────────

    def _docente(self, access_admin, collection):
        grupo, _ = Group.objects.get_or_create(name="Docente")
        grupo.permissions.add(access_admin)

        from apps.noticias.models import PostsIndexPage
        from apps.pesquisa.models import ProjetosIndexPage, PublicacoesIndexPage

        paginas = [
            ("posts",        PostsIndexPage),
            ("projetos",     ProjetosIndexPage),
            ("publicações",  PublicacoesIndexPage),
        ]
        for nome, PageType in paginas:
            page = PageType.objects.live().first()
            if page:
                _set_page_perms(grupo, page, ["add_page", "change_page"])
                self.stdout.write(f"  Docente: add+edit em '{page}' ({nome})")
            else:
                self.stdout.write(self.style.WARNING(
                    f"  Docente: {PageType.__name__} não encontrada."
                ))

        if collection:
            _set_collection_perms(grupo, collection, [
                "add_image", "choose_image",
                "add_document", "choose_document",
            ])

    # ── Técnico ────────────────────────────────────────────────────────────────

    def _tecnico(self, access_admin, collection):
        grupo, _ = Group.objects.get_or_create(name="Técnico")
        grupo.permissions.add(access_admin)

        from apps.institucional.models import DocumentosIndexPage, EventosIndexPage

        paginas = [
            ("documentos", DocumentosIndexPage),
            ("eventos",    EventosIndexPage),
        ]
        for nome, PageType in paginas:
            page = PageType.objects.live().first()
            if page:
                _set_page_perms(grupo, page, ["add_page", "change_page", "publish_page"])
                self.stdout.write(f"  Técnico: add+edit+publish em '{page}' ({nome})")
            else:
                self.stdout.write(self.style.WARNING(
                    f"  Técnico: {PageType.__name__} não encontrada."
                ))

        if collection:
            _set_collection_perms(grupo, collection, [
                "add_image", "choose_image",
                "add_document", "choose_document",
            ])
