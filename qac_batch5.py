# QAC 25/44 - الدفعة الخامسة - عدل الميزان

# 21. [7:85] ولا تبخسوا الناس اشياءهم
def check_bakhs(is_cheating) -> str:
    if is_cheating:
        return "REJECT [7:85] بخس حقوق"
    return "APPROVE [7:85]"


# 22. [83:1] ويل للمطففين - غش الميزان
def check_tatfif(weight_loss) -> str:
    if weight_loss > 0:
        return f"REJECT [83:1] تطفيف {weight_loss}g"
    return "APPROVE [83:1]"


# 23. [16:90] يأمر بالعدل والاحسان
def check_adl(is_just) -> str:
    if not is_just:
        return "REVIEW [16:90] ظلم"
    return "APPROVE [16:90] عدل"


# 24. [2:219] فيهما اثم كبير ومنافع - موازنة ضرر
def check_darar(benefit, harm) -> str:
    if harm > benefit:
        return f"REJECT [2:219] ضرره اكبر {harm}>{benefit}"
    return "APPROVE [2:219]"


# 25. [17:26] ولا تبذر تبذيرا
def check_tabdhir(waste_percent) -> str:
    if waste_percent > 20:
        return f"REVIEW [17:26] تبذير {waste_percent}%"
    return "APPROVE [17:26]"


print(check_bakhs(False))
print(check_tatfif(0))
print(check_darar(10, 2))
