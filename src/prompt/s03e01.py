NAMES_PROMPT = """
Na podstawie tekstu napisz o jakiej osobie jest teskt.
Podaj imię i nazwisko w pierwszej osobie liczby pojedyńczeń.

Podaj tylko i imię i nazwisko reszta tektstu jest zbędna.
Imię i nazwisko powinno być podane wprost w tekście.
W przypadku jego braku wpisz wartość: "Brak"

Przykład output:
"Jan Kowalski"

Nazwa Pliku:
{filename}

Tekst do analizy:
{content}
"""

KEYWORD_PROMPT = """
Wyodrębnij słowa kluczowe z poniższego tekstu i jego tytłu według następujących zasad:

Zasady wyodrębniania:
- Uwzględnij tylko pojęcia istotne dla głównego przekazu tekstu
- Zachowaj słowa w języku polskim
- Podaj każde słowo w mianowniku liczby pojedynczej
- Z nazwy pliku wyodrebnij datę i numer sektoru (na przykład "2024-11-12", "sektor C4" (usuń "_"))
- Pamiętaj nazwa pliku też jest istotna zawiera datę i miejsce (sektor), którą trzeba dodać 
- Odcisk palców potraktuj jako słowo kluczowe

Format wyjściowy:
- Tylko lista słów kluczowych
- Słowa oddzielone przecinkami
- Bez dodatkowego formatowania czy opisów

Przykład output:
słowo_klucz_1, słowo_klucz_2, słowo_klucz_n

Nazwa Pliku:
{filename}

Tekst do analizy:
{content}
"""
