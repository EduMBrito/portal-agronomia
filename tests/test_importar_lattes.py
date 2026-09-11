"""Testes do comando `importar_lattes`.

A metade de cima cobre o parser puro, sem banco — é onde moram as regras de
tradução do vocabulário do CNPq para o do portal. A metade de baixo roda o
comando de ponta a ponta contra a árvore de páginas.
"""

import datetime
import xml.etree.ElementTree as ET
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core.management.commands.importar_lattes import (
    parse_perfil,
    parse_projetos,
    resumir,
)
from apps.pesquisa.models import ProjetoPage
from apps.pessoas.models import AreaConhecimento, DocentePage

# ---------------------------------------------------------------------------
# Fábrica de XML
# ---------------------------------------------------------------------------

XML_MINIMO = """<?xml version="1.0" encoding="UTF-8"?>
<CURRICULO-VITAE NUMERO-IDENTIFICADOR="1234567890123456">
  <DADOS-GERAIS NOME-COMPLETO="Maria Silva Andrade" CPF="00000000000">
    <RESUMO-CV TEXTO-RESUMO-CV-RH="Doutora em Fitotecnia. Atua com manejo."/>
    <ENDERECO>
      <ENDERECO-PROFISSIONAL E-MAIL="maria@pessoal.com" TELEFONE="99999999"/>
    </ENDERECO>
    <FORMACAO-ACADEMICA-TITULACAO>
      {formacao}
    </FORMACAO-ACADEMICA-TITULACAO>
    <AREAS-DE-ATUACAO>
      {areas}
    </AREAS-DE-ATUACAO>
    <ATUACOES-PROFISSIONAIS>
      <ATUACAO-PROFISSIONAL>
        <ATIVIDADES-DE-PARTICIPACAO-EM-PROJETO>
          <PARTICIPACAO-EM-PROJETO>
            {projetos}
          </PARTICIPACAO-EM-PROJETO>
        </ATIVIDADES-DE-PARTICIPACAO-EM-PROJETO>
      </ATUACAO-PROFISSIONAL>
    </ATUACOES-PROFISSIONAIS>
  </DADOS-GERAIS>
</CURRICULO-VITAE>
"""

FORMACAO_PADRAO = """
      <GRADUACAO STATUS-DO-CURSO="CONCLUIDO" NOME-INSTITUICAO="UNIVASF"/>
      <DOUTORADO STATUS-DO-CURSO="CONCLUIDO" NOME-INSTITUICAO="UFRPE"/>
"""

AREAS_PADRAO = """
      <AREA-DE-ATUACAO NOME-DA-AREA-DO-CONHECIMENTO="Agronomia"
                       NOME-DA-SUB-AREA-DO-CONHECIMENTO="Fitotecnia"/>
      <AREA-DE-ATUACAO NOME-DA-AREA-DO-CONHECIMENTO="Agronomia"
                       NOME-DA-SUB-AREA-DO-CONHECIMENTO="Irrigação"/>
"""

PROJETO_PADRAO = """
      <PROJETO-DE-PESQUISA NOME-DO-PROJETO="Manejo de Sorgo no Semiárido"
                           ANO-INICIO="2023" ANO-FIM=""
                           SITUACAO="EM_ANDAMENTO" NATUREZA="PESQUISA"
                           DESCRICAO-DO-PROJETO="Avalia cultivares de sorgo.">
        <EQUIPE-DO-PROJETO>
          <INTEGRANTES-DO-PROJETO NOME-COMPLETO="Maria Silva Andrade"
                                  NRO-ID-CNPQ="1234567890123456"
                                  ORDEM-DE-INTEGRACAO="1" FLAG-RESPONSAVEL="SIM"/>
          <INTEGRANTES-DO-PROJETO NOME-COMPLETO="Ana Beatriz Souza"
                                  NRO-ID-CNPQ="" ORDEM-DE-INTEGRACAO="2"
                                  FLAG-RESPONSAVEL="NAO"/>
        </EQUIPE-DO-PROJETO>
      </PROJETO-DE-PESQUISA>
"""


def montar_xml(formacao=FORMACAO_PADRAO, areas=AREAS_PADRAO, projetos=PROJETO_PADRAO):
    return XML_MINIMO.format(formacao=formacao, areas=areas, projetos=projetos)


