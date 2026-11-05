import base64
import datetime as dt
import logging

import pytest
import xmltodict
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.x509.oid import NameOID

from afip_services.models.ticket import TicketAutorizacion
from afip_services.services.wsaa_client import WSAAClient
from afip_services.utils.signing import sign_tra
from afip_services.utils.tra_utils import create_tra_xml

FAKE_TOKEN = "fake-token-value"
FAKE_SIGN = "fake-sign-value"


def _ticket_response(expiration: dt.datetime) -> dict:
    return {
        "loginTicketResponse": {
            "header": {
                "expirationTime": expiration.isoformat(),
                "destination": "SERIALNUMBER=CUIT 20111111112, CN=example",
            },
            "credentials": {"token": FAKE_TOKEN, "sign": FAKE_SIGN},
        }
    }


@pytest.fixture(scope="module")
def cert_and_key(tmp_path_factory):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "afip-services-test")])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(days=1))
        .not_valid_after(now + dt.timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    folder = tmp_path_factory.mktemp("certs")
    cert_path = folder / "cert.crt"
    key_path = folder / "key.key"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(b"secret"),
        )
    )
    return cert_path, key_path


def test_tra_xml_has_service_and_ten_minute_window():
    tra = xmltodict.parse(create_tra_xml("ws_sr_padron_a13"))["loginTicketRequest"]
    assert tra["@version"] == "1.0"
    assert tra["service"] == "ws_sr_padron_a13"
    start = dt.datetime.fromisoformat(tra["header"]["generationTime"])
    end = dt.datetime.fromisoformat(tra["header"]["expirationTime"])
    assert end - start == dt.timedelta(minutes=20)


def test_ticket_parsing_and_validity():
    future = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
    ticket = TicketAutorizacion(_ticket_response(future))
    assert ticket.token == FAKE_TOKEN
    assert ticket.sign == FAKE_SIGN
    assert ticket.number_cuit == "20111111112"
    assert ticket.is_valid()

    past = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)
    assert not TicketAutorizacion(_ticket_response(past)).is_valid()


def test_ticket_never_exposes_credentials(caplog):
    future = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
    with caplog.at_level(logging.DEBUG):
        ticket = TicketAutorizacion(_ticket_response(future))
        ticket.is_valid()
    text = caplog.text + str(ticket)
    assert FAKE_TOKEN not in text
    assert FAKE_SIGN not in text


def test_sign_tra_produces_verifiable_cms(cert_and_key):
    cert_path, key_path = cert_and_key
    client = WSAAClient("ws_sr_padron_a13", str(cert_path), str(key_path), False, "secret")
    tra = create_tra_xml("ws_sr_padron_a13")
    cms_b64 = sign_tra(tra, client.certificate, client.private_key)

    der = base64.b64decode(cms_b64)
    certs = pkcs7.load_der_pkcs7_certificates(der)
    assert certs[0].subject == client.certificate.subject
    assert tra.encode("utf-8") in der


def test_wsaa_client_authenticates_with_fake_service(cert_and_key, monkeypatch):
    cert_path, key_path = cert_and_key
    client = WSAAClient("ws_sr_padron_a13", str(cert_path), str(key_path), False, "secret")
    assert "wsaahomo" in client.get_wsdl_url()

    sent = {}
    future = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)

    def fake_request(cms):
        sent["cms"] = cms
        return _ticket_response(future)

    monkeypatch.setattr(client, "request_afip_authorization", fake_request)
    client.authenticate()
    assert base64.b64decode(sent["cms"])
    assert client.get_authorization_ticket().token == FAKE_TOKEN


def test_wsaa_client_without_authentication_fails(cert_and_key):
    cert_path, key_path = cert_and_key
    client = WSAAClient("ws_sr_padron_a13", str(cert_path), str(key_path), False, "secret")
    with pytest.raises(ValueError):
        client.get_authorization_ticket()


def test_missing_certificate_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        WSAAClient("ws_sr_padron_a13", str(tmp_path / "nope.crt"), str(tmp_path / "nope.key"))
