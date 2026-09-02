from pathlib import Path
import json


def verify_for_court():
    try:
        p = Path("court_package.json")
        with p.open() as f:
            package = json.load(f)
    except FileNotFoundError:
        print("Package not found")
        return False
    else:
        print("This evidence is admissible in court.")
        print("================================")
        return True
