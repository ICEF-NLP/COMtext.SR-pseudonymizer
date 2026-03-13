from typing import Tuple

from comtext_sr_pseudonymizer.constants import MONEY_CURRENCY_DICT, NUMBERS_TO_WORDS_DICT
from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity
from comtext_sr_pseudonymizer.patterns import ANY_NUMBER_STEM_OR_INDICATOR_SUBSTRING, TEXT_NUMERIC_CORE_TEXT, CONTAINS_DIGIT

class MoneyAnonymizer(BaseAnonymizer):
    """
    Anonymizes monetary values while preserving numeric scale and Serbian grammatical rules.
    
    This class handles the conversion of numeric amounts (e.g., 1.200,50) into anonymized 
    versions and updates the 'written-out' (slovima) text to match the new amount 
    using correct Serbian declension (gender and case).

    Assumes the money number format is ddd,ddd,ddd,ddd.dd
    Always turns the subcurrency into 00
    """

    def _anonymize_entity(self, entity: Entity) -> str:
        """
        Main logic for parsing, randomizing, and reconstructing money strings.
        """
        # Quick check if the string contains any numeric data; if not, return as is.
        if not CONTAINS_DIGIT.search(entity.original_text):
            return entity.original_text

        # Use regex to split the text into three parts:
        # Group 1 (Prefix): Text before the number (e.g., "Iznos od ")
        # Group 2 (Core): The digits, dots, and commas (e.g., "1.250,50")
        # Group 3 (Suffix): Text after the number (e.g., " RSD (hiljadu dvesta pedeset dinara)")
        match = TEXT_NUMERIC_CORE_TEXT.match(entity.original_text.strip())
        if not match:
            return entity.original_text
        
        prefix_text = match.group(1)           
        original_number_string = match.group(2)
        suffix_text = match.group(3)
        
        # Seed the RNG based on the original numeric value and document context
        # This ensures that "1.250,50" is always replaced by the same random value in one document.
        self.rng.seed(entity.get_seed_string(original_number_string, self.timestamp))

        is_leading_digit = True
        is_decimal_section = False 
        anonymized_digits = ""
        
        # Step 1: Anonymize the numeric string character by character while preserving formatting.
        for char in original_number_string:
            if char == ",":
                is_decimal_section = True
                anonymized_digits += char
                continue
            
            if char.isdigit():
                if is_decimal_section:
                    # Legal/Banking standard: Round all decimals to '.00' to hide exact cents.
                    anonymized_digits += "0"
                elif is_leading_digit:
                    # Prevent leading zeros (e.g., "0.500") unless it was originally "0".
                    anonymized_digits += str(self.rng.randint(1, 9))
                    is_leading_digit = False
                else:
                    anonymized_digits += str(self.rng.randint(0, 9))
            else:
                # Preserves thousands separators (usually dots in Serbian: 1.000).
                anonymized_digits += char
        
        # Check if the document contains the "written-out" version of the amount.
        has_written_component = self._detect_written_numbers(suffix_text)
        if not has_written_component:
            return f"{prefix_text}{anonymized_digits}{suffix_text}"
        
        # Step 2: Handle Serbian Grammar for the "written-out" part (e.g., "slovima: ...").
        # Clean the numeric string to get a raw integer for grammatical logic.
        integer_part_only = anonymized_digits.split(",")[0].replace(".", "")
        last_two_digits = int(integer_part_only) % 100
        
        # Serbian Grammatical Rule: Numbers ending in 1 (except 11) are singular.
        # e.g., 21 is "jedan" (singular), but 11 is "jedanaest" (plural genitive).
        is_singular = (last_two_digits % 10 == 1) and (last_two_digits != 11)

        # Map the currency (RSD, EUR) to its correct Serbian case (dinar vs dinara).
        currency_short, currency_long = self._detect_currency(suffix_text, is_singular)
        
        # Convert the new random number into Serbian words (e.g., 1500 -> "hiljada petsto").
        new_word_representation = self._build_word_from_number(anonymized_digits)

        # Standardize the output format for legal clarity.
        label = ""
        if "slovima" in suffix_text.lower():
            label = "slovima : "
            
        return f"{prefix_text}{anonymized_digits} {currency_short} ({label}{new_word_representation} {currency_long})".strip()

    def _detect_written_numbers(self, text: str) -> bool:
        """Checks if the text contains keywords or stems indicating the amount is written out."""
        lower_text = text.lower()
        if "slovima" in lower_text:
            return True
        return bool(ANY_NUMBER_STEM_OR_INDICATOR_SUBSTRING.search(lower_text))

    def _detect_currency(self, text: str, is_singular: bool) -> Tuple[str, str]:
        """Identifies currency and selects the correct singular/plural case based on the amount."""
        found_short = ""
        found_long = ""
        
        for short, long_variants in MONEY_CURRENCY_DICT.items():
            if short in text or any(variant in text for variant in long_variants):
                found_short = short
                # long_variants[1] is singular (dinar), [0] is plural (dinara).
                if is_singular:
                    found_long = long_variants[1]
                else:
                    found_long = long_variants[0]
                break
        
        # Fallback to Serbian Dinar if no specific currency is found in the text.
        if not found_short:
            found_short = "RSD"
            if is_singular:
                found_long = "dinar"
            else:
                found_long = "dinara"
            
        return found_short, found_long

    def _build_word_from_number(self, numeric_str: str) -> str:
        """Converts a numeric string into Serbian words, handling millions, thousands, etc."""
        whole_number_str = numeric_str.split(",")[0].replace(".", "")
        try:
            current_value = int(whole_number_str)
        except ValueError:
            return ""

        if current_value == 0:
            return "nula"

        # Definition of scales: (Threshold value, Word stem, Grammatical Gender, Category name)
        # Gender matters for 'one' and 'two' (jedan milion vs jedna hiljada).
        magnitude_scales = [
            (1_000_000_000, "milijard", "f", "milijarda"),
            (1_000_000, "milion", "m", "milion"),
            (1_000, "hiljad", "f", "hiljada"),
            (1, "", "", "")
        ]
        
        result_words = []

        for limit, stem, gender, category in magnitude_scales:
            if current_value >= limit:
                chunk = current_value // limit
                current_value %= limit
                
                # Special Case: Serbian often uses "hiljadu" instead of "jedna hiljada" for exactly 1,000.
                if category == "hiljada" and chunk == 1:
                    result_words.append("hiljadu")
                else:
                    # Convert the 3-digit chunk (e.g., 500) to words.
                    result_words.append(self._convert_triplet_to_words(chunk, gender))
                    # Add the scale label (miliona, hiljade, etc.) with correct declension.
                    if stem != "":
                        result_words.append(self._get_grammatical_label(chunk, stem, category))
                        
        return " ".join(result_words).strip()

    def _convert_triplet_to_words(self, value: int, gender: str) -> str:
        """Converts a 3-digit group (0-999) into words, respecting gender agreement."""
        parts = []
        if value >= 100:
            # Handle hundreds (stotina, dvesta, trista...).
            parts.append(NUMBERS_TO_WORDS_DICT[str((value // 100) * 100)])
            value %= 100
            
        if value > 0:
            # Handle unique teen names (11-19).
            if 10 < value < 20:
                parts.append(NUMBERS_TO_WORDS_DICT[str(value)])
            else:
                tens = (value // 10) * 10
                ones = value % 10
                if tens:
                    parts.append(NUMBERS_TO_WORDS_DICT[str(tens)])
                if ones:
                    word = NUMBERS_TO_WORDS_DICT[str(ones)]
                    # Grammatical gender adjustment:
                    # '1' -> jedan (m), jedna (f); '2' -> dva (m), dve (f).
                    if gender == "f":
                        if ones == 1:
                            word = "jedna"
                        if ones == 2:
                            word = "dve"
                    parts.append(word)
        return " ".join(parts)

    def _get_grammatical_label(self, value: int, stem: str, category: str) -> str:
        """Returns the correct suffix for magnitudes (hiljada/milion) based on Serbian counting rules."""
        last_digit = value % 10
        last_two = value % 100
        
        # Rule 1: 11-19 always take Genitive Plural (e.g., 15 miliona).
        if 11 <= last_two <= 19:
            if category == "milijarda":
                return "milijardi"
            return f"{stem}a" 
        
        # Rule 2: Numbers ending in 1 take Nominative Singular.
        if last_digit == 1:
            if category == "milion":
                return stem # jedan milion
            return f"{stem}a" # jedna hiljada, jedna milijarda
            
        # Rule 3: Numbers ending in 2, 3, 4 take the Paucal case.
        if 2 <= last_digit <= 4:
            if category == "milijarda":
                return "milijarde"
            if category == "hiljada":
                return "hiljade"
            return "miliona" # Paucal for Million is 'miliona'
            
        # Rule 4: Numbers ending in 5-9 or 0 take Genitive Plural.
        if category == "milijarda":
            return "milijardi"
        return f"{stem}a"