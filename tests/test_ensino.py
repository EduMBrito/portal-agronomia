# ---------------------------------------------------------------------------
# Page: DisciplinasIndexPage.get_context
# ---------------------------------------------------------------------------

def test_disciplinas_index_sem_filtro_agrupa_todos_periodos(
    rf, disciplinas_index, disciplina_p1, disciplina_p3
):
    request = rf.get("/disciplinas/")
    context = disciplinas_index.get_context(request)
    agrupadas = context["disciplinas_por_periodo"]

    assert 1 in agrupadas
    assert 3 in agrupadas
    assert disciplina_p1 in agrupadas[1]
    assert disciplina_p3 in agrupadas[3]


def test_disciplinas_index_filtro_periodo_exclui_outros_periodos(
    rf, disciplinas_index, disciplina_p1, disciplina_p3
):
    request = rf.get("/disciplinas/?periodo=1")
    context = disciplinas_index.get_context(request)
    agrupadas = context["disciplinas_por_periodo"]

    assert 1 in agrupadas
    assert 3 not in agrupadas


def test_disciplinas_index_periodos_disponiveis_no_context(
    rf, disciplinas_index, disciplina_p1, disciplina_p3
):
    request = rf.get("/disciplinas/")
    context = disciplinas_index.get_context(request)

    assert 1 in context["periodos"]
    assert 3 in context["periodos"]


def test_disciplinas_index_periodo_selecionado_no_context(rf, disciplinas_index):
    request = rf.get("/disciplinas/?periodo=5")
    context = disciplinas_index.get_context(request)
    assert context["periodo_selecionado"] == "5"


def test_disciplinas_index_sem_disciplinas_retorna_agrupamento_vazio(rf, disciplinas_index):
    request = rf.get("/disciplinas/")
    context = disciplinas_index.get_context(request)
    assert context["disciplinas_por_periodo"] == {}


def test_disciplinas_index_agrupamento_ordenado_por_periodo(
    rf, disciplinas_index, disciplina_p3, disciplina_p1
):
    request = rf.get("/disciplinas/")
    context = disciplinas_index.get_context(request)
    periodos = list(context["disciplinas_por_periodo"].keys())
    assert periodos == sorted(periodos)
