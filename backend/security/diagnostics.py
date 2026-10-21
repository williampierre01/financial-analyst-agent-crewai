"""Allowlisted diagnostics: never log exception text, credentials or identities."""
from contextlib import contextmanager

from fastapi import HTTPException


def failure_kind(error):
    kinds = {
        "DefaultCredentialsError": "credentials_unavailable",
        "RefreshError": "credentials_refresh_failed",
        "PermissionDeniedError": "provider_permission_denied",
        "Forbidden": "provider_permission_denied",
        "CertificateFetchError": "provider_certificates_unavailable",
        "TransportError": "provider_transport_failed",
        "SSLError": "tls_failed",
        "InsufficientPrivilege": "database_permission_denied",
        "UndefinedTable": "database_schema_missing",
        "OperationalError": "database_connection_failed",
        "TimeoutError": "timeout",
    }
    return kinds.get(type(error).__name__, "unexpected_failure")


class AuthDependencyFailure(Exception):
    def __init__(self, stage, kind):
        super().__init__("Authentication dependency unavailable")
        self.stage, self.kind = stage, kind


@contextmanager
def auth_stage(stage):
    try:
        yield
    except (HTTPException, AuthDependencyFailure):
        raise
    except Exception as error:
        raise AuthDependencyFailure(stage, failure_kind(error)) from None
