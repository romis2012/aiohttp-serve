import ssl

import pytest
import trustme


@pytest.fixture
def ssl_ca() -> trustme.CA:
    return trustme.CA()


@pytest.fixture
def ssl_cert(ssl_ca: trustme.CA) -> trustme.LeafCert:
    return ssl_ca.issue_cert(
        "localhost",
        "127.0.0.1",
        "::1",
    )


@pytest.fixture
def ssl_certfile(ssl_cert: trustme.LeafCert):
    with ssl_cert.cert_chain_pems[0].tempfile() as cert_path:
        yield cert_path


@pytest.fixture
def ssl_keyfile(ssl_cert: trustme.LeafCert):
    with ssl_cert.private_key_pem.tempfile() as private_key_path:
        yield private_key_path


@pytest.fixture
def ssl_key_and_cert_chain(ssl_cert: trustme.LeafCert):
    with ssl_cert.private_key_and_cert_chain_pem.tempfile() as path:
        yield path


@pytest.fixture
def ssl_ca_cert(ssl_ca: trustme.CA):
    with ssl_ca.cert_pem.tempfile() as ca_cert_pem:
        yield ca_cert_pem


@pytest.fixture
def server_ssl_context(ssl_cert: trustme.LeafCert) -> ssl.SSLContext:
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
    ssl_cert.configure_cert(ssl_ctx)
    return ssl_ctx


@pytest.fixture
def client_ssl_context(ssl_ca: trustme.CA) -> ssl.SSLContext:
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    ssl_ctx.check_hostname = True
    ssl_ca.configure_trust(ssl_ctx)
    return ssl_ctx
