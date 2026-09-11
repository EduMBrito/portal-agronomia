"""Importa perfil e projetos de um XML do Currículo Lattes.

Uso pela comissão gestora:

    python manage.py importar_lattes /caminho/fora/da/web/curriculo.xml
    python manage.py importar_lattes curriculo.xml --email joao@ifsertao-pe.edu.br
    python manage.py importar_lattes curriculo.xml --dry-run

O docente exporta o XML no site do CNPq e entrega à comissão — não existe API
pública do Lattes (verificado em 31/07/2026: os endpoints não respondem e a
busca é protegida por reCAPTCHA).

LGPD — o XML contém CPF, RG, filiação, telefone e endereço. Nada disso entra no
banco: o parser lê apenas o que alimenta os models. O arquivo é insumo de
processamento e deve ficar FORA da raiz web (em produção o Nginx serve /media/
como alias direto, sem autenticação) e ser descartado depois da importação.

Tudo que o comando cria nasce como rascunho (`live=False`) para a comissão
revisar e publicar. O comando é idempotente: rodar de novo atualiza em vez de
duplicar. A chave de deduplicação é o `lattes_url` para o docente e o slug do
título para o projeto — se a comissão renomear o slug de um projeto, uma nova
rodada cria uma página separada.

Publicações NÃO entram por aqui: o campo DOI do Lattes vem vazio. Elas são
colhidas pela rotina de ORCID + CrossRef, que é uma fonte paralela.
"""

import datetime
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.html import escape
from django.utils.text import Truncator, slugify
from wagtail.rich_text import RichText

from apps.pesquisa.models import ProjetoPage, ProjetosIndexPage
from apps.pessoas.models import AreaConhecimento, DocentePage, DocentesIndexPage

# Cada elemento de <FORMACAO-ACADEMICA-TITULACAO> vira uma das TITULACAO_CHOICES.
# O peso serve para escolher a mais alta entre as formações CONCLUÍDAS — curso em
# andamento não confere título. Livre-docência entra como doutorado porque
# pressupõe o doutorado e não existe como opção própria em choices.py.
TITULACAO_POR_FORMACAO = {
    "GRADUACAO": ("graduacao", 1),
    "GRADUACAO-SANDUICHE": ("graduacao", 1),
    "APERFEICOAMENTO": ("especializacao", 2),
    "ESPECIALIZACAO": ("especializacao", 2),
    "RESIDENCIA-MEDICA": ("especializacao", 2),
    "MESTRADO": ("mestrado", 3),
    "MESTRADO-PROFISSIONALIZANTE": ("mestrado", 3),
    "DOUTORADO": ("doutorado", 4),
    "DOUTORADO-SANDUICHE": ("doutorado", 4),
    "LIVRE-DOCENCIA": ("doutorado", 4),
    "POS-DOUTORADO": ("pos_doutor", 5),
}

# NATUREZA do CNPq → TIPO_PROJETO_CHOICES. PIBIC, PIBEX e TCC não existem como
# natureza no Lattes; ficam a cargo da comissão na revisão do rascunho.
NATUREZA_PARA_TIPO = {
    "PESQUISA": "pesquisa",
    "EXTENSAO": "extensao",
    "ENSINO": "ensino",
    "DESENVOLVIMENTO": "pesquisa",
    "OUTRA": "pesquisa",
}

# SITUACAO do CNPq → STATUS_PROJETO_CHOICES. "submetido" não tem equivalente:
# o Lattes só registra projeto que já começou.
SITUACAO_PARA_STATUS = {
    "EM_ANDAMENTO": "em_andamento",
    "CONCLUIDO": "concluido",
    "DESATIVADO": "suspenso",
    "OUTRO": "em_andamento",
}

LATTES_URL = "http://lattes.cnpq.br/{}"


# ---------------------------------------------------------------------------
# Estruturas do parser — sem Django, para poderem ser testadas sem banco
# ---------------------------------------------------------------------------

@dataclass
class Integrante:
    """Um participante da equipe do projeto, como consta no XML."""

    nome: str
    id_lattes: str
    responsavel: bool


@dataclass
class ProjetoLattes:
    """Um <PROJETO-DE-PESQUISA>, já mapeado para o vocabulário do portal."""

    nome: str
    tipo: str
    status: str
    ano_inicio: int
    ano_fim: int | None
    descricao: str
    integrantes: list[Integrante] = field(default_factory=list)
    natureza_original: str = ""

    @property
    def responsavel(self) -> Integrante | None:
        return next((i for i in self.integrantes if i.responsavel), None)

    @property
    def data_inicio(self) -> datetime.date:
        return datetime.date(self.ano_inicio, 1, 1)

    @property
    def data_fim(self) -> datetime.date | None:
        return datetime.date(self.ano_fim, 12, 31) if self.ano_fim else None


