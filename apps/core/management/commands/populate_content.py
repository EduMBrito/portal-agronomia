import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.ensino.models import DisciplinaPage, DisciplinasIndexPage
from apps.institucional.models import EventoPage, EventosIndexPage
from apps.noticias.models import PostPage, PostsIndexPage
from apps.pesquisa.models import (
    ProjetoPage,
    ProjetosIndexPage,
    PublicacaoPage,
    PublicacoesIndexPage,
)
from apps.pessoas.models import AreaConhecimento, DocentePage, DocentesIndexPage


class Command(BaseCommand):
    help = "Popula o portal com dados de exemplo para demonstração."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== populate_content ===\n"))

        self.stdout.write(self.style.MIGRATE_HEADING("Áreas de Conhecimento"))
        areas = self._criar_areas()

        self.stdout.write(self.style.MIGRATE_HEADING("\nDocentes"))
        docentes = self._criar_docentes(areas)

        if not docentes:
            self.stdout.write(self.style.WARNING(
                "Nenhum docente criado — as seções seguintes dependem de docentes. "
                "Verifique se DocentesIndexPage existe na árvore do Wagtail."
            ))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("\nDisciplinas"))
        self._criar_disciplinas(docentes)

        self.stdout.write(self.style.MIGRATE_HEADING("\nProjetos"))
        self._criar_projetos(docentes)

        self.stdout.write(self.style.MIGRATE_HEADING("\nPublicações"))
        self._criar_publicacoes(docentes)

        self.stdout.write(self.style.MIGRATE_HEADING("\nPosts"))
        self._criar_posts(docentes)

        self.stdout.write(self.style.MIGRATE_HEADING("\nEventos"))
        self._criar_eventos(docentes)

        self.stdout.write(self.style.SUCCESS(
            "\n✓ Concluído. Acesse /admin/ para revisar e editar o conteúdo criado.\n"
        ))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ok(self, titulo):
        self.stdout.write(f"  ✓ {titulo}")

    def _skip(self, slug):
        self.stdout.write(f"  → já existe: {slug}")

    def _add_page(self, parent, instance):
        """Cria página filha se não existir. Retorna instância salva."""
        existing = parent.get_children().filter(slug=instance.slug).first()
        if existing:
            self._skip(instance.slug)
            return existing.specific
        page = parent.add_child(instance=instance)
        self._ok(instance.title)
        return page

    def _get_index(self, PageType):
        index = PageType.objects.live().first()
        if not index:
            self.stdout.write(self.style.WARNING(
                f"  ✗ {PageType._meta.verbose_name} não encontrada na árvore."
                " Crie-a no admin antes de rodar este comando."
            ))
        return index

    # ------------------------------------------------------------------
    # Áreas de Conhecimento
    # ------------------------------------------------------------------

    def _criar_areas(self):
        dados = [
            ("Fitotecnia",                  "fitotecnia"),
            ("Zootecnia",                   "zootecnia"),
            ("Solos e Nutrição de Plantas", "solos-nutricao"),
            ("Irrigação e Drenagem",        "irrigacao-drenagem"),
            ("Mecanização Agrícola",        "mecanizacao-agricola"),
            ("Agroecologia",                "agroecologia"),
            ("Fruticultura",                "fruticultura"),
            ("Defesa Fitossanitária",       "defesa-fitossanitaria"),
        ]
        areas = {}
        for nome, slug in dados:
            area, created = AreaConhecimento.objects.get_or_create(
                slug=slug, defaults={"nome": nome}
            )
            if created:
                self._ok(nome)
            else:
                self._skip(slug)
            areas[slug] = area
        return areas

    # ------------------------------------------------------------------
    # Docentes
    # ------------------------------------------------------------------

    def _criar_docentes(self, areas):
        index = self._get_index(DocentesIndexPage)
        if not index:
            return []

        dados = [
            {
                "title": "Prof. Dr. Carlos Eduardo Ferreira",
                "slug": "carlos-ferreira",
                "nome_completo": "Carlos Eduardo Ferreira",
                "email": "carlos.ferreira@ifsertao.edu.br",
                "lattes_url": "https://lattes.cnpq.br/0000000000000001",
                "orcid": "0000-0001-0000-0001",
                "titulacao": "doutorado",
                "instituicao_titulacao": "Universidade Federal de Viçosa (UFV)",
                "areas": ["fitotecnia", "solos-nutricao"],
                "bio": (
                    "<p>Doutor em Fitotecnia pela UFV, com ênfase em fisiologia de culturas "
                    "adaptadas ao Semiárido. Desenvolve pesquisas com milho, sorgo e feijão-caupi "
                    "sob condições de déficit hídrico. Atua como coordenador do grupo de pesquisa "
                    "em Produção Vegetal do Campus Petrolina Zona Rural.</p>"
                ),
            },
            {
                "title": "Profa. Dra. Ana Paula Rodrigues",
                "slug": "ana-paula-rodrigues",
                "nome_completo": "Ana Paula Rodrigues",
                "email": "ana.rodrigues@ifsertao.edu.br",
                "lattes_url": "https://lattes.cnpq.br/0000000000000002",
                "orcid": "0000-0001-0000-0002",
                "titulacao": "doutorado",
                "instituicao_titulacao": "Universidade Federal Rural de Pernambuco (UFRPE)",
                "areas": ["zootecnia", "agroecologia"],
                "bio": (
                    "<p>Doutora em Zootecnia pela UFRPE, especializada em sistemas de produção "
                    "animal sustentáveis no Semiárido. Pesquisa a integração lavoura-pecuária "
                    "em bases agroecológicas e coordena o projeto de extensão Horta Comunitária "
                    "no assentamento vizinho ao campus.</p>"
                ),
            },
            {
                "title": "Prof. Dr. Marcos Antônio Lima",
                "slug": "marcos-lima",
                "nome_completo": "Marcos Antônio Lima",
                "email": "marcos.lima@ifsertao.edu.br",
                "lattes_url": "https://lattes.cnpq.br/0000000000000003",
                "orcid": "",
                "titulacao": "doutorado",
                "instituicao_titulacao": "Universidade Federal do Vale do São Francisco (UNIVASF)",
                "areas": ["irrigacao-drenagem", "mecanizacao-agricola"],
                "bio": (
                    "<p>Doutor em Engenharia Agrícola pela UNIVASF, com foco em eficiência "
                    "do uso da água em sistemas irrigados do Polo Petrolina-Juazeiro. "
                    "Responsável pelo Laboratório de Hidráulica e Mecanização do campus.</p>"
                ),
            },
            {
                "title": "Profa. Ma. Fernanda Costa Souza",
                "slug": "fernanda-souza",
                "nome_completo": "Fernanda Costa Souza",
                "email": "fernanda.souza@ifsertao.edu.br",
                "lattes_url": "https://lattes.cnpq.br/0000000000000004",
                "orcid": "",
                "titulacao": "mestrado",
                "instituicao_titulacao": "Universidade Federal do Vale do São Francisco (UNIVASF)",
                "areas": ["fruticultura", "defesa-fitossanitaria"],
                "bio": (
                    "<p>Mestra em Horticultura Irrigada, com experiência em produção de manga, "
                    "uva e goiaba no Vale do São Francisco. Atua na identificação e manejo de "
                    "pragas e doenças em fruteiras tropicais, com ênfase no controle biológico.</p>"
                ),
            },
        ]

        docentes = []
        for d in dados:
            page = self._add_page(index, DocentePage(
                title=d["title"],
                slug=d["slug"],
                nome_completo=d["nome_completo"],
                email=d["email"],
                lattes_url=d.get("lattes_url", ""),
                orcid=d.get("orcid", ""),
                titulacao=d["titulacao"],
                instituicao_titulacao=d["instituicao_titulacao"],
                bio=d["bio"],
                live=True,
            ))
            # Vincula áreas (ParentalManyToManyField requer .save() para persistir)
            for slug in d["areas"]:
                if slug in areas:
                    page.areas_conhecimento.add(areas[slug])
            page.save()
            docentes.append(page)

        return docentes

    # ------------------------------------------------------------------
    # Disciplinas
    # ------------------------------------------------------------------

    def _criar_disciplinas(self, docentes):
        index = self._get_index(DisciplinasIndexPage)
        if not index:
            return

        carlos, _, marcos, fernanda = docentes[0], docentes[1], docentes[2], docentes[3]

        dados = [
            {
                "title": "Botânica Agrícola",
                "slug": "botanica-agricola",
                "codigo": "AGR-101", "carga_horaria": 60, "periodo": 1,
                "docente": carlos,
                "ementa": (
                    "<p>Morfologia e anatomia vegetal aplicadas à identificação de plantas "
                    "cultivadas e daninhas. Sistemática das principais famílias de interesse "
                    "agronômico. Fisiologia do crescimento e desenvolvimento vegetal.</p>"
                ),
            },
            {
                "title": "Química Geral e Orgânica",
                "slug": "quimica-geral-organica",
                "codigo": "AGR-102", "carga_horaria": 60, "periodo": 1,
                "docente": None,
                "ementa": (
                    "<p>Estrutura atômica e ligações químicas. Funções orgânicas de interesse "
                    "agrícola. Reações químicas aplicadas aos processos do solo e da planta.</p>"
                ),
            },
            {
                "title": "Física e Classificação do Solo",
                "slug": "fisica-classificacao-solo",
                "codigo": "AGR-201", "carga_horaria": 60, "periodo": 2,
                "docente": carlos,
                "ementa": (
                    "<p>Origem e formação dos solos. Propriedades físicas: textura, estrutura e "
                    "consistência. Sistema Brasileiro de Classificação de Solos. "
                    "Levantamento e mapeamento de solos.</p>"
                ),
            },
            {
                "title": "Irrigação e Drenagem",
                "slug": "irrigacao-drenagem",
                "codigo": "AGR-301", "carga_horaria": 60, "periodo": 3,
                "docente": marcos,
                "ementa": (
                    "<p>Fundamentos da hidráulica agrícola. Sistemas de irrigação por "
                    "superfície, aspersão e gotejamento. Manejo da irrigação baseado em "
                    "evapotranspiração. Drenagem superficial e subsuperficial.</p>"
                ),
            },
            {
                "title": "Nutrição Mineral de Plantas",
                "slug": "nutricao-mineral-plantas",
                "codigo": "AGR-302", "carga_horaria": 60, "periodo": 3,
                "docente": carlos,
                "ementa": (
                    "<p>Elementos essenciais às plantas. Dinâmica de nutrientes no solo. "
                    "Diagnose foliar e análise de solo para recomendação de adubação. "
                    "Fertirrigação em culturas irrigadas.</p>"
                ),
            },
            {
                "title": "Fruticultura Tropical",
                "slug": "fruticultura-tropical",
                "codigo": "AGR-501", "carga_horaria": 60, "periodo": 5,
                "docente": fernanda,
                "ementa": (
                    "<p>Aspectos botânicos e ecofisiológicos das principais fruteiras tropicais. "
                    "Técnicas de cultivo de manga, uva, goiaba, banana e maracujá. "
                    "Colheita, pós-colheita e comercialização.</p>"
                ),
            },
            {
                "title": "Defesa Fitossanitária",
                "slug": "defesa-fitossanitaria",
                "codigo": "AGR-701", "carga_horaria": 60, "periodo": 7,
                "docente": fernanda,
                "ementa": (
                    "<p>Fundamentos de fitopatologia e entomologia agrícola. "
                    "Manejo Integrado de Pragas (MIP). Defensivos agrícolas: classificação, "
                    "registro e uso seguro. Controle biológico de pragas e doenças.</p>"
                ),
            },
            {
                "title": "Estágio Supervisionado",
                "slug": "estagio-supervisionado",
                "codigo": "AGR-901", "carga_horaria": 120, "periodo": 9,
                "docente": None,
                "ementa": (
                    "<p>Atividade prática supervisionada em empresas, propriedades rurais, "
                    "órgãos públicos ou entidades de pesquisa. Relatório técnico de estágio "
                    "e apresentação pública dos resultados.</p>"
                ),
            },
        ]

        for d in dados:
            self._add_page(index, DisciplinaPage(
                title=d["title"],
                slug=d["slug"],
                codigo=d["codigo"],
                carga_horaria=d["carga_horaria"],
                periodo=d["periodo"],
                ementa=d["ementa"],
                docente_responsavel=d["docente"],
                live=True,
            ))

    # ------------------------------------------------------------------
    # Projetos
    # ------------------------------------------------------------------

    def _criar_projetos(self, docentes):
        index = self._get_index(ProjetosIndexPage)
        if not index:
            return

        carlos, ana, marcos, fernanda = docentes[0], docentes[1], docentes[2], docentes[3]
        hoje = datetime.date.today()

        dados = [
            {
                "title": "Cultivo de Sorgo e Milho sob Déficit Hídrico no Semiárido",
                "slug": "sorgo-milho-deficit-hidrico",
                "tipo": "pesquisa",
                "status": "em_andamento",
                "resumo": (
                    "Avalia genótipos de sorgo granífero e milho submetidos a regimes "
                    "hídricos reduzidos, visando identificar materiais tolerantes à seca "
                    "para o Semiárido pernambucano."
                ),
                "data_inicio": hoje - datetime.timedelta(days=300),
                "data_fim": None,
                "coordenador": carlos,
                "participantes": [marcos],
                "financiador": "CNPq — Edital Universal 2023",
            },
            {
                "title": "Horta Comunitária e Segurança Alimentar na Zona Rural",
                "slug": "horta-comunitaria-zona-rural",
                "tipo": "extensao",
                "status": "concluido",
                "resumo": (
                    "Implantação e acompanhamento de hortas agroecológicas em famílias "
                    "de assentamento rural próximo ao campus, com foco em soberania "
                    "alimentar e geração de renda."
                ),
                "data_inicio": hoje - datetime.timedelta(days=540),
                "data_fim": hoje - datetime.timedelta(days=60),
                "coordenador": ana,
                "participantes": [fernanda],
                "financiador": "IFSertãoPE — Programa de Extensão Institucional",
            },
            {
                "title": "Manejo da Irrigação por Gotejamento em Culturas Frutíferas",
                "slug": "irrigacao-gotejamento-frutiferas",
                "tipo": "pibic",
                "status": "em_andamento",
                "resumo": (
                    "Monitora a eficiência do uso da água em sistemas de gotejamento "
                    "subsuperficial em plantios de goiaba e acerola, comparando "
                    "estratégias de manejo baseadas em sensores de umidade do solo."
                ),
                "data_inicio": hoje - datetime.timedelta(days=180),
                "data_fim": hoje + datetime.timedelta(days=185),
                "coordenador": marcos,
                "participantes": [carlos, fernanda],
                "financiador": "FACEPE — PIBIC 2024/2025",
            },
        ]

        for d in dados:
            projeto = self._add_page(index, ProjetoPage(
                title=d["title"],
                slug=d["slug"],
                tipo=d["tipo"],
                status=d["status"],
                resumo=d["resumo"],
                descricao=[],
                data_inicio=d["data_inicio"],
                data_fim=d["data_fim"],
                coordenador=d["coordenador"],
                financiador=d.get("financiador", ""),
                live=True,
            ))
            for p in d.get("participantes", []):
                projeto.participantes_docentes.add(p)
            projeto.save()

    # ------------------------------------------------------------------
    # Publicações
    # ------------------------------------------------------------------

    def _criar_publicacoes(self, docentes):
        index = self._get_index(PublicacoesIndexPage)
        if not index:
            return

        carlos, ana, marcos, fernanda = docentes[0], docentes[1], docentes[2], docentes[3]

        dados = [
            {
                "title": "Produtividade do Feijão-Caupi sob Diferentes Regimes de Irrigação",
                "slug": "feijao-caupi-regimes-irrigacao",
                "tipo": "artigo_periodico",
                "resumo": (
                    "Avalia o efeito de quatro lâminas de irrigação (50, 75, 100 e 125% da "
                    "ETc) sobre componentes de produção do feijão-caupi cv. BRS Guariba "
                    "cultivado no Submédio São Francisco."
                ),
                "autores_internos": [carlos, marcos],
                "autores_externos": "Souza, J. A.; Lima, P. C.",
                "veiculo": "Revista Brasileira de Engenharia Agrícola e Ambiental",
                "doi": "10.1590/1807-1929/agriambi.v28n00p000-000",
                "issn": "1807-1929",
                "data_publicacao": datetime.date(2024, 6, 15),
            },
            {
                "title": "Análise da Fertilidade de Solos em Assentamentos Rurais do Sertão",
                "slug": "fertilidade-solos-assentamentos-sertao",
                "tipo": "artigo_anais",
                "resumo": (
                    "Caracteriza atributos químicos de solos sob diferentes sistemas de uso "
                    "em assentamentos rurais do município de Petrolina-PE, subsidiando "
                    "recomendações de calagem e adubação para agricultores familiares."
                ),
                "autores_internos": [carlos, ana],
                "autores_externos": "",
                "veiculo": "Anais do Congresso Brasileiro de Ciência do Solo (CBCS 2023)",
                "doi": "",
                "issn": "",
                "data_publicacao": datetime.date(2023, 8, 22),
            },
            {
                "title": (
                    "Controle Biológico da Mosca-Branca em Culturas Hortícolas "
                    "no Vale do São Francisco"
                ),
                "slug": "controle-biologico-mosca-branca",
                "tipo": "artigo_periodico",
                "resumo": (
                    "Testa a eficácia de três agentes de controle biológico — Beauveria bassiana, "
                    "Metarhizium anisopliae e Encarsia formosa — no manejo de Bemisia tabaci "
                    "em cultivos de tomate e pimentão sob ambiente protegido."
                ),
                "autores_internos": [fernanda],
                "autores_externos": "Moraes, G. J.; Bettiol, W.",
                "veiculo": "Neotropical Entomology",
                "doi": "10.1007/s13744-024-00000-0",
                "issn": "1519-566X",
                "data_publicacao": datetime.date(2024, 3, 10),
            },
        ]

        for d in dados:
            pub = self._add_page(index, PublicacaoPage(
                title=d["title"],
                slug=d["slug"],
                tipo=d["tipo"],
                resumo=d["resumo"],
                corpo=[],
                autores_externos=d.get("autores_externos", ""),
                veiculo=d["veiculo"],
                doi=d.get("doi", ""),
                issn=d.get("issn", ""),
                data_publicacao=d["data_publicacao"],
                live=True,
            ))
            for docente in d.get("autores_internos", []):
                pub.autores_internos.add(docente)
            pub.save()

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------

    def _criar_posts(self, docentes):
        index = self._get_index(PostsIndexPage)
        if not index:
            return

        carlos, ana, _, _ = docentes[0], docentes[1], docentes[2], docentes[3]

        dados = [
            {
                "title": "Semiárido tem potencial para agricultura sustentável e inovação",
                "slug": "semiarido-potencial-agricultura-sustentavel",
                "autor": carlos,
                "resumo": (
                    "Pesquisas recentes demonstram que o Semiárido nordestino, longe de ser "
                    "apenas uma limitação, pode ser um laboratório vivo de inovação agrícola."
                ),
                "corpo": [
                    {
                        "type": "paragrafo",
                        "value": (
                            "<p>O Semiárido brasileiro abriga uma das regiões com maior "
                            "potencial para o desenvolvimento de agriculturas adaptadas, "
                            "resilientes e produtivas. Ao contrário do que se imagina, "
                            "a escassez hídrica força a criação de soluções que depois "
                            "se tornam referência mundial.</p>"
                        ),
                        "id": "block-post1-1",
                    },
                    {
                        "type": "paragrafo",
                        "value": (
                            "<p>No Campus Petrolina Zona Rural, pesquisadores têm trabalhado "
                            "com culturas adaptadas como o sorgo, o feijão-caupi e a palma "
                            "forrageira, mostrando que é possível produzir alimento e renda "
                            "mesmo com precipitações abaixo de 500 mm anuais.</p>"
                        ),
                        "id": "block-post1-2",
                    },
                ],
            },
            {
                "title": "Novos cultivares de feijão-caupi chegam ao campus para avaliação",
                "slug": "novos-cultivares-feijao-caupi",
                "autor": carlos,
                "resumo": (
                    "A Embrapa Meio-Norte firmou parceria com o IFSertãoPE para testar "
                    "seis novos materiais genéticos de feijão-caupi nas condições do Sertão."
                ),
                "corpo": [
                    {
                        "type": "paragrafo",
                        "value": (
                            "<p>A Embrapa Meio-Norte disponibilizou seis linhagens experimentais "
                            "de feijão-caupi ao Campus Petrolina Zona Rural para avaliação de "
                            "desempenho agronômico sob as condições edafoclimáticas do Sertão "
                            "pernambucano.</p>"
                        ),
                        "id": "block-post2-1",
                    },
                    {
                        "type": "paragrafo",
                        "value": (
                            "<p>Os ensaios, coordenados pelo Prof. Carlos Ferreira, serão "
                            "conduzidos em duas épocas de plantio e incluem avaliações de "
                            "produtividade, qualidade de grãos e tolerância à seca. "
                            "Os resultados alimentarão o banco de dados da rede nacional "
                            "de melhoramento da espécie.</p>"
                        ),
                        "id": "block-post2-2",
                    },
                ],
            },
            {
                "title": "Extensionistas do campus capacitam famílias em compostagem agroecológica",
                "slug": "capacitacao-compostagem-agroecologica",
                "autor": ana,
                "resumo": (
                    "Projeto de extensão levou oficinas práticas de compostagem e "
                    "biofertilizantes a 30 famílias rurais no município de Petrolina."
                ),
                "corpo": [
                    {
                        "type": "paragrafo",
                        "value": (
                            "<p>O projeto <em>Horta Comunitária e Segurança Alimentar</em>, "
                            "coordenado pela Profa. Ana Paula Rodrigues, encerrou seu ciclo "
                            "de capacitações com uma oficina de compostagem e produção de "
                            "biofertilizantes realizada no assentamento São Domingos, "
                            "em Petrolina-PE.</p>"
                        ),
                        "id": "block-post3-1",
                    },
                    {
                        "type": "paragrafo",
                        "value": (
                            "<p>Trinta famílias participaram das atividades, que incluíram "
                            "montagem de composteiras domésticas, preparo de caldas "
                            "repelentes naturais e orientações sobre adubação orgânica "
                            "para hortas. O material didático ficará disponível para "
                            "download neste portal.</p>"
                        ),
                        "id": "block-post3-2",
                    },
                ],
            },
        ]

        for d in dados:
            self._add_page(index, PostPage(
                title=d["title"],
                slug=d["slug"],
                autor=d["autor"],
                resumo=d["resumo"],
                corpo=d["corpo"],
                live=True,
            ))

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def _criar_eventos(self, docentes):
        index = self._get_index(EventosIndexPage)
        if not index:
            return

        carlos, ana, marcos, fernanda = docentes[0], docentes[1], docentes[2], docentes[3]
        agora = timezone.now()

        dados = [
            {
                "title": "Defesa de TCC — Análise da Qualidade de Solo em Área de Caatinga",
                "slug": "defesa-tcc-qualidade-solo-caatinga",
                "tipo": "defesa_tcc",
                "local": "Sala de Reuniões — Bloco Administrativo",
                "online": False,
                "data_inicio": agora - datetime.timedelta(days=30),
                "data_fim":    agora - datetime.timedelta(days=30, hours=-2),
                "docentes": [carlos],
                "descricao": (
                    "<p>Defesa de Trabalho de Conclusão de Curso do discente João Ferreira Lima. "
                    "Banca composta pelos professores Carlos Ferreira (orientador), "
                    "Marcos Lima e convidado externo da UNIVASF.</p>"
                ),
            },
            {
                "title": "Workshop de Manejo de Irrigação com Sensores",
                "slug": "workshop-manejo-irrigacao-sensores",
                "tipo": "workshop",
                "local": "Laboratório de Hidráulica — Campus Petrolina Zona Rural",
                "online": False,
                "data_inicio": agora - datetime.timedelta(days=10),
                "data_fim":    agora - datetime.timedelta(days=10, hours=-4),
                "docentes": [marcos],
                "descricao": (
                    "<p>Workshop prático sobre uso de sensores de umidade do solo (TDR e FDR) "
                    "para automação do manejo da irrigação. Atividade direcionada a produtores "
                    "rurais e estudantes do 5º ao 8º período do curso de Agronomia.</p>"
                ),
            },
            {
                "title": "Seminário de Agroecologia e Transição Produtiva no Semiárido",
                "slug": "seminario-agroecologia-transicao",
                "tipo": "seminario",
                "local": "Auditório Principal — IFSertãoPE Campus Petrolina Zona Rural",
                "online": True,
                "link_online": "https://meet.google.com/placeholder-agroecologia",
                "data_inicio": agora + datetime.timedelta(days=10),
                "data_fim":    agora + datetime.timedelta(days=10, hours=6),
                "docentes": [ana, carlos],
                "descricao": (
                    "<p>Seminário com palestras e mesas-redondas sobre experiências de "
                    "transição agroecológica em propriedades familiares do Sertão. "
                    "Evento híbrido: presencial e transmitido ao vivo.</p>"
                    "<p><strong>Entrada franca.</strong> Certificado para participantes "
                    "com presença mínima de 75%.</p>"
                ),
            },
            {
                "title": "Visita Técnica ao Polo Agrícola Petrolina-Juazeiro",
                "slug": "visita-tecnica-polo-petrolina-juazeiro",
                "tipo": "visita_tecnica",
                "local": "Empresas do Distrito de Irrigação Senador Nilo Coelho",
                "online": False,
                "data_inicio": agora + datetime.timedelta(days=22),
                "data_fim":    agora + datetime.timedelta(days=22, hours=8),
                "docentes": [marcos, fernanda],
                "descricao": (
                    "<p>Visita técnica às empresas produtoras de uva e manga do Polo "
                    "Petrolina-Juazeiro, com foco em sistemas de irrigação localizada, "
                    "manejo fitossanitário integrado e cadeia de exportação de frutas. "
                    "Atividade obrigatória para discentes do 6º período.</p>"
                ),
            },
        ]

        for d in dados:
            evento = self._add_page(index, EventoPage(
                title=d["title"],
                slug=d["slug"],
                tipo=d["tipo"],
                descricao=d["descricao"],
                data_inicio=d["data_inicio"],
                data_fim=d.get("data_fim"),
                local=d["local"],
                online=d.get("online", False),
                link_online=d.get("link_online", ""),
                live=True,
            ))
            for docente in d.get("docentes", []):
                evento.docentes_envolvidos.add(docente)
            evento.save()
