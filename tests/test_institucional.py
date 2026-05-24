from django.utils import timezone


# ---------------------------------------------------------------------------
# Page: EventosIndexPage.get_context
# ---------------------------------------------------------------------------

def test_eventos_index_filtro_futuros_exclui_eventos_passados(
    rf, eventos_index, evento_futuro, evento_passado
):
    request = rf.get("/eventos/?futuros=1")
    context = eventos_index.get_context(request)
    ids = [e.pk for e in context["page_obj"].object_list]

    assert evento_futuro.pk in ids
    assert evento_passado.pk not in ids


def test_eventos_index_sem_filtro_futuros_retorna_todos(
    rf, eventos_index, evento_futuro, evento_passado
):
    request = rf.get("/eventos/")
    context = eventos_index.get_context(request)
    ids = [e.pk for e in context["page_obj"].object_list]

    assert evento_futuro.pk in ids
    assert evento_passado.pk in ids


def test_eventos_index_filtro_por_tipo_seminario(
    rf, eventos_index, evento_seminario, evento_workshop
):
    request = rf.get("/eventos/?tipo=seminario")
    context = eventos_index.get_context(request)
    ids = [e.pk for e in context["page_obj"].object_list]

    assert evento_seminario.pk in ids
    assert evento_workshop.pk not in ids


def test_eventos_index_filtro_por_tipo_workshop(
    rf, eventos_index, evento_seminario, evento_workshop
):
    request = rf.get("/eventos/?tipo=workshop")
    context = eventos_index.get_context(request)
    ids = [e.pk for e in context["page_obj"].object_list]

    assert evento_workshop.pk in ids
    assert evento_seminario.pk not in ids


def test_eventos_index_tipo_selecionado_no_context(rf, eventos_index, evento_seminario):
    request = rf.get("/eventos/?tipo=seminario")
    context = eventos_index.get_context(request)
    assert context["tipo_selecionado"] == "seminario"


def test_eventos_index_sem_filtro_tipo_selecionado_e_none(rf, eventos_index):
    request = rf.get("/eventos/")
    context = eventos_index.get_context(request)
    assert context["tipo_selecionado"] is None


def test_eventos_index_now_presente_no_context(rf, eventos_index):
    request = rf.get("/eventos/")
    context = eventos_index.get_context(request)
    assert "now" in context
    assert abs((context["now"] - timezone.now()).total_seconds()) < 5


def test_eventos_index_apenas_futuros_flag_no_context(rf, eventos_index):
    request = rf.get("/eventos/?futuros=1")
    context = eventos_index.get_context(request)
    assert context["apenas_futuros"] is True


def test_eventos_index_sem_flag_futuros_falso_no_context(rf, eventos_index):
    request = rf.get("/eventos/")
    context = eventos_index.get_context(request)
    assert context["apenas_futuros"] is False