def raiz(**kwargs):
    return ET.fromstring(montar_xml(**kwargs))


@pytest.fixture
def arquivo_xml(tmp_path):
    """Escreve o XML padrão em disco e devolve o caminho."""
    def _escrever(**kwargs):
        caminho = tmp_path / "curriculo.xml"
        caminho.write_text(montar_xml(**kwargs), encoding="utf-8")
        return str(caminho)
    return _escrever


def rodar(caminho, **opcoes):
    saida = StringIO()
    call_command("importar_lattes", caminho, stdout=saida, **opcoes)
    return saida.getvalue()


# ---------------------------------------------------------------------------
# Parser: perfil
# ---------------------------------------------------------------------------

def test_perfil_le_identificacao_basica():
    perfil = parse_perfil(raiz())

    assert perfil.nome_completo == "Maria Silva Andrade"
    assert perfil.id_lattes == "1234567890123456"
    assert perfil.bio.startswith("Doutora em Fitotecnia")


def test_perfil_escolhe_a_titulacao_mais_alta_concluida():
    perfil = parse_perfil(raiz())

    assert perfil.titulacao == "doutorado"
    assert perfil.instituicao_titulacao == "UFRPE"


def test_perfil_ignora_curso_em_andamento():
    formacao = """
      <GRADUACAO STATUS-DO-CURSO="CONCLUIDO" NOME-INSTITUICAO="UNIVASF"/>
      <DOUTORADO STATUS-DO-CURSO="EM_ANDAMENTO" NOME-INSTITUICAO="UFRPE"/>
    """
    perfil = parse_perfil(raiz(formacao=formacao))

    assert perfil.titulacao == "graduacao"
    assert perfil.instituicao_titulacao == "UNIVASF"


def test_perfil_sem_formacao_concluida_sinaliza_o_fallback():
    formacao = '<DOUTORADO STATUS-DO-CURSO="EM_ANDAMENTO" NOME-INSTITUICAO="UFRPE"/>'
    perfil = parse_perfil(raiz(formacao=formacao))

    assert perfil.titulacao == "graduacao"
    assert perfil.titulacao_encontrada is False


def test_perfil_mestrado_profissional_conta_como_mestrado():
    formacao = """
      <MESTRADO-PROFISSIONALIZANTE STATUS-DO-CURSO="CONCLUIDO"
                                   NOME-INSTITUICAO="CESAR School"/>
    """
    perfil = parse_perfil(raiz(formacao=formacao))

    assert perfil.titulacao == "mestrado"


def test_perfil_colapsa_areas_repetidas_preservando_a_ordem():
    perfil = parse_perfil(raiz())

    assert perfil.areas == ["Agronomia"]


def test_perfil_le_email_do_endereco_profissional():
    perfil = parse_perfil(raiz())

    assert perfil.email == "maria@pessoal.com"


def test_perfil_sem_dados_gerais_e_erro_de_comando():
    sem_dados = ET.fromstring('<CURRICULO-VITAE NUMERO-IDENTIFICADOR="1"/>')

    with pytest.raises(CommandError):
        parse_perfil(sem_dados)


# ---------------------------------------------------------------------------
# Parser: projetos
# ---------------------------------------------------------------------------

def test_projeto_traduz_natureza_e_situacao_para_as_choices():
    projeto = parse_projetos(raiz())[0]

    assert projeto.tipo == "pesquisa"
    assert projeto.status == "em_andamento"


def test_projeto_extensao_concluido():
    xml = PROJETO_PADRAO.replace('NATUREZA="PESQUISA"', 'NATUREZA="EXTENSAO"').replace(
        'SITUACAO="EM_ANDAMENTO"', 'SITUACAO="CONCLUIDO"'
    )
    projeto = parse_projetos(raiz(projetos=xml))[0]

    assert projeto.tipo == "extensao"
    assert projeto.status == "concluido"


def test_projeto_desativado_vira_suspenso():
    xml = PROJETO_PADRAO.replace('SITUACAO="EM_ANDAMENTO"', 'SITUACAO="DESATIVADO"')
    projeto = parse_projetos(raiz(projetos=xml))[0]

    assert projeto.status == "suspenso"