@dataclass
class PerfilLattes:
    """Os <DADOS-GERAIS> que alimentam a DocentePage."""

    id_lattes: str
    nome_completo: str
    email: str
    titulacao: str
    instituicao_titulacao: str
    areas: list[str] = field(default_factory=list)
    bio: str = ""
    titulacao_encontrada: bool = True


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def resumir(texto: str, limite: int = 250) -> str:
    """Corta o texto no limite de caracteres, sem partir palavra.

    O `.strip()` não é decorativo: o `Truncator.chars()` do Django 5.1 devolve o
    resultado com um espaço à esquerda, que apareceria no começo de todo card
    de listagem.
    """
    return Truncator(texto).chars(limite).strip()


def _ano(valor: str) -> int | None:
    """Converte um atributo de ano do Lattes em int, tolerando vazio e lixo."""
    valor = (valor or "").strip()
    return int(valor) if valor.isdigit() and len(valor) == 4 else None


def parse_perfil(raiz: ET.Element) -> PerfilLattes:
    """Extrai o perfil do docente da raiz <CURRICULO-VITAE>."""
    dados = raiz.find("DADOS-GERAIS")
    if dados is None:
        raise CommandError("XML sem <DADOS-GERAIS> — não parece um Currículo Lattes.")

    titulacao, instituicao, encontrada = _parse_titulacao(dados)

    endereco = dados.find("ENDERECO/ENDERECO-PROFISSIONAL")
    email = endereco.get("E-MAIL", "").strip() if endereco is not None else ""

    resumo = dados.find("RESUMO-CV")
    bio = resumo.get("TEXTO-RESUMO-CV-RH", "").strip() if resumo is not None else ""

    return PerfilLattes(
        id_lattes=raiz.get("NUMERO-IDENTIFICADOR", "").strip(),
        nome_completo=dados.get("NOME-COMPLETO", "").strip(),
        email=email,
        titulacao=titulacao,
        instituicao_titulacao=instituicao,
        areas=_parse_areas(dados),
        bio=bio,
        titulacao_encontrada=encontrada,
    )


def _parse_titulacao(dados: ET.Element) -> tuple[str, str, bool]:
    """Devolve a titulação mais alta já concluída e a instituição que a conferiu."""
    formacoes = dados.find("FORMACAO-ACADEMICA-TITULACAO")
    melhor_peso = 0
    melhor = ("graduacao", "")

    for elemento in formacoes if formacoes is not None else []:
        mapeada = TITULACAO_POR_FORMACAO.get(elemento.tag)
        if not mapeada or elemento.get("STATUS-DO-CURSO", "") != "CONCLUIDO":
            continue
        titulacao, peso = mapeada
        if peso > melhor_peso:
            melhor_peso = peso
            melhor = (titulacao, elemento.get("NOME-INSTITUICAO", "").strip())

    return melhor[0], melhor[1], melhor_peso > 0


def _parse_areas(dados: ET.Element) -> list[str]:
    """Lista as áreas de conhecimento, sem repetir e preservando a ordem do XML.

    Usa NOME-DA-AREA-DO-CONHECIMENTO e ignora a sub-área: no XML real as
    sub-áreas são muito específicas ("Help Desk", "Tutoria") e cinco entradas
    costumam colapsar em uma única área.
    """
    elemento = dados.find("AREAS-DE-ATUACAO")
    areas: list[str] = []
    for area in elemento if elemento is not None else []:
        nome = area.get("NOME-DA-AREA-DO-CONHECIMENTO", "").strip()
        if nome and nome not in areas:
            areas.append(nome)
    return areas


