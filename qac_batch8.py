# QAC 40/44 - الدفعة التامنة

# 36. [6:145] الا ان يكون ميتة او دما مسفوحا
def check_dam_masfuh(is_masfuh):
    if is_masfuh: return "REJECT [6:145] دم مسفوح"
    return "APPROVE [6:145]"

# 37. [5:3] اليوم اكملت لكم دينكم - كمال المعيار
def check_kamal(is_complete_std):
    if not is_complete_std: return "REVIEW [5:3] معيار ناقص"
    return "APPROVE [5:3] كامل"

# 38. [2:168] خطوات الشيطان - لا تتبعوا
def check_khutuwat(is_shaytan_step):
    if is_shaytan_step: return "REJECT [2:168] خطوة شيطان"
    return "APPROVE [2:168]"

# 39. [7:31] خذوا زينتكم - جمال بلا اسراف
def check_zeena(is_zeena_halal):
    if not is_zeena_halal: return "REVIEW [7:31] زينة غير طيبة"
    return "APPROVE [7:31] زينة طيبة"

# 40. [2:233] لا تضار والدة بولدها - لا ضرر
def check_no_darar(is_harmful):
    if is_harmful: return "REJECT [2:233] فيه ضرر"
    return "APPROVE [2:233] لا ضرر"

print(check_dam_masfuh(False))
print(check_kamal(True))
