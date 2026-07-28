import shutil
from pathlib import Path

# انسخ الكود القديم لجوه src
Path("src/apex/qac").mkdir(parents=True, exist_ok=True)
Path("src/apex/utils").mkdir(parents=True, exist_ok=True)
Path("src/shield").mkdir(parents=True, exist_ok=True)

try:
    shutil.copy("apex/qac/checks_44.py", "src/apex/qac/checks_44.py")
    shutil.copy("apex/utils/logger.py", "src/apex/utils/logger.py")
    shutil.copy("shield/core.py", "src/shield/core.py")
    shutil.copy("shield/self_defense.py", "src/shield/self_defense.py")
    print("✅ تم النقل لـ src/ بنجاح")
except Exception as e:
    print(f"الملفات الأصلية لسه في مكانها وده عادي - {e}")
