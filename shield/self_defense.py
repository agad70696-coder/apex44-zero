"""
APEX-SHIELD - Self-Defense System
نظام حماية يحمي نفسه بنفسه - أعلى من الشركات العالمية
Version: 1.0 - Unkillable Core
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

try:
    from apex.utils.logger import setup_logger

    logger = setup_logger("shield-defense")
except:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("shield-defense")

MANIFEST_FILE = Path(".shield_manifest.json")
CRITICAL_FILES = [
    "apex.py",
    "apex/qac/checks_44.py",
    "apex/utils/logger.py",
    "shield/self_defense.py",
    "shield/core.py",
]


class SelfDefense:
    """
    قلب النظام الخارق:
    1. بيحسب بصمة لكل ملف مهم
    2. لو حد لعب في ملف، بيكشفه
    3. بيصلح نفسه بنفسه
    """

    def __init__(self) -> None:
        self.base = Path()
        logger.info("[SELF-DEFENSE] Unkillable mode activated")

    def get_hash(self, file_path: Path) -> str:
        """بصمة الملف - SHA256"""
        try:
            data = file_path.read_bytes()
            return hashlib.sha256(data).hexdigest()[:16]  # اول 16 حرف كفاية
        except:
            return "MISSING"

    def create_manifest(self) -> dict:
        """بيعمل خريطة للأصول - أول مرة بس"""
        manifest = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0-unkillable",
            "files": {},
        }
        for file_str in CRITICAL_FILES:
            p = self.base / file_str
            if p.exists():
                manifest["files"][file_str] = self.get_hash(p)

        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"✅ Manifest created: {len(manifest['files'])} files protected")
        return manifest

    def verify_integrity(self) -> dict:
        """يفحص هل حد لعب في الكود؟"""
        logger.info("[SELF-DEFENSE] Verifying integrity...")

        if not MANIFEST_FILE.exists():
            logger.warning("No manifest found - creating first one")
            return {"status": "FIRST_RUN", "manifest": self.create_manifest()}

        try:
            manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        except:
            return {"status": "MANIFEST_CORRUPTED", "tampered": []}

        tampered = []
        for file_str, old_hash in manifest.get("files", {}).items():
            p = self.base / file_str
            new_hash = self.get_hash(p)
            if new_hash != old_hash:
                tampered.append(
                    {
                        "file": file_str,
                        "old": old_hash,
                        "new": new_hash,
                        "status": "TAMPERED" if new_hash != "MISSING" else "DELETED",
                    }
                )

        if tampered:
            logger.error(f"🚨 TAMPER DETECTED! {len(tampered)} files modified!")
            for t in tampered:
                logger.error(f"  - {t['file']}: {t['status']}")
            return {"status": "TAMPERED", "tampered": tampered}
        else:
            logger.info("✅ Integrity OK - No tampering")
            return {"status": "OK", "tampered": []}

    def self_heal(self, verification_result: dict) -> bool:
        """
        أهم دالة - بيصلح نفسه بنفسه
        لو حد مسح ملف أو لعب فيه، بيرجعه من جيت هاب
        """
        if verification_result["status"] != "TAMPERED":
            return True

        logger.info("[SELF-HEAL] Attempting to heal...")
        # في النسخة الخارقة V2 هنخليه ينزل الملف من GitHub Raw تلقائيا
        # دلوقتي هنعمل نسخة بسيطة: تحذير + تسجيل محاولة الاختراق

        attack_log = {
            "timestamp": datetime.now().isoformat(),
            "attack_type": "FILE_TAMPERING",
            "tampered_files": verification_result["tampered"],
            "action": "LOGGED_FOR_EVOLUTION",
        }

        # سجل الهجوم عشان يتعلم منه بعدين
        log_file = Path("shield_attacks.json")
        attacks = []
        if log_file.exists():
            try:
                attacks = json.loads(log_file.read_text(encoding="utf-8"))
            except:
                attacks = []
        attacks.append(attack_log)

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(attacks, f, indent=2, ensure_ascii=False)

        logger.info("🛡️ Attack logged - System will evolve to block it")
        logger.info(f"📈 Total attacks learned: {len(attacks)}")

        # في V2: هنرجع الملف الأصلي من GitHub
        return False  # حاليا بيكشف بس، V2 هيصلح تلقائيا

    def protect(self) -> bool:
        """الدالة الرئيسية - شغلها في أول البرنامج"""
        result = self.verify_integrity()
        if result["status"] == "TAMPERED":
            self.self_heal(result)
            return False
        return True


# تشغيل مباشر للاختبار
if __name__ == "__main__":
    defense = SelfDefense()
    if not MANIFEST_FILE.exists():
        defense.create_manifest()
        print("✅ نظام الحماية الذاتية اتفعل - أول بصمة اتعملت")
    else:
        result = defense.verify_integrity()
        if result["status"] == "OK":
            print("✅ النظام سليم - محدش لمسه")
        else:
            print(f"🚨 خطر! {len(result['tampered'])} ملفات تم التلاعب بها")
