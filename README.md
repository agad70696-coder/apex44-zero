<p align="center">
  <img src="https://raw.githubusercontent.com/agad70696-coder/apex44-zero/main/apex-shield-logo.png" width="200" />
</p>

<h1 align="center">🛡️ APEX-SHIELD</h1>
<p align="center"><b>Irreducible Evidence System | Zero Trust Architecture</b></p>

<p align="center">
  <a href="https://github.com/agad70696-coder/apex44-zero/actions/workflows/quality-gate.yml">
    <img src="https://github.com/agad70696-coder/apex44-zero/actions/workflows/quality-gate.yml/badge.svg" alt="Quality Gate" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" />
  <img src="https://img.shields.io/badge/Docker-Ready-blue?logo=docker" />
  <img src="https://img.shields.io/badge/Tests-6%20Passed-green" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
  <img src="https://img.shields.io/github/stars/agad70696-coder/apex44-zero?style=social" />
</p>

## ✨ ايه ده؟
نظام حماية الأدلة الرقمية - بيضمن ان الدليل مستحيل يتزور أو يتمسح. مبني بـ Python و Zero-Trust.

> **العلم نور | Evidence is Truth**

## 🚀 التشغيل في ثانية

```bash
# بالـ Docker
docker build -t apex44-zero .
docker run apex44-zero
   ## 🤖 AI Verifier الجديد
   ```python
   from src.ai.verifier import AIVerifier
   verifier = AIVerifier()
   result = verifier.analyze_claim("العلم نور", "2026-07-29", "abc123")
   print(result['ai_verdict'])
# أو عادي
pip install pytest
pytest tests/test_evidence_claim.py -v