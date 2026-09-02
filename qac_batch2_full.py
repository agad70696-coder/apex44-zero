# QAC 10/44 - الدفعة التانية كاملة


def check_israf(pack, total) -> str:
    if total == 0:
        return "REVIEW"
    if pack * 100 / total > 30:
        return "REVIEW [7:31] اسراف"
    return "APPROVE [7:31]"


def check_tayyib(halal, toxins) -> str:
    if halal and toxins:
        return "REJECT [2:168] ليس طيبا"
    if not halal:
        return "REJECT [2:168]"
    return "APPROVE [2:168]"


def check_khabaith(items) -> str:
    bad = ["khinzir", "maita", "dam", "khamr"]
    for i in items:
        if i in bad:
            return f"REJECT [7:157] خبيث {i}"
    return "APPROVE [7:157]"


def check_khamr(alcohol) -> str:
    if alcohol > 0.5:
        return "REJECT [5:90] خمر"
    return "APPROVE [5:90]"


def check_haram(items) -> str:
    haram = ["maita", "dam", "khinzir"]
    for i in items:
        if i in haram:
            return f"REJECT [2:173] حرام {i}"
    return "APPROVE [2:173]"


# تجربة
print(check_israf(400, 500))
print(check_tayyib(True, []))
print(check_khabaith(["qamh"]))
print(check_khamr(0.6))
print(check_haram(["qamh"]))