def test_projeto_de_natureza_desconhecida_cai_em_pesquisa():
    xml = PROJETO_PADRAO.replace('NATUREZA="PESQUISA"', 'NATUREZA="DESENVOLVIMENTO"')
    projeto = parse_projetos(raiz(projetos=xml))[0]

    assert projeto.tipo == "pesquisa"
    assert projeto.natureza_original == "DESENVOLVIMENTO"


def test_projeto_converte_ano_em_primeiro_de_janeiro():
    projeto = parse_projetos(raiz())[0]

    assert projeto.data_inicio == datetime.date(2023, 1, 1)
    assert projeto.data_fim is None


def test_projeto_com_ano_fim_termina_em_31_de_dezembro():
    xml = PROJETO_PADRAO.replace('ANO-FIM=""', 'ANO-FIM="2025"')
    projeto = parse_projetos(raiz(projetos=xml))[0]

    assert projeto.data_fim == datetime.date(2025, 12, 31)


def test_projeto_sem_ano_de_inicio_e_descartado():
    xml = PROJETO_PADRAO.replace('ANO-INICIO="2023"', 'ANO-INICIO=""')

    assert parse_projetos(raiz(projetos=xml)) == []


def test_projeto_identifica_o_responsavel_pela_flag():
    projeto = parse_projetos(raiz())[0]

    assert projeto.responsavel.nome == "Maria Silva Andrade"
    assert len(projeto.integrantes) == 2


# ---------------------------------------------------------------------------
# Comando: docente
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_importa_docente_como_rascunho(docentes_index, projetos_index, arquivo_xml):
    rodar(arquivo_xml(), email="maria@ifsertao-pe.edu.br")

    docente = DocentePage.objects.get(nome_completo="Maria Silva Andrade")
    assert docente.live is False
    assert docente.titulacao == "doutorado"
    assert docente.email == "maria@ifsertao-pe.edu.br"
    assert docente.lattes_url == "http://lattes.cnpq.br/1234567890123456"


@pytest.mark.django_db
def test_email_do_xml_e_usado_quando_nao_ha_opcao(docentes_index, projetos_index, arquivo_xml):
    rodar(arquivo_xml())

    docente = DocentePage.objects.get(nome_completo="Maria Silva Andrade")
    assert docente.email == "maria@pessoal.com"


@pytest.mark.django_db
def test_sem_email_no_xml_e_sem_opcao_o_comando_falha(docentes_index, arquivo_xml, tmp_path):
    caminho = tmp_path / "sem-email.xml"
    caminho.write_text(montar_xml().replace('E-MAIL="maria@pessoal.com"', ''), encoding="utf-8")

    with pytest.raises(CommandError, match="--email"):
        rodar(str(caminho))


@pytest.mark.django_db
def test_areas_do_lattes_viram_snippets(docentes_index, projetos_index, arquivo_xml):
    rodar(arquivo_xml())

    area = AreaConhecimento.objects.get(slug="agronomia")
    docente = DocentePage.objects.get(nome_completo="Maria Silva Andrade")
    assert area in docente.areas_conhecimento.all()


@pytest.mark.django_db
def test_rodar_duas_vezes_nao_duplica_o_docente(docentes_index, projetos_index, arquivo_xml):
    caminho = arquivo_xml()
    rodar(caminho)
    rodar(caminho)

    assert DocentePage.objects.filter(nome_completo="Maria Silva Andrade").count() == 1


@pytest.mark.django_db
def test_reimportacao_nao_despublica_perfil_ja_no_ar(
    docentes_index, projetos_index, arquivo_xml
):
    """A atualização vira revisão de rascunho — a versão pública fica intacta."""
    caminho = arquivo_xml()
    rodar(caminho)

    docente = DocentePage.objects.get(nome_completo="Maria Silva Andrade")
    docente.live = True
    docente.save()

    rodar(caminho, email="maria@ifsertao-pe.edu.br")

    docente.refresh_from_db()
    assert docente.live is True
    # --email só entra na revisão; a página publicada segue com o e-mail antigo
    assert docente.email == "maria@pessoal.com"


@pytest.mark.django_db
def test_dry_run_nao_grava_nada(docentes_index, projetos_index, arquivo_xml):
    saida = rodar(arquivo_xml(), dry_run=True)

    assert "dry-run" in saida
    assert not DocentePage.objects.filter(nome_completo="Maria Silva Andrade").exists()
    assert not ProjetoPage.objects.exists()


