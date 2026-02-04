def to_cyrillic(text):
    """
    Converts Uzbek Latin text to Cyrillic.
    Simple mapping for common characters.
    """
    mapping = {
        "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ",
        "i": "и", "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о",
        "p": "п", "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в",
        "x": "х", "y": "й", "z": "з", "o'": "ў", "g'": "ғ", "sh": "ш", "ch": "ч",
        "ng": "нг", "ye": "е", "yo": "ё", "yu": "ю", "ya": "я", "'": "ъ",
        
        # Uppercase
        "A": "А", "B": "Б", "D": "Д", "E": "Е", "F": "Ф", "G": "Г", "H": "Ҳ",
        "I": "И", "J": "Ж", "K": "К", "L": "Л", "M": "М", "N": "Н", "O": "О",
        "P": "П", "Q": "Қ", "R": "Р", "S": "С", "T": "Т", "U": "У", "V": "В",
        "X": "Х", "Y": "Й", "Z": "З", "O'": "Ў", "G'": "Ғ", "SH": "Ш", "CH": "Ч",
        "NG": "НГ", "YE": "Е", "YO": "Ё", "YU": "Ю", "YA": "Я"
    }
    
    # Sort keys by length in descending order to handle multi-char mappings first (like 'sh', 'ch', "o'")
    sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
    
    result = text
    for key in sorted_keys:
        result = result.replace(key, mapping[key])
        
    return result

def to_latin(text):
    """
    Converts Uzbek Cyrillic text to Latin.
    """
    mapping = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
        "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "x", "ц": "s", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "'",
        "ы": "i", "э": "e", "ю": "yu", "я": "ya", "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
        
        # Uppercase
        "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "Yo",
        "Ж": "J", "З": "Z", "И": "I", "Й": "Y", "К": "K", "Л": "L", "М": "M",
        "Н": "N", "О": "O", "П": "P", "Р": "R", "С": "S", "Т": "T", "У": "U",
        "Ф": "F", "Х": "X", "Ц": "S", "Ч": "Ch", "Ш": "Sh", "Щ": "Sh", "Ъ": "'",
        "Ы": "I", "Э": "E", "Ю": "Yu", "Я": "Ya", "Ў": "O'", "Қ": "Q", "Ғ": "G'", "Ҳ": "H"
    }
    
    result = text
    for key, value in mapping.items():
        result = result.replace(key, value)
        
    return result

def normalize_query(query):
    """
    Attempts to guess the script and normalize to Cyrillic for database search.
    If the query seems to be Latin, convert to Cyrillic.
    """
    # Simple heuristic: unmatched latin characters suggest Latin script
    latin_chars = set("abcdefghijklmnopqrstuvwxyzo'g'shch")
    query_chars = set(query.lower())
    
    # If substantial overlap with latin chars, assume latin
    if query_chars.intersection(latin_chars):
        return to_cyrillic(query)
    
    return query
