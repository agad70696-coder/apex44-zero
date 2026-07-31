# QAC 15/44 - الدفعة التالتة [6:118][6:121][21:30][2:275][4:29]

# 11. [6:118] فكلوا مما ذكر اسم الله عليه - تتبع
def check_dhikr(has_bismillah):
    if not has_bismillah: return "REVIEW [6:118] لا يوجد ذكر اسم الله"
    return "APPROVE [6:118]"

# 12. [6:121] ولا تأكلوا مما لم يذكر اسم الله
def check_no_dhikr(concealed):
    if concealed: return "REJECT [6:121] اخفاء مصدر"
    return "APPROVE [6:121]"

# 13. [21:30] وجعلنا من الماء كل شيء حي - طهارة الماء
def check_water(turbidity):
    if turbidity>5: return "REJECT [21:30] ماء غير طاهر"
    return "APPROVE [21:30] ماء طهور"

# 14. [2:275] وحرم الربا - لا ربا
def check_riba(interest):
    if interest>0: return f"REJECT [2:275] ربا {interest}%"
    return "APPROVE [2:275]"

# 15. [4:29] لا تأكلوا اموالكم بالباطل - لا غش
def check_batil
