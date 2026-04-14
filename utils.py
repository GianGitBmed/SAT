# utils.py

def extract_id(s: str) -> str:
    """Estrae l'ID numerico dalla stringa formattata 'ID - Nome' o 'ID1 - Nome | ID2 - Nome'."""
    if not s: return ""
    if "|" in s:
        parts = [p.split(" - ")[0].strip() for p in s.split("|") if p.strip()]
        return "|".join(parts)
    return s.split(" - ")[0].strip() if " - " in s else s

def parse_int_list(s: str) -> list:
    """Converte una stringa di ID separati da pipe in una lista di interi."""
    if not s: return []
    return [int(float(x.strip())) for x in s.split('|') if x.strip() and x.strip().replace('.','',1).isdigit()]

def parse_str_list(s: str) -> list:
    """Converte una stringa di valori separati da pipe in una lista di stringhe."""
    if not s: return []
    return [x.strip() for x in s.split('|') if x.strip()]

def get_db_list(local_db: dict, category: str) -> list:
    """Formatta i dizionari del DB locale in liste ordinate per le ComboBox della UI."""
    items = local_db.get(category, {})
    return sorted([f"{k} - {v}" for k, v in items.items()]) if items else []