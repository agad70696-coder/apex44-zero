import datetime
import json
import pathlib
import socket
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))


class OpportunityScanner:
    def scan_rpc(self):
        try:
            socket.gethostbyname("polygon-amoy.drpc.org")
            return {"status": "PASS", "opportunity": "RPC healthy"}
        except OSError:
            return {"status": "FAIL", "opportunity": "RPC DOWN"}

    def scan_jcs(self):
        try:
            import IRRE.ledger.jcs_canonical as jcs

            return {
                "status": "PASS" if jcs.is_jcs() else "FAIL",
                "opportunity": "JCS check",
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "opportunity": str(e),
            }

    def scan_tla(self):
        p = pathlib.Path("specs/evidence_chain.tla")

        if not p.exists():
            return {
                "status": "FAIL",
                "opportunity": "TLA missing",
            }

        txt = p.read_text(encoding="utf-8")

        ok = (
            "Inv_Crypto" in txt
            and "Inv_Linkage" in txt
        )

        return {
            "status": "PASS" if ok else "FAIL",
            "opportunity": "TLA invariants",
        }

    def scan_nist(self):
        d = (
            datetime.date(2030, 12, 31)
            - datetime.date.today()
        ).days

        return {
            "status": "OPPORTUNITY",
            "opportunity": f"{d} days before 2030 deprecation",
        }

    def run(self):
        result = {
            "rpc": self.scan_rpc(),
            "jcs": self.scan_jcs(),
            "tla": self.scan_tla(),
            "nist": self.scan_nist(),
        }

        ledger_path = pathlib.Path(
            "data/opportunity_ledger.jsonl"
        )

        ledger_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        lines = []

        for component, record in result.items():
            lines.append(
                json.dumps(
                    {
                        "component": component,
                        **record,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )

        ledger_path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                sort_keys=True,
            )
        )

        return result


if __name__ == "__main__":
    OpportunityScanner().run()
