def to_latin(text):
    if not text:
        return ""
    
    mapping = {
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'J', 'З': 'Z',
        'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P',
        'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'X', 'Ц': 'Ts', 'Ч': 'Ch',
        'Ш': 'Sh', 'Ъ': "'", 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya', 'Ў': "O'", 'Қ': 'Q',
        'Ғ': "G'", 'Ҳ': 'H',
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z',
        'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
        'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'ъ': "'", 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya', 'ў': "o'", 'қ': 'q',
        'ғ': "g'", 'ҳ': 'h'
    }

    result = []
    for i in range(len(text)):
        char = text[i]
        
        # Special case for 'E'/'e' at the start of a word or after a vowel
        if char.upper() == 'Е':
            if i == 0 or text[i-1].lower() in "аеёиоуэюяўқғҳ":
                res = 'Ye' if char.isupper() else 'ye'
            else:
                res = 'E' if char.isupper() else 'e'
        else:
            res = mapping.get(char, char)
            
        result.append(res)
        
    return "".join(result)