def parse_projetos(raiz: ET.Element) -> list[ProjetoLattes]:
    """Extrai todos os <PROJETO-DE-PESQUISA>, incluindo os de extensão e ensino.

    Apesar do nome do elemento, o CNPq guarda todas as naturezas de projeto aí,
    aninhados sob as atuações profissionais.
    """
    projetos = []
    for no in raiz.findall(".//PROJETO-DE-PESQUISA"):
        nome = no.get("NOME-DO-PROJETO", "").strip()
        ano_inicio = _ano(no.get("ANO-INICIO", ""))
        if not nome or not ano_inicio:
            continue

        natureza = no.get("NATUREZA", "").strip()
        situacao = no.get("SITUACAO", "").strip()

        projetos.append(ProjetoLattes(
            nome=nome,
            tipo=NATUREZA_PARA_TIPO.get(natureza, "pesquisa"),
            status=SITUACAO_PARA_STATUS.get(situacao, "em_andamento"),
            ano_inicio=ano_inicio,
            ano_fim=_ano(no.get("ANO-FIM", "")),
            descricao=" ".join(no.get("DESCRICAO-DO-PROJETO", "").split()),
            integrantes=_parse_integrantes(no),
            natureza_original=natureza,
        ))
    return projetos


def _parse_integrantes(projeto: ET.Element) -> list[Integrante]:
    """Lê a equipe do projeto na ordem de integração declarada no Lattes."""
    integrantes = []
    for no in projeto.findall("EQUIPE-DO-PROJETO/INTEGRANTES-DO-PROJETO"):
        nome = no.get("NOME-COMPLETO", "").strip()
        if not nome:
            continue
        integrantes.append(Integrante(
            nome=nome,
            id_lattes=no.get("NRO-ID-CNPQ", "").strip(),
            responsavel=no.get("FLAG-RESPONSAVEL", "") == "SIM",
        ))
    return integrantes


