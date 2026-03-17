import csv
from collections import defaultdict
import random
from typing import Set, List, Tuple

from comtext_sr_pseudonymizer.data_paths import *
from comtext_sr_pseudonymizer.patterns import WHITESPACE_SEQUENCE, NON_WHITESPACE_COMMA

class DataManager:
    """
    Central repository for all lookup data and replacement pools.
    Implemented as a Singleton to prevent redundant memory usage.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
            # Initialize a flag so we only load files once
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        # --- LOOKUP SETS (For existence checks) ---
        # Used for fast 'if name in lookup_set' checks. 
        # Lowercased for case-insensitive matching.
        self.lookup_city_set: Set[str] = read_file(LOOKUP_CITY_PATH, lower=True, set_output=True)
        self.lookup_country_set: Set[str] = read_file(LOOKUP_COUNTRY_PATH, lower=True, set_output=True)
        self.lookup_female_name_set: Set[str] = read_file(LOOKUP_FEMALE_NAME_PATH, lower=True, set_output=True)
        self.lookup_id_company_set: Set[str] = read_file(POOL_IDCOM_COM_PATH, lower=True, set_output=True)
        self.lookup_id_ngo_set: Set[str] = read_file(POOL_IDCOM_NGO_PATH, lower=True, set_output=True)
        self.lookup_male_name_set: Set[str] = read_file(LOOKUP_MALE_NAME_PATH, lower=True, set_output=True)
        self.lookup_municipality_set: Set[str] = read_file(LOOKUP_MUNICIPALITY_PATH, lower=True, set_output=True)
        self.lookup_surname_set: Set[str] = read_file(LOOKUP_SURNAME_PATH, lower=True, set_output=True)

        # --- REPLACEMENT POOLS (For anonymization) ---
        # Ordered lists used to pick a random replacement value.
        self.pool_companies: List[str] = read_file(POOL_COM_PATH)
        self.pool_female_names: List[str] = read_file(POOL_FEMALE_NAME_PATH)
        self.pool_id_companies: List[str] = read_file(POOL_IDCOM_COM_PATH)
        self.pool_id_ngos: List[str] = read_file(POOL_IDCOM_NGO_PATH)
        self.pool_male_names: List[str] = read_file(POOL_MALE_NAME_PATH)
        self.pool_ngos: List[str] = read_file(POOL_NGO_PATH)
        self.pool_streets: List[str] = read_file(POOL_ADR_STREET_PATH)
        self.pool_surnames: List[str] = read_file(POOL_SURNAME_PATH)

        # --- GEOGRAPHIC TRIADS ---
        # Loads correlated City, ZIP, and Municipality data.
        self._load_pool(POOL_ADR_ZIP_PATH)
        self.adr_mapping = defaultdict(list)

        self._initialized = True

    # ==========================================
    # BOOLEAN CHECK METHODS (is_something)
    # ==========================================

    def is_city(self, text: str) -> bool:
        return self._is_something(text, self.lookup_city_set)
    
    def is_country(self, text: str) -> bool:
        return self._is_something(text, self.lookup_country_set)
        
    def is_municipality(self, text: str) -> bool:
        return self._is_something(text, self.lookup_municipality_set)
    
    def is_female_name(self, text: str) -> bool:
        return self._is_something(text, self.lookup_female_name_set)
    
    def is_male_name(self, text: str) -> bool:
        return self._is_something(text, self.lookup_male_name_set)
    
    def is_surname(self, text: str) -> bool:
        return self._is_something(text, self.lookup_surname_set)
    
    def is_id_com(self, text: str) -> bool:
        return self._is_something(text, self.lookup_id_company_set)
    
    def is_id_ngo(self, text: str) -> bool:
        return self._is_something(text, self.lookup_id_ngo_set)

    # ==========================================
    # RANDOM RETRIEVAL METHODS (get_random)
    # ==========================================

    def get_random_male_name(self, rng: random.Random, lower: bool = False) -> str:
        text: str = self._get_random_something(rng, self.pool_male_names)
        return text.lower() if lower else text.title()
        
    def get_random_female_name(self, rng: random.Random, lower: bool = False) -> str:
        text: str = self._get_random_something(rng, self.pool_female_names)
        return text.lower() if lower else text.title()
    
    def get_random_surname(self, rng: random.Random, lower: bool = False) -> str:
        text: str = self._get_random_something(rng, self.pool_surnames)
        return text.lower() if lower else text.title()

    def get_random_ngo(self, rng: random.Random) -> str:
        return self._get_random_something(rng, self.pool_ngos)
    
    def get_random_id_com(self, rng: random.Random) -> str:
        return self._get_random_something(rng, self.pool_id_companies)
    
    def get_random_id_ngo(self, rng: random.Random) -> str:
        return self._get_random_something(rng, self.pool_id_ngos)
    
    def get_random_com(self, rng: random.Random) -> str:
        return self._get_random_something(rng, self.pool_companies)
        
    def get_random_street(self, rng: random.Random) -> str:
        return self._get_random_something(rng, self.pool_streets)
    
    def get_random_zip(self, rng: random.Random) -> str:
        return self._get_random_something(rng, self.pool_zip_list)

    def get_random_city_zip_muni(self, rng: random.Random) -> Tuple[str, str, str]:
        """Returns a synchronized geographic triplet to maintain realistic address data."""
        if not self.pool_city_zip_muni:
            return ("", "", "")
        city, zip_code, muni = rng.choice(self.pool_city_zip_muni)
        return str(city), str(zip_code), str(muni)
    
    def clear_mapping(self):
        self.adr_mapping = defaultdict(list)

    # ==========================================
    # INTERNAL HELPERS
    # ==========================================
    def _is_something(self, text: str, lookup_set: Set[str]) -> bool:
        return text.lower() in lookup_set

    def _get_random_something(self, rng: random.Random, pool_list: List[str]) -> str:
        """Helper to pick a random value and normalize its whitespace."""
        random_text: str = rng.choice(pool_list)
        random_text = NON_WHITESPACE_COMMA.sub(' ,', random_text)
        random_text = WHITESPACE_SEQUENCE.sub(' ', random_text).strip()
        return random_text
    
    def _load_pool(self, path: str) -> None:
        """Parses the TSV file containing ZIP codes and corresponding administrative regions."""
        self.pool_city_zip_muni = []
        self.pool_zip_list: List[str] = [] 
        
        with open(path, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader, None) # Skip header
            
            for row in reader:
                if len(row) >= 3:
                    city, zip_code, muni = row[0], row[1], row[2]
                    
                    # Store the full tuple for random selection
                    self.pool_city_zip_muni.append((city, zip_code, muni))
                    
                    # Store just the ZIP code as a string
                    self.pool_zip_list.append(str(zip_code))