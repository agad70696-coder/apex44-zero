from datetime import UTC, datetime

from cryptography import x509
from cryptography.hazmat.backends import default_backend

try:
    from rfc3161ng import RemoteTimestamper

    RFC3161_AVAILABLE = True
except ImportError:
    RFC3161_AVAILABLE = False


class TrustedTimestamp:
    def __init__(self) -> None:
        self.tsa_url = "https://timestamp.digicert.com"

    def get_timestamp(self, hash_to_stamp: str):
        if not RFC3161_AVAILABLE:
            return None
        rt = RemoteTimestamper(self.tsa_url)
        return rt.timestamp(data=hash_to_stamp.encode())

    def verify_tsa_chain(self, tst_response) -> dict:
        try:
            certs = tst_response.certificates
            if not certs:
                return {"valid": False, "reason": "No certificate"}
            tsa_cert = certs[0]
            cert = x509.load_der_x509_certificate(tsa_cert.dump(), default_backend())
            issuer = cert.issuer.rfc4514_string()
            if "DigiCert" not in issuer and "DigiCert" not in cert.subject.rfc4514_string():
                return {"valid": False, "reason": f"Untrusted: {issuer}"}
            now = datetime.now(UTC)
            if now < cert.not_valid_before_utc or now > cert.not_valid_after_utc:
                return {"valid": False, "reason": "Expired"}
            return {"valid": True, "issuer": issuer, "trusted_root": "DigiCert Verified"}
        except Exception as e:
            return {"valid": False, "reason": str(e)}
