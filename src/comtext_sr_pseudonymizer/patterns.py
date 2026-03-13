import re

from comtext_sr_pseudonymizer.constants import (
    NUMBER_STEMS, 
    NUMBERS_TO_WORDS_DICT, 
    MONTH_DICTIONARY
)

# ==============================================================================
# 1. WHITESPACE & CLEANING PATTERNS
# ==============================================================================

# Targets: [Two or more whitespace characters]
WHITESPACE_SEQUENCE = re.compile(r'\s\s+')

# Targets: [Non-whitespace character][Comma]
# Logic: Checks the left side for a letter/number stuck to the comma
NON_WHITESPACE_COMMA = re.compile(r'(?<=\S),') 

# Targets: [Optional Whitespace][Open Paren][Optional Whitespace]
WHITESPACE_PAREN_OPEN_WHITESPACE = re.compile(r'\s*\(\s*')

# Targets: [Optional Whitespace][Close Paren][Optional Whitespace]
WHITESPACE_PAREN_CLOSE_WHITESPACE = re.compile(r'\s*\)\s*')

# Targets: [Optional Whitespace][Comma][Optional Whitespace]
WHITESPACE_COMMA_WHITESPACE = re.compile(r'\s*,\s*')

# Targets: [Dot][Whitespace][Digit]
DOT_WHITESPACE_DIGIT = re.compile(r'(?<=\.)\s+(?=\d)')

# Targets: [Dot][Letter]
# Logic: Specifically targets dots stuck to characters (missing space)
DOT_LETTER = re.compile(r'(?<=\.)(?=[a-zA-ZčćžšđČĆŽŠĐ])')


# ==============================================================================
# 2. ENTITY & ABBREVIATION LOGIC
# ==============================================================================

# Sequence: [Start][d.o.o. OR a.d. OR u OR iz][End]
EXACT_COMPANY_SUFFIX_OR_PREPOSITION = re.compile(r'^(?:d\.?o\.?o\.?|a\.?d\.?|u|iz)$', re.IGNORECASE)

# Targets: [Boundary][J][Opt. Dot][Opt. Space][P][Opt. Dot][Boundary]
ABBR_J_P_DOT_SPACE_OPTIONAL = re.compile(r'\bj\.?\s?p\.?\b', re.IGNORECASE)

# Targets the preposition "u" as a standalone word
WORD_BOUNDARY_U_WORD_BOUNDARY = re.compile(r'\b[Uu]\b')

# Sequence: [Start of string][One or more Serbian/English letters]
# Note: Extracts city codes from strings like NUMCAR
START_CITY_CODE_LETTERS = re.compile(r"^[a-zA-ZČĆŽŠĐčćžšđ]+")

# Sequence: [Any of the specified quote or dash characters]
# Note: Used to clean lemmas by removing Serbian-specific quotes and various dash types
CORPORATE_STRIP_PUNCTUATION_AND_QUOTES = re.compile(r'[\'\"“„\-—–−”‘«»’]')


# ==============================================================================
# 3. NUMBER & MONEY EXTRACTION
# ==============================================================================

# Sequence: [Any single digit 0-9]
CONTAINS_DIGIT = re.compile(r"\d")

# Sequence: [1: Prefix][2: Numeric Core (Digits/Dots/Commas)][3: Suffix]
TEXT_NUMERIC_CORE_TEXT = re.compile(r"^([^0-9]*)([\d.,]*\d)(.*)")

# Targets: [0-9][+][-][/][Space] - Used to validate contact number strings
CONTACT_NUMBER_CHARS_ONLY = re.compile(r"^[0-9/\-\+ ]+$")

# Targets: [The first character that is NOT a digit]
FIRST_NON_DIGIT_CHARACTER = re.compile(r'\D')

# Sequence: [Any of the number stems or word indicators found anywhere in string]
ANY_NUMBER_STEM_OR_INDICATOR_SUBSTRING = re.compile(
    "|".join(set(NUMBER_STEMS + list(NUMBERS_TO_WORDS_DICT.values()))), 
    re.IGNORECASE
)


# ==============================================================================
# 4. COMPLEX DATE SEQUENCES
# ==============================================================================

# Build the shared month OR-chain for date patterns
month_words_pattern = "|".join([name for names in MONTH_DICTIONARY.values() for name in names])

# Sequence: [StartText][Day][Dot][MonthName/Num][Dot][Year][Dot][EndText]
TEXT_DAY_DOT_MONTH_DOT_YEAR_DOT_TEXT = re.compile(
    rf"^(.*?)(\d{{1,2}})(\.\s*)({month_words_pattern}|\d{{1,2}})(\.?\s*)(\d{{4}})(\.?)(.*)$", 
    re.IGNORECASE | re.DOTALL
)

# Sequence: [StartText][MonthName][Space][Year][Dot][EndText]
TEXT_MONTH_SPACE_YEAR_DOT_TEXT = re.compile(
    rf"^(.*?)({month_words_pattern})(\s+)(\d{{4}})(\.?)(.*)$", 
    re.IGNORECASE | re.DOTALL
)

# Sequence: [StartText][Boundary][4-Digits][Boundary][OptionalDot][EndText]
TEXT_YEAR_DOT_TEXT = re.compile(
    r"^(.*?)(\b\d{4}\b)(\.?)(.*)$", 
    re.IGNORECASE | re.DOTALL
)

# Sequence: [StartText][Boundary][MonthName][Boundary][EndText]
TEXT_MONTH_TEXT = re.compile(
    rf"^(.*?)(\b{month_words_pattern}\b)(.*)$", 
    re.IGNORECASE | re.DOTALL
)