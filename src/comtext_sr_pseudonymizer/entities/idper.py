import random
from datetime import datetime, timedelta
from typing import List

from comtext_sr_pseudonymizer.constants import IDPER_REGION_DICTIONARY
from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity

# Source for JMBG structure: 
# https://pravno-informacioni-sistem.rs/eli/rep/sgrs/skupstina/zakon/2018/24/6/reg
# Legally mandated length for the Yugoslav/Serbian JMBG
IDPER_DIGITS = 13

# Calculation constraints:
# Using 20 and 100 years to simplify leap year logic (Feb 29).
# Note: Years divisible by 4 are leap years, except for years divisible by 100 
# but not 400 (e.g., 1900 is not a leap year but 2000 is).
# Generation boundaries to ensure the fake JMBG represents an adult
END_DATE_YEARS_BEFORE_TODAY = 20 
START_DATE_YEARS_BEFORE_TODAY = 100 

class PersonIDAnonymizer(BaseAnonymizer):
    """
    Anonymizes the Serbian JMBG. 
    Constructs a synthetic 13-digit number that preserves gender but 
    randomizes birth date and region, using an invalid checksum for safety.
    """
    
    def __init__(self, timestamp: str, rng: random.Random) -> None:
        super().__init__(timestamp, rng)
        today = datetime.today()
        # Create a sliding window for realistic birth years
        self.end_date = today.replace(year=today.year - END_DATE_YEARS_BEFORE_TODAY)
        self.start_date = today.replace(year=today.year - START_DATE_YEARS_BEFORE_TODAY)

    def anonymize(self, list_of_entities: List[Entity]) -> List[Entity]:
        """Validates length before triggering the component-based anonymization."""
        for entity in list_of_entities:
            if len(entity.original_text) != IDPER_DIGITS:
                # Log invalid lengths (JMBG must be exactly 13 digits)
                print(f"IDPER number {entity.original_text} is incorrect. Must have {IDPER_DIGITS} digits")
                entity.anonymized_text = entity.original_text
            else:
                entity.anonymized_text = self._anonymize_entity(entity)
            
            # Flush morphological data from memory
            entity.clean_up()
        return list_of_entities

    def _anonymize_entity(self, entity: Entity) -> str:
        """Assembles the JMBG parts: DDMMYYY + RR + GGG + K."""
        # Ensure referential integrity: same JMBG in same doc -> same fake JMBG
        self.rng.seed(entity.get_seed_string(entity.original_text, self.timestamp))
        
        # 1. First 7 digits: DDMMYYY (Birth date)
        birthday_segment = self._random_birthday()
        # 2. Next 2 digits: RR (Political region)
        region_segment = self._random_region()
        # 3. Next 3 digits: GGG (Gender and unique identifier)
        gender_segment = self._random_gender(entity.original_text)
        
        # Combine the first 12 digits to calculate the checksum
        base_12_digits = f"{birthday_segment}{region_segment}{gender_segment}"
        
        # 4. Final digit: K (Control/Checksum)
        # false_control_number=True ensures this ID will fail official validation
        control_digit = self._generate_control(base_12_digits, false_control_number=True)
        
        return f"{base_12_digits}{control_digit}"
    
    def _random_birthday(self) -> str:
        """Generates birthday segment. Note: JMBG uses only last 3 digits of the year."""
        delta = self.end_date - self.start_date
        random_day_count = self.rng.randint(0, delta.days)
        random_date = self.start_date + timedelta(days=random_day_count)
        
        day_str = f"{random_date.day:02d}"
        month_str = f"{random_date.month:02d}"
        # Year 1985 -> '985', Year 2010 -> '010'
        year_str = str(random_date.year)[-3:]
        
        return f"{day_str}{month_str}{year_str}"
    
    def _random_region(self) -> str:
        """Picks a random valid Yugoslavian region code (e.g., 71 for Belgrade)."""
        return self.rng.choice(list(IDPER_REGION_DICTIONARY.keys()))
    
    def _random_gender(self, original_idper: str) -> str:
        """Preserves sex: Males (000-499), Females (500-999)."""
        gender_code_str = original_idper[9:12]
        gender_int = int(gender_code_str)
        
        if gender_int < 500:
            new_code = self.rng.randint(0, 499)
        else:
            new_code = self.rng.randint(500, 999)
        return f"{new_code:03d}"
        
    def _generate_control(self, idper_12: str, false_control_number: bool = True) -> int:
        """
        Calculates the Modulo 11 checksum.
        If false_control_number is True, it explicitly returns a WRONG digit.
        """
        digits = [int(char) for char in idper_12]
        
        # Weighted sum formula: 7*(D1+D7) + 6*(D2+D8) + 5*(D3+D9) + ...
        weighted_sum = (
            7 * (digits[0] + digits[6]) +
            6 * (digits[1] + digits[7]) +
            5 * (digits[2] + digits[8]) +
            4 * (digits[3] + digits[9]) +
            3 * (digits[4] + digits[10]) +
            2 * (digits[5] + digits[11])
        )
        
        remainder = weighted_sum % 11
        m_value = 11 - remainder
        
        # Standard JMBG rule: if 10 or 11, the digit is 0
        control = m_value if m_value <= 9 else 0
            
        if not false_control_number:
            return control
            
        # ANONYMIZATION POISONING: Pick any digit EXCEPT the valid one.
        # This makes the ID look real to the naked eye but fail any computer check.
        false_choices = [i for i in range(10) if i != control]
        return self.rng.choice(false_choices)