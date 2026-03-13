import random
from typing import List

from comtext_sr_pseudonymizer.constants import NUMCAR_PLATE_LIST
from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity
from comtext_sr_pseudonymizer.patterns import START_CITY_CODE_LETTERS, CONTAINS_DIGIT

class CarNumberAnonymizer(BaseAnonymizer):
    """
    Anonymizes vehicle identification data including Serbian license plates and VINs.
    
    The logic preserves the original formatting (spaces, dashes) and replaces city 
    codes and digits while maintaining the original digit count for realism.
    """

    def _anonymize_entity(self, entity: Entity) -> str:
        """
        Internal logic to determine identifier type and apply replacement.
        
        Handles:
        1. VINs (17 chars, alphanumeric)
        2. License plates (extracts city code and replaces digits)
        """
        entity.original_text = entity.original_text.strip()
        
        # Branch to VIN logic if string meets the 17-char alphanumeric standard
        if len(entity.original_text) == 17 and entity.original_text.isalnum():
            return self._anonymize_VIN(entity)
        
        # Extract leading city code (including Serbian Latin characters)
        # Assumes every NUMCAR starts with it's city code
        city_match = START_CITY_CODE_LETTERS.match(entity.original_text)
        orig_city_code = city_match.group(0) if city_match else ""
        
        # Isolate digits for seeding and determining the replacement pool size
        digits_only = "".join(CONTAINS_DIGIT.findall(entity.original_text))
        normalized_seed = f"{orig_city_code.lower()}{digits_only}"
        self.rng.seed(entity.get_seed_string(normalized_seed, self.timestamp))
        
        # Selection of new city and digit replacements
        new_city = self.rng.choice(NUMCAR_PLATE_LIST)
        digits = self.rng.choices("0123456789", k=len(digits_only))
        
        result: List[str] = []
        city_replaced = False
        digit_ptr = 0
        orig_city_len = len(orig_city_code)
        letters_processed = 0
        
        for char in entity.original_text:
            if char.isalpha():
                # Replace the initial block of letters (city code) only once
                if letters_processed < orig_city_len:
                    if not city_replaced:
                        result.append(new_city)
                        city_replaced = True
                    letters_processed += 1
                else:
                    # Keep suffix letters or descriptive words like "tablice"
                    result.append(char)
            elif char.isdigit():
                # Sequentially replace digits from the generated pool
                if digit_ptr < len(digits):
                    result.append(digits[digit_ptr])
                    digit_ptr += 1
            else:
                # Keep symbols, spaces, and punctuation
                result.append(char)
                
        return "".join(result)

    def _anonymize_VIN(self, entity: Entity, false_control: bool = True) -> str:
        """
        Anonymizes a 17-character VIN while keeping the WMI and calculating check digits.
        """
        self.rng = random.Random(entity.get_seed_string(entity.original_text, self.timestamp))
        vin_chars = "0123456789ABCDEFGHJKLMNPRSTUVWXYZ"
        
        wmi = entity.original_text[:3].upper()
        res = list(wmi) + self.rng.choices(vin_chars, k=14)
        
        char_map = {
            "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
            "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
            "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9
        }
        weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
        
        total = 0
        for i in range(17):
            if i == 8: 
                continue
            char = res[i]
            val = int(char) if char.isdigit() else char_map[char]
            total += val * weights[i]
            
        check_digit = str(total % 11)
        if check_digit == "10":
            check_digit = "X"
            
        if not false_control:
            res[8] = check_digit
            return "".join(res)
            
        # Select a random incorrect check digit
        possible_check_chars = list("0123456789X")
        if check_digit in possible_check_chars:
            possible_check_chars.remove(check_digit)
        res[8] = self.rng.choice(possible_check_chars)
        
        return "".join(res)