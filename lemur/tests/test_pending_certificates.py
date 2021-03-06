import json

import pytest

from .vectors import CSR_STR, INTERNAL_VALID_LONG_STR, VALID_ADMIN_API_TOKEN, VALID_ADMIN_HEADER_TOKEN, VALID_USER_HEADER_TOKEN

from lemur.pending_certificates.views import *  # noqa


def test_increment_attempt(pending_certificate):
    from lemur.pending_certificates.service import increment_attempt
    initial_attempt = pending_certificate.number_attempts
    attempts = increment_attempt(pending_certificate)
    assert attempts == initial_attempt + 1


def test_create_pending_certificate(async_issuer_plugin, async_authority, user):
    from lemur.certificates.service import create
    pending_cert = create(authority=async_authority, csr=CSR_STR, owner='joe@example.com', creator=user['user'], common_name='ACommonName')
    assert pending_cert.external_id == '12345'


def test_create_pending(pending_certificate, user, session):
    import copy
    from lemur.pending_certificates.service import create_certificate, get
    cert = {'body': INTERNAL_VALID_LONG_STR,
            'chain': None,
            'external_id': 54321}

    # Weird copy because the session behavior.  pending_certificate is a valid object but the
    # return of vars(pending_certificate) is a sessionobject, and so nothing from the pending_cert
    # is used to create the certificate.  Maybe a bug due to using vars(), and should copy every
    # field explicitly.
    pending_certificate = copy.copy(get(pending_certificate.id))
    real_cert = create_certificate(pending_certificate, cert, user['user'])
    assert real_cert.owner == pending_certificate.owner
    assert real_cert.notify == pending_certificate.notify
    assert real_cert.private_key == pending_certificate.private_key
    assert real_cert.external_id == '54321'


@pytest.mark.parametrize("token,status", [
    (VALID_USER_HEADER_TOKEN, 403),
    (VALID_ADMIN_HEADER_TOKEN, 204),
    (VALID_ADMIN_API_TOKEN, 204),
    ('', 401)
])
def test_pending_cancel(client, pending_certificate, token, status):
    assert client.delete(api.url_for(PendingCertificates, pending_certificate_id=pending_certificate.id),
                         data=json.dumps({'note': "unit test", 'send_email': False}),
                         headers=token).status_code == status
