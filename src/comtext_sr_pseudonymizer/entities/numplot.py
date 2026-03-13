from comtext_sr_pseudonymizer.constants import ROMAN_NUMBERS
from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity

class PlotNumberAnonymizer(BaseAnonymizer):
    """Anonymizes cadastral plot numbers while preserving formatting and digit length."""

    def _anonymize_entity(self, entity: Entity) -> str:
        """Determines the plot format and generates a corresponding fake number."""
        self.rng.seed(entity.get_seed_string(entity.original_text, self.timestamp))

        # Case 1: Roman Numerals (e.g., 'II')
        if entity.original_text.upper() in ROMAN_NUMBERS:
            return self.rng.choice(ROMAN_NUMBERS)

        # Case 2: Divided plots (e.g., '123/4')
        if "/" in entity.original_text:
            parts = [p.strip() for p in entity.original_text.split("/")]
            # Process each part individually to maintain the slash structure
            gen_parts = [self._get_same_number_of_digits_random(p) for p in parts]
            return "/".join(gen_parts)

        # Case 3: Simple integer plots
        return self._get_same_number_of_digits_random(entity.original_text)

    def _get_same_number_of_digits_random(self, original_str: str) -> str:
        """Generates a random number with the same number of digits as the original."""
        # Ensure we are dealing with digits to avoid ValueError on int()
        digits_only = "".join(filter(str.isdigit, original_str))
        if not digits_only:
            return original_str # Fallback if no digits present

        length = len(digits_only)
        
        # Calculate bounds: e.g., for 3 digits, low=100, high=999
        low = 10**(length - 1)
        high = (10**length) - 1
        
        # Heuristic: Avoid unrealistic sub-plot numbers
        # If the number is large, cap the upper bound to keep it realistic
        if high > 100:
            high = max(low + 1, high // 5)
            
        fake_val = self.rng.randint(low, high)
            
        return str(fake_val).zfill(length)