import random

from comtext_sr_pseudonymizer.constants import EMAIL_ENDINGS, SERBIAN_PHONE_OPERATORS
from comtext_sr_pseudonymizer.data_manager import DataManager
from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity
from comtext_sr_pseudonymizer.patterns import CONTACT_NUMBER_CHARS_ONLY, FIRST_NON_DIGIT_CHARACTER

class ContactAnonymizer(BaseAnonymizer):
    """
    Anonymizes contact information including Emails, URLs, and Phone Numbers.
    
    This class identifies the type of contact data and applies specific 
    anonymization strategies: synthetic identity generation for emails, 
    search redirection for URLs, and prefix-preserving randomization for 
    Serbian phone numbers.
    """
    
    def __init__(self, timestamp: str, rng: random.Random,  data_manager: DataManager) -> None:
        super().__init__(timestamp, rng, data_manager)

        self.mobile_prefixes = list(SERBIAN_PHONE_OPERATORS["mobile"].keys())
        self.landline_prefixes = list(SERBIAN_PHONE_OPERATORS["landline"].keys())
    
    def _anonymize_entity(self, entity: Entity) -> str:
        """Routes the contact string to the appropriate anonymization method."""
        # Create a deterministic seed based on the specific contact and session time
        self.rng.seed(entity.get_seed_string(entity.original_text, self.timestamp))
        
        # 1. Email Detection
        if "@" in entity.original_text:
            return self._anonymize_email()
            
        # 2. URL Detection
        elif entity.original_text.lower().startswith(("http:", "https:", "www.")):
            return self._anonymize_url()
            
        # 3. Phone Number Detection (Digits and common separators)
        elif CONTACT_NUMBER_CHARS_ONLY.match(entity.original_text):
            return self._anonymize_phone(entity.original_text)
            
        # 4. Fallback
        else:
            print(f"CONTACT {entity.original_text} can't be matched to email, url or phone number")
            return entity.original_text

    def _anonymize_email(self) -> str:
        """Generates a synthetic email using random names and common domains."""
        gender_choice = self.rng.choice(["m", "f"])
        
        if gender_choice == "m":
            first_name = self.data_manager.get_random_male_name(self.rng, lower=True)
        else:
            first_name = self.data_manager.get_random_female_name(self.rng, lower=True)
            
        last_name = self.data_manager.get_random_surname(self.rng, lower=True)
        domain = self.rng.choice(EMAIL_ENDINGS)
        
        return f"{first_name}.{last_name}@{domain}"

    def _anonymize_url(self) -> str:
        """Replaces original URL with a generic Google 'I'm Feeling Lucky' search."""
        lucky_number = self.rng.randint(1000, 9_999_999)
        return f"https://www.google.com/search?q={lucky_number}&btnI=1"
    
    def _anonymize_phone(self, contact: str) -> str:
        """
        Anonymizes phone numbers while preserving the network type (Mobile vs Landline).
        Standardizes the output to the Serbian format: XXX/XXX-XXXX.
        """
        # Clean international prefix for easier network detection
        clean_contact = contact.lstrip('+')
        
        # Attempt to find the first separator to isolate the network prefix
        separator_match = FIRST_NON_DIGIT_CHARACTER.search(clean_contact)
        
        if separator_match:
            separator_index = separator_match.start()
            extracted_prefix = clean_contact[:separator_index]
        else:
            # Fallback for numbers without separators (e.g., 0651231234)
            extracted_prefix = clean_contact[:3]
            
        # Check if the extracted prefix belongs to a mobile operator
        is_mobile = extracted_prefix in self.mobile_prefixes
        
        if is_mobile:
            new_prefix = self.rng.choice(self.mobile_prefixes)
        else:
            new_prefix = self.rng.choice(self.landline_prefixes)
            
        # Generate a random 7-digit subscriber number
        subscriber_id_val = self.rng.randint(0, 9_999_999)
        subscriber_id_str = str(subscriber_id_val).zfill(7)
        
        # Construct the final number in standard Serbian format
        # Example: XXX/XXX-XXXX
        return f"{new_prefix}/{subscriber_id_str[:3]}-{subscriber_id_str[3:]}"