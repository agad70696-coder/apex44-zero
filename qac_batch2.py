# [7:31] ولا تسرفوا - [2:168] حلالا طيبا
def check_israf(pack, total):
    if total==0: return "REVIEW"
    if pack*100/total > 30: return "REVIEW [7:31] اسراف"
    return "APPROVE"

def check_tayyib(halal, toxins):
    if halal and len(toxins)>0: return "REJECT [2:168] ليس طيبا"
    if not halal: return "REJECT"
    return "APPROVE"
