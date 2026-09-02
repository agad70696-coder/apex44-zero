from src.apex import ApexShieldZero

shield = ApexShieldZero(owner_id="amr")
result = shield.protect_text("كتابي السري", buyer_id="buyer_1")
print(result["protected_text"])
