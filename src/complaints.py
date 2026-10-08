import re

PATTERNS = {
    "not_received": r"n\u00e3o recebi|nao recebi|n\u00e3o chegou|nao chegou|n\u00e3o entreg|nao entreg",
    "delay": r"atras|prazo|demor",
    "quality": r"defeito|quebrad|qualidade|danific|n\u00e3o funciona|nao funciona",
    "wrong_item": r"errado|diferente|outro produto",
    "incomplete": r"faltou|falta|s\u00f3 um|so um|apenas um",
    "refund": r"cancel|estorno|reembolso|devol",
    "stock": r"estoque",
}


def categorize(text):
    """Return the sorted list of complaint categories found in a review."""
    t = re.sub(r"\s+", " ", str(text).lower())
    return sorted(k for k, p in PATTERNS.items() if re.search(p, t))
