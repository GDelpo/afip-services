from types import SimpleNamespace

import pytest

from afip_services import WSN, WSNService
from afip_services.afip_gateway import _padron_list_handler, _padron_single_handler
from afip_services.registry import HandlerNotRegisteredError, register_handler
from afip_services.utils.exceptions import AFIPRequestError

TICKET = SimpleNamespace(token="t", sign="s", number_cuit="20111111112", is_valid=lambda: True)


def _persona(cuit: int, name: str) -> dict:
    return {"datosGenerales": {"idPersona": cuit, "razonSocial": name}}


def _rejected(cuit: int) -> dict:
    return {"errorConstancia": {"idPersona": cuit, "error": ["No existe persona con ese Id"]}}


def _wsn() -> WSN:
    wsn = WSN.__new__(WSN)
    wsn.authorization_ticket = TICKET
    return wsn


class FakeClient:
    def __init__(self, list_answer=None, single_answers=None):
        self.calls = []
        list_answer = list_answer or []
        single_answers = single_answers or {}

        def get_persona_list(**kwargs):
            self.calls.append(kwargs)
            return {"persona": list_answer}

        def get_persona(**kwargs):
            self.calls.append(kwargs)
            answer = single_answers[kwargs["idPersona"]]
            if isinstance(answer, Exception):
                raise answer
            return {"persona": answer}

        self.service = SimpleNamespace(getPersonaList_v2=get_persona_list, getPersona=get_persona)


def test_padron_list_matches_answers_by_id_not_position():
    client = FakeClient(list_answer=[_persona(20222222223, "B"), _persona(20111111112, "A")])
    result = _padron_list_handler(_wsn(), client, persona_ids=["20111111112", "20222222223"])

    assert result == [
        {"20111111112": _persona(20111111112, "A")},
        {"20222222223": _persona(20222222223, "B")},
    ]
    assert client.calls[0]["idPersona"] == [20111111112, 20222222223]
    assert client.calls[0]["cuitRepresentada"] == 20111111112


def test_padron_list_keeps_afip_rejections_and_marks_missing_ids():
    client = FakeClient(list_answer=[_rejected(20111111112)])
    result = _padron_list_handler(_wsn(), client, persona_ids=[20111111112, 20333333334])

    assert result[0] == {20111111112: _rejected(20111111112)}
    assert result[1] == {20333333334: {"error": "not returned by AFIP"}}


def test_padron_list_fails_on_answer_without_id():
    client = FakeClient(list_answer=[{"datosGenerales": {"razonSocial": "?"}}])
    with pytest.raises(AFIPRequestError):
        _padron_list_handler(_wsn(), client, persona_ids=[20111111112])


def test_padron_single_returns_serializable_errors():
    client = FakeClient(
        single_answers={
            20111111112: {"idPersona": 20111111112},
            20222222223: RuntimeError("boom"),
        }
    )
    result = _padron_single_handler(_wsn(), client, persona_ids=[20111111112, 20222222223])

    assert result == [
        {20111111112: {"idPersona": 20111111112}},
        {20222222223: {"error": "boom"}},
    ]


def test_request_persona_list_dispatches_by_kind(monkeypatch):
    wsn = _wsn()
    wsn.service = WSNService.WS_SR_PADRON_A13
    client = FakeClient(single_answers={20111111112: {"idPersona": 20111111112}})
    monkeypatch.setattr(wsn, "_new_client", lambda: client)

    assert wsn.request_persona_list([20111111112]) == [{20111111112: {"idPersona": 20111111112}}]


def test_unregistered_kind_raises(monkeypatch):
    wsn = _wsn()
    wsn.service = SimpleNamespace(name="CUSTOM", value=SimpleNamespace(kind="nobody_handles_this"))
    monkeypatch.setattr(wsn, "_new_client", lambda: None)

    with pytest.raises(HandlerNotRegisteredError):
        wsn.request_persona_list([1])
    with pytest.raises(HandlerNotRegisteredError):
        wsn.request(foo=1)


def test_generic_request_passes_kwargs_to_custom_handler(monkeypatch):
    @register_handler("echo_kind")
    def echo(wsn, client, **kwargs):
        return {"client": client, **kwargs}

    wsn = _wsn()
    wsn.service = SimpleNamespace(name="ECHO", value=SimpleNamespace(kind="echo_kind"))
    monkeypatch.setattr(wsn, "_new_client", lambda: "zeep-client")

    assert wsn.request(invoice=7) == {"client": "zeep-client", "invoice": 7}
