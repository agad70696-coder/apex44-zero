# QAC 20/44 - الدفعة الرابعة - نواة APEX-SHIELD نفسه!

# 16. [49:6] فتبينوا - التحقق قبل النشر - اهم قانون في مشروعك
def check_tabayyun(verified):
    if not verified: return "REJECT [49:6] خبر غير متبين"
    return "APPROVE [49:6] تم التبين"

# 17. [2:222] يحب المتطهرين - طهارة الدليل
def check_tahara(is_pure):
    if not is_pure: return "REJECT [2:222] دليل ملوث"
    return "APPROVE [2:222] طاهر"

# 18. [24:35] نور على نور - شفافية
def check_noor(is_transparent):
    if not is_transparent: return "REVIEW [24:35] دليل غير منير"
    return "APPROVE [24:35] نور"

# 19. [96:1] اقرأ باسم ربك - علم
def check_ilm(has_source):
    if not has_source: return "REVIEW [96:1] بلا مصدر علمي"
    return "APPROVE [96:1]"

# 20. [17:36] ولا تقف ما ليس لك به علم - لا افتراء
def check_no_assumption(is_assumption):
    if is_assumption: return "REJECT [17:36] تقول بلا علم"
    return "APPROVE [17:36]"

print(check_tabayyun(True))
print(check_noor(True))
