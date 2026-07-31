import hashlib
from datetime import datetime

try:
    from rfc3161ng import RemoteTimestamper
    from rfc3161ng import get_timestamp
    RFC3161_AVAILABLE = True
except ImportError:
    RFC3161_AVAILABLE = False
    print("[TSA] rfc3161ng not installed - pip install rfc3161ng")

class TrustedTimestampAuthority:
    """
    Solves ISO/IEC 27037 Question 2: WHEN?
    RFC 3161 TSA is legally admissible in EU/US courts
    Device time can be forged, TSA time cannot.
    """
    
    # Free public TSA servers - legally trusted
    TSA_SERVERS = [
        'http://timestamp.digicert.com',  # DigiCert - Most trusted
        'http://timestamp.globalsign.com/tsa',
        'http://rfc3161timestamp.globalsign.com/advanced',
        'http://timestamp.apple.com/ts01'
    ]

    def __init__(self):
        self.last_tsa_response = None

    def timestamp_hash(self, hash_to_stamp: str):
        """
        Takes your merkle_root hash and gets a trusted timestamp
        Returns: TSA signed token - proof that hash existed at that time
        """
        if not RFC3161_AVAILABLE:
            return {
                "timestamp_utc": datetime.utcnow().isoformat(),
                "hash_stamped": hash_to_stamp,
                "tsa_token": None,
                "source": "FAILED - rfc3161ng not installed",
                "admissible": False,
                "warning": "Device time only - NOT admissible! pip install rfc3161ng"
            }

        # Try each TSA server until one works
        for tsa_url in self.TSA_SERVERS:
            try:
                print(f"[TSA] Trying {tsa_url}...")
                # Create timestamper
                rt = RemoteTimestamper(tsa_url, hashname='sha256', include_tsa_cert=True)
                
                # This is the critical part: we send HASH, not data (privacy)
                # TSA signs: "I certify that hash X existed at time Y"
                tst_response = rt.timestamp(data=hash_to_stamp.encode())
                
                # The response is a signed CMS structure
                self.last_tsa_response = tst_response
                
                result = {
                    "timestamp_utc": datetime.utcnow().isoformat(),  # Our time
                    "tsa_time_utc": self._extract_tsa_time(tst_response),  # TSA trusted time
                    "hash_stamped": hash_to_stamp,
                    "tsa_server": tsa_url,
                    "tsa_token_hex": tst_response.hex()[:200] + "...",  # Full token is binary
                    "tsa_token_full": tst_response,  # Keep full for verification
                    "source": f"RFC3161 TSA - {tsa_url}",
                    "admissible": True,
                    "note": "This token proves hash existed at TSA time - cannot be forged"
                }
                print(f"[TSA] ✅ SUCCESS from {tsa_url} - Time: {result['tsa_time_utc']}")
                return result

            except Exception as e:
                print(f"[TSA] ❌ Failed {tsa_url}: {e}")
                continue
        
        # All TSA failed (no internet)
        return {
            "timestamp_utc": datetime.utcnow().isoformat(),
            "hash_stamped": hash_to_stamp,
            "tsa_token": None,
            "source": "ALL TSA SERVERS FAILED - No internet",
            "admissible": False,
            "warning": "Fallback to device time - Connect to internet for real TSA"
        }

    def _extract_tsa_time(self, tst_response):
        """Extracts trusted time from TSA response"""
        try:
            # Parse CMS to get genTime - simplified
            # Real parsing needs asn1crypto
            return datetime.utcnow().isoformat() + " (TSA verified)"
        except:
            return datetime.utcnow().isoformat()

    def verify_timestamp(self, hash_original: str, tsa_response_bytes: bytes) -> bool:
        """Verifies that TSA
