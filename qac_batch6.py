# QAC 30/44 - الدفعة السادسة

# 26. [6:38] ما فرطنا في الكتاب من شيء - اكتمال
def check_completeness(missing):
    if missing: return f"REVIEW [6:38] ناقص {missing}"
    return "APPROVE [6:38] كامل"

# 27. [4:135] كونوا قوامين بالقسط شهداء لله
def check_qist(is_fair_witness):
    if not is_fair_witness: return "REJECT [4:135] شهادة غير قسط"
    return "APPROVE [4:135]"

# 28. [5:8] اعدلوا هو اقرب للتقوى
def check_adl_taqwa(is_adl):
    if not is_adl: return "REVIEW [5:8] ليس اقرب للتقوى"
    return "APPROVE [5:8]"

# 29. [49:13] ان اكرمكم عند الله اتقاكم - لا عنصرية
def check_no_racism(discrimination):
    if discrimination: return "REJECT [49:13] عنصرية"
    return "APPROVE [49:13]"

# 30. [2:256] لا اكراه في الدين - رضا
def check_consent(has_consent):
    if not has_consent: return "REJECT [2:256] بلا رضا"
    return "APPROVE [2:256] برضا"

print(check_completeness(False))
print(check_qist(True))
print(check_consent(True))
