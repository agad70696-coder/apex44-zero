import time
from src.apex import ApexShieldZero
start = time.time()
# اختبار أداء 10k حرف
print(f"Benchmark: {time.time()-start:.2f}s - لازم < 2s")
