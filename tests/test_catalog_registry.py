import textwrap

import pytest

import afip_services
from afip_services import catalog
from afip_services.registry import get_handler, list_registered_kinds, register_handler


def test_default_catalog_ships_padron_services():
    services = catalog.get_catalog()
    assert services["WS_SR_CONSTANCIA_INSCRIPCION"].kind == "padron_list"
    assert services["WS_SR_PADRON_A13"].kind == "padron_single"
    assert services["WS_SR_PADRON_A13"].slug == "padron"


def test_environment_selection():
    cfg = catalog.get_catalog()["WS_SR_PADRON_A13"]
    assert "awshomo" in cfg.get_environment(False).wsdl_url
    assert "awshomo" not in cfg.get_environment(True).wsdl_url


def test_custom_catalog_builds_enum_and_derives_slug(tmp_path):
    custom = tmp_path / "services.yaml"
    custom.write_text(
        textwrap.dedent(
            """
            services:
              WS_SR_PADRON_A4:
                testing_service_url: https://test.example/a4
                testing_wsdl_url: https://test.example/a4?WSDL
                production_service_url: https://prod.example/a4
                production_wsdl_url: https://prod.example/a4?WSDL
                service_name: ws_sr_padron_a4
                method_name: getPersona
                kind: padron_single
            """
        ),
        encoding="utf-8",
    )
    try:
        catalog.reload_catalog(custom)
        member = catalog.WSNService.WS_SR_PADRON_A4
        assert member.get_service_name() == "ws_sr_padron_a4"
        assert member.value.slug == "padron-a4"
        assert list(catalog.get_catalog()) == ["WS_SR_PADRON_A4"]
    finally:
        catalog.reload_catalog()


def test_builtin_kinds_are_registered():
    assert {"padron_list", "padron_single"} <= set(list_registered_kinds())


def test_register_custom_handler():
    @register_handler("test_kind")
    def handler(wsn, client, **kwargs):
        return kwargs

    assert get_handler("test_kind") is handler
    assert get_handler("missing_kind") is None


def test_version_matches_package_metadata():
    assert afip_services.__version__ == "0.2.0"


@pytest.mark.parametrize("name", ["WS_SR_CONSTANCIA_INSCRIPCION", "WS_SR_PADRON_A13"])
def test_enum_members_exist(name):
    assert catalog.WSNService[name].value is catalog.get_catalog()[name]
