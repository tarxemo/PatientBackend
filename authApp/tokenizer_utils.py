import re

def syllable_tokenizer(text):
    vowels = "aeiou"
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    words = text.split()
    syllables = []

    for word in words:
        i = 0
        w_len = len(word)
        word_syllables = []
        while i < w_len:
            if word[i] in vowels:
                if i + 1 < w_len and word[i + 1] in vowels:
                    word_syllables.append(word[i])
                    i += 1
                else:
                    word_syllables.append(word[i])
                    i += 1
                continue

            if i + 1 < w_len and word[i+1] in vowels:
                if word[i:i+2] in ['mw', 'ny', 'ng', 'nd', 'mb', 'nj', 'sy', 'sh']:
                    if i + 2 < w_len and word[i+2] in vowels:
                        word_syllables.append(word[i:i+3])
                        i += 3
                        continue
                word_syllables.append(word[i:i+2])
                i += 2
                continue

            if i + 2 < w_len and word[i+1] in vowels and word[i+2] not in vowels:
                word_syllables.append(word[i:i+3])
                i += 3
                continue

            word_syllables.append(word[i])
            i += 1

        syllables.extend(word_syllables)

    return syllables