# ---------------------------------------------------------------------------
# Comando
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Importa perfil e projetos de um XML do Lattes como rascunho."

    def add_arguments(self, parser) -> None:
        parser.add_argument("arquivo", help="Caminho do XML exportado do Lattes.")
        parser.add_argument(
            "--email",
            default="",
            help=(
                "E-mail institucional do docente. Sobrepõe o e-mail do XML, que"
                " costuma ser pessoal. Obrigatório se o XML não trouxer nenhum."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra o que seria importado e desfaz tudo no final.",
        )

    def handle(self, *args, **options) -> None:
        caminho = Path(options["arquivo"]).expanduser().resolve()
        if not caminho.is_file():
            raise CommandError(f"Arquivo não encontrado: {caminho}")

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== importar_lattes ===\n"))
        self._avisar_se_dentro_da_raiz_web(caminho)

        try:
            raiz = ET.parse(caminho).getroot()
        except ET.ParseError as erro:
            raise CommandError(f"XML inválido: {erro}") from erro

        if raiz.tag != "CURRICULO-VITAE":
            raise CommandError(
                f"Raiz do XML é <{raiz.tag}>, esperava <CURRICULO-VITAE>."
            )

        perfil = parse_perfil(raiz)
        projetos = parse_projetos(raiz)

        with transaction.atomic():
            docente = self._importar_docente(perfil, options["email"])
            self._importar_projetos(projetos, docente)

            if options["dry_run"]:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING(
                    "\n--dry-run: nada foi gravado no banco.\n"
                ))
                return

        self.stdout.write(self.style.SUCCESS(
            "\n✓ Importado como rascunho. Revise em /admin/pages/ e publique."
            "\n  Depois de conferir, apague o XML — ele contém dados pessoais.\n"
        ))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ok(self, texto: str) -> None:
        self.stdout.write(f"  ✓ {texto}")

    def _aviso(self, texto: str) -> None:
        self.stdout.write(self.style.WARNING(f"  ✗ {texto}"))

    def _avisar_se_dentro_da_raiz_web(self, caminho: Path) -> None:
        """Alerta se o XML está sob MEDIA_ROOT, servido sem autenticação."""
        media = Path(str(settings.MEDIA_ROOT)).expanduser().resolve()
        if media.exists() and caminho.is_relative_to(media):
            self.stdout.write(self.style.WARNING(
                f"  ! O XML está em {media} — em produção o Nginx serve esse\n"
                "    diretório sem autenticação e o arquivo, que tem CPF e\n"
                "    telefone, fica publicamente acessível. Mova-o para fora.\n"
            ))

    def _salvar_como_rascunho(self, pagina) -> None:
        """Registra a alteração como revisão à espera de revisão da comissão.

        Página já publicada recebe só a revisão — o que está no ar não muda até
        alguém publicar. Página ainda em rascunho recebe também o `save()`:
        sem ele o registro ficaria com os dados da rodada anterior e só a
        revisão teria os novos, o que confunde quem abre a listagem do admin.

        O `title` e o `slug` nunca são reescritos: eles formam a URL da página e
        são a chave de deduplicação entre rodadas.
        """
        if not pagina.live:
            pagina.save()
        pagina.save_revision()

    def _slug_livre(self, pai, base: str) -> str:
        """Gera um slug único entre os filhos de `pai`, como o Wagtail faria."""
        slug = slugify(base)[:240] or "sem-titulo"
        candidato, n = slug, 1
        while pai.get_children().filter(slug=candidato).exists():
            n += 1
            candidato = f"{slug}-{n}"
        return candidato

    def _buscar_docente(self, id_lattes: str, nome: str) -> DocentePage | None:
        """Localiza um docente pelo ID do Lattes e, se falhar, pelo nome.

        Inclui rascunhos: um perfil importado numa rodada anterior e ainda não
        publicado precisa ser reconhecido, senão a importação duplica.
        """
        if id_lattes:
            achado = DocentePage.objects.filter(lattes_url__contains=id_lattes).first()
            if achado:
                return achado
        return DocentePage.objects.filter(nome_completo__iexact=nome).first() if nome else None

    # ------------------------------------------------------------------
    # Docente
    # ------------------------------------------------------------------

    def _importar_docente(self, perfil: PerfilLattes, email_opcao: str) -> DocentePage:
        self.stdout.write(self.style.MIGRATE_HEADING("Docente"))

        if not perfil.nome_completo:
            raise CommandError("O XML não traz NOME-COMPLETO em <DADOS-GERAIS>.")

        existente = self._buscar_docente(perfil.id_lattes, perfil.nome_completo)

        email = email_opcao or perfil.email
        if not email and existente is None:
            raise CommandError(
                "Nenhum e-mail no XML e nenhum --email informado. O campo é"
                " obrigatório na DocentePage — rode de novo com"
                " --email nome@ifsertao-pe.edu.br"
            )

        if not perfil.titulacao_encontrada:
            self._aviso(
                "nenhuma formação concluída no XML — titulação veio como"
                " 'Graduação'. Confira no rascunho."
            )

        areas = self._garantir_areas(perfil.areas)
        bio = f"<p>{escape(perfil.bio)}</p>" if perfil.bio else ""

        if existente:
            docente = existente
            docente.nome_completo = perfil.nome_completo
            docente.titulacao = perfil.titulacao
            docente.instituicao_titulacao = perfil.instituicao_titulacao
            if bio:
                docente.bio = bio
            if perfil.id_lattes:
                docente.lattes_url = LATTES_URL.format(perfil.id_lattes)
            # O e-mail só é sobrescrito quando a comissão passa --email: o que
            # está na página costuma ser a correção institucional do e-mail
            # pessoal que vem do Lattes.
            if email_opcao:
                docente.email = email_opcao
            if areas:
                docente.areas_conhecimento.set(areas)

            self._salvar_como_rascunho(docente)
            self._ok(f"{docente.nome_completo} — atualizado (rascunho para revisão)")
            return docente

        index = DocentesIndexPage.objects.first()
        if not index:
            raise CommandError(
                "DocentesIndexPage não existe na árvore. Rode `bootstrap_site` antes."
            )

        docente = index.add_child(instance=DocentePage(
            title=perfil.nome_completo,
            slug=self._slug_livre(index, perfil.nome_completo),
            nome_completo=perfil.nome_completo,
            email=email,
            lattes_url=LATTES_URL.format(perfil.id_lattes) if perfil.id_lattes else "",
            titulacao=perfil.titulacao,
            instituicao_titulacao=perfil.instituicao_titulacao,
            bio=bio,
            live=False,
        ))
        if areas:
            docente.areas_conhecimento.set(areas)
            docente.save()
        docente.save_revision()
        self._ok(f"{docente.nome_completo} — criado como rascunho")
        return docente

    def _garantir_areas(self, nomes: list[str]) -> list[AreaConhecimento]:
        """Cria as áreas de conhecimento que ainda não existirem como snippet."""
        areas = []
        for nome in nomes:
            area, criada = AreaConhecimento.objects.get_or_create(
                slug=slugify(nome)[:50], defaults={"nome": nome},
            )
            if criada:
                self._ok(f"área de conhecimento criada: {area.nome}")
            areas.append(area)
        return areas

    # ------------------------------------------------------------------
    # Projetos
    # ------------------------------------------------------------------

    def _importar_projetos(self, projetos: list[ProjetoLattes], dono: DocentePage) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("\nProjetos"))

        if not projetos:
            self.stdout.write("  → nenhum projeto no XML")
            return

        index = ProjetosIndexPage.objects.first()
        if not index:
            raise CommandError(
                "ProjetosIndexPage não existe na árvore. Rode `bootstrap_site` antes."
            )

        sem_perfil: list[tuple[str, str]] = []
        externos: set[str] = set()

        for projeto in projetos:
            responsavel = projeto.responsavel
            if responsavel is None:
                sem_perfil.append((projeto.nome, "nenhum integrante marcado como responsável"))
                continue

            coordenador = self._buscar_docente(responsavel.id_lattes, responsavel.nome)
            if coordenador is None:
                sem_perfil.append((projeto.nome, responsavel.nome))
                continue

            participantes, nao_encontrados = self._resolver_participantes(projeto, coordenador)
            externos.update(nao_encontrados)
            self._gravar_projeto(index, projeto, coordenador, participantes)

        self._relatar_pendencias(sem_perfil, externos, dono)

    def _resolver_participantes(
        self, projeto: ProjetoLattes, coordenador: DocentePage,
    ) -> tuple[list[DocentePage], list[str]]:
        """Casa a equipe do XML com perfis do portal; devolve também quem sobrou.

        Quem sobra é geralmente estudante ou pesquisador externo —
        `participantes_docentes` só aceita DocentePage.
        """
        encontrados, faltantes = [], []
        for integrante in projeto.integrantes:
            if integrante.responsavel:
                continue
            docente = self._buscar_docente(integrante.id_lattes, integrante.nome)
            if docente and docente.pk != coordenador.pk:
                encontrados.append(docente)
            elif not docente:
                faltantes.append(integrante.nome)
        return encontrados, faltantes

    def _gravar_projeto(
        self,
        index: ProjetosIndexPage,
        projeto: ProjetoLattes,
        coordenador: DocentePage,
        participantes: list[DocentePage],
    ) -> None:
        campos = {
            "tipo": projeto.tipo,
            "status": projeto.status,
            "data_inicio": projeto.data_inicio,
            "data_fim": projeto.data_fim,
            "coordenador": coordenador,
            # O Lattes não guarda resumo curto: o texto longo vira a descrição e
            # os primeiros 250 caracteres viram o resumo dos cards de listagem.
            "resumo": resumir(projeto.descricao or projeto.nome),
            "descricao": (
                [("paragrafo", RichText(f"<p>{escape(projeto.descricao)}</p>"))]
                if projeto.descricao else []
            ),
        }

        slug = slugify(projeto.nome)[:240]
        existente = index.get_children().filter(slug=slug).first()

        if existente:
            pagina = existente.specific
            for nome_campo, valor in campos.items():
                setattr(pagina, nome_campo, valor)
            pagina.participantes_docentes.set(participantes)
            self._salvar_como_rascunho(pagina)
            self._ok(f"{projeto.nome} — atualizado (rascunho para revisão)")
            return

        pagina = index.add_child(instance=ProjetoPage(
            title=projeto.nome,
            slug=self._slug_livre(index, projeto.nome),
            live=False,
            **campos,
        ))
        if participantes:
            pagina.participantes_docentes.set(participantes)
            pagina.save()
        pagina.save_revision()

        aviso = ""
        if projeto.natureza_original not in ("PESQUISA", "EXTENSAO", "ENSINO"):
            aviso = f"  (natureza '{projeto.natureza_original}' → Pesquisa, confira)"
        self._ok(f"{projeto.nome} — criado como rascunho{aviso}")

    def _relatar_pendencias(
        self, sem_perfil: list[tuple[str, str]], externos: set[str], dono: DocentePage,
    ) -> None:
        """Lista o que ficou de fora, para a comissão decidir o que fazer."""
        if sem_perfil:
            self.stdout.write(self.style.WARNING(
                f"\n  {len(sem_perfil)} projeto(s) não importado(s) — o coordenador"
                " precisa ter perfil no portal:"
            ))
            for nome_projeto, responsavel in sem_perfil:
                self.stdout.write(f"    · {nome_projeto}")
                self.stdout.write(f"      coordenado por: {responsavel}")
            self.stdout.write(
                "    Importe o Lattes dessas pessoas (ou cadastre o perfil) e"
                f" rode de novo o XML de {dono.nome_completo}."
            )

        if externos:
            self.stdout.write(self.style.WARNING(
                f"\n  {len(externos)} integrante(s) sem perfil ficaram de fora da"
                " equipe (estudantes ou externos, que o model não comporta):"
            ))
            for nome in sorted(externos):
                self.stdout.write(f"    · {nome}")
