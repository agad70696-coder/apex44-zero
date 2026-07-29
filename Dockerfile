FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir pytest

RUN pytest tests/test_evidence_claim.py -v

CMD ["pytest", "tests/test_evidence_claim.py", "-v"]
