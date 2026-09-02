# QAC 44/44 - الخاتمة - العلم نور

# 41. [6:119] وقد فصل لكم ما حرم عليكم - تفصيل
def check_tafsil(is_mufassal) -> str:
    if not is_mufassal:
        return "REVIEW [6:119] حرام غير مفصل"
    return "APPROVE [6:119] مفصل"


# 42. [5:87] لا تحرموا طيبات ما احل الله
def check_no_tahrim_tayyib(is_forbidding_tayyib) -> str:
    if is_forbidding_tayyib:
        return "REJECT [5:87] تحريم طيب"
    return "APPROVE [5:87]"


# 43. [16:116] ولا تقولوا لما تصف السنتكم الكذب هذا حلال وهذا حرام
def check_no_kadhib_halal(is_lying_halal) -> str:
    if is_lying_halal:
        return "REJECT [16:116] كذب على الله"
    return "APPROVE [16:116] صدق"


# 44. [2:2] ذلك الكتاب لا ريب فيه هدى للمتقين - الختم
def check_no_rayb(has_doubt) -> str:
    if has_doubt:
        return "REVIEW [2:2] فيه ريب"
    return "APPROVE [2:2] لا ريب فيه | Evidence is Truth"


# الختم النهائي
print("APEX-SHIELD QAC 44/44 COMPLETE")
print(check_tafsil(True))
print(check_no_kadhib_halal(False))
print(check_no_rayb(False))
print("العلم نور | Evidence is Truth")