@pytest.mark.django_db
def test_arquivo_inexistente_e_erro_de_comando(docentes_index):
    with pytest.raises(CommandError, match="não encontrado"):
        rodar("/caminho/que/nao/existe.xml")


@pytest.mark.django_db
def test_xml_de_outra_natureza_e_recusado(docentes_index, tmp_path):
    caminho = tmp_path / "outro.xml"
    caminho.write_text("<QUALQUER-COISA/>", encoding="utf-8")

    with pytest.raises(CommandError, match="CURRICULO-VITAE"):
        rodar(str(caminho))


@pytest.mark.django_db
def test_sem_arvore_de_paginas_o_comando_orienta(db, arquivo_xml):
    with pytest.raises(CommandError, match="bootstrap_site"):
        rodar(arquivo_xml())


# ---------------------------------------------------------------------------
# Comando: projetos
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_importa_projeto_do_docente_como_rascunho(
    docentes_index, projetos_index, arquivo_xml
):
    rodar(arquivo_xml())

    projeto = ProjetoPage.objects.get(title="Manejo de Sorgo no Semiárido")
    docente = DocentePage.objects.get(nome_completo="Maria Silva Andrade")
    assert projeto.live is False
    assert projeto.coordenador_id == docente.pk
    assert projeto.tipo == "pesquisa"
    assert projeto.data_inicio == datetime.date(2023, 1, 1)


@pytest.mark.django_db
def test_resumo_sai_da_descricao_e_respeita_o_limite(
    docentes_index, projetos_index, arquivo_xml, tmp_path
):
    longa = "palavra " * 100
    caminho = tmp_path / "longo.xml"
    caminho.write_text(
        montar_xml().replace("Avalia cultivares de sorgo.", longa.strip()),
        encoding="utf-8",
    )
    rodar(str(caminho))

    projeto = ProjetoPage.objects.get(title="Manejo de Sorgo no Semiárido")
    assert len(projeto.resumo) <= 250
    assert projeto.resumo == projeto.resumo.strip()
    assert len(projeto.descricao) == 1


@pytest.mark.django_db
def test_resumir_nao_deixa_espaco_na_frente(db):
    """O Truncator do Django 5.1 devolve o texto com um espaço à esquerda."""
    longo = "palavra " * 100

    assert not resumir(longo).startswith(" ")
    assert len(resumir(longo)) <= 250
    assert resumir("curto") == "curto"


@pytest.mark.django_db
def test_projeto_de_coordenador_sem_perfil_e_pulado(
    docentes_index, projetos_index, arquivo_xml, tmp_path
):
    """Coordenador externo não vira dado errado: o projeto fica de fora e é relatado."""
    xml = montar_xml().replace('NRO-ID-CNPQ="1234567890123456"\n', 'NRO-ID-CNPQ="999"\n')
    xml = xml.replace(
        '<INTEGRANTES-DO-PROJETO NOME-COMPLETO="Maria Silva Andrade"',
        '<INTEGRANTES-DO-PROJETO NOME-COMPLETO="Carlos Externo"',
    )
    caminho = tmp_path / "externo.xml"
    caminho.write_text(xml, encoding="utf-8")

    saida = rodar(str(caminho))

    assert not ProjetoPage.objects.exists()
    assert "Carlos Externo" in saida


@pytest.mark.django_db
def test_integrante_sem_perfil_e_relatado(docentes_index, projetos_index, arquivo_xml):
    saida = rodar(arquivo_xml())

    projeto = ProjetoPage.objects.get(title="Manejo de Sorgo no Semiárido")
    assert projeto.participantes_docentes.count() == 0
    assert "Ana Beatriz Souza" in saida


@pytest.mark.django_db
def test_rodar_duas_vezes_nao_duplica_o_projeto(docentes_index, projetos_index, arquivo_xml):
    caminho = arquivo_xml()
    rodar(caminho)
    rodar(caminho)

    assert ProjetoPage.objects.filter(title="Manejo de Sorgo no Semiárido").count() == 1


@pytest.mark.django_db
def test_xml_sem_projetos_importa_so_o_perfil(docentes_index, projetos_index, arquivo_xml):
    saida = rodar(arquivo_xml(projetos=""))

    assert DocentePage.objects.filter(nome_completo="Maria Silva Andrade").exists()
    assert not ProjetoPage.objects.exists()
    assert "nenhum projeto" in saida
