# QAC 35/44 - الدفعة السابعة - نور وعلم

# 31. [2:42] ولا تلبسوا الحق بالباطل
def check_no_mixing(hak_batil_mix):
    if hak_batil_mix: return "REJECT [2:42] خلط حق بباطل"
    return "APPROVE [2:42]"

# 32. [2:282] واشهدوا اذا تبايعتم - توثيق
def check_tawthiq(documented):
    if not documented: return "REVIEW [2:282] بلا توثيق"
    return "APPROVE [2:282] موثق"

# 33. [16:67] سكرا ورزقا حسنا - تمييز طيب
def check_sukr_rizq(is_sukr):
    if is_sukr: return "REJECT [16:67] سكرا ليس رزقا حسنا"
    return "APPROVE [16:67] رزق حسن"

# 34. [25:67] لم يسرفوا ولم يقتروا وكان بين ذلك قواما
def check_qawam(balance):
    if balance<0.3 or balance>0.7: return f"REVIEW [25:67] غير قوام {balance}"
    return "APPROVE [25:67] قوام"

# 35. [7:32] قل من حرم زينة الله - لا تحريم بلا دليل
def check_no_fake_haram(fake_haram):
    if fake_haram: return "REJECT [7:32] تحريم بلا دليل"
    return "APPROVE [7:32]"

print(check_no_mixing(False))
print(check_tawthiq(True))
