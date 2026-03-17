import csv
import pickle
import random
from typing import List

from comtext_sr_pseudonymizer.data_paths import *


class Lex:
    """
    The linguistic core of the pseudonymizer. 
    Handles morphological inflection (declension) of Serbian names and toponyms 
    to ensure grammatical correctness in anonymized text.
    """
    _instance = None

    def __new__(cls):
        # Singleton pattern to ensure the large lexicon is only loaded once in memory
        if cls._instance is None:
            cls._instance = super(Lex, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        cities: List[str] = []
        municipalities: List[str] = []

        # Load correlated geographic data from the ZIP pool
        with open(POOL_ADR_ZIP_PATH, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                # Using DictReader lets us access by column name directly
                cities.append(row["city"])
                municipalities.append(row["municipality"])
        # Internal pools containing lemmas for random selection
        self.pools = {
            "female": read_file(POOL_FEMALE_NAME_PATH),
            "male": read_file(POOL_MALE_NAME_PATH),
            "surname": read_file(POOL_SURNAME_PATH),
            "city": cities,
            "municipality": municipalities,
            "country": ["Srbija"]
        }

        # Load the main morphological dictionaries, using a binary cache if available
        self.lex_dict, self.relaxed_dict = self._get_cached_srlex()
        
        self._initialized = True

    # --- PUBLIC INFLECTION ENGINE (given lemma) ---
    def get_wordform(self, lemma: str, msd: str) -> str:
        """
        Takes a known lemma and inflects it based on the Morphosyntactic Descriptor (MSD).
        Example: ('Beograd', 'Npmsl') -> 'Beogradu' (Locative case)
        """
        # 1. Exact Match: Highest precision lookup
        wordform = self.lex_dict.get((lemma, msd))
        if wordform:
            return wordform
        
        # 2. Relaxed Match logic: Fallback when the exact tag combination is missing.
        # Serbian MSDs are positional: msd[3] is Number (s/p), msd[4] is Case (n/g/d/a/v/i/l).
        if len(msd) >= 5 and lemma in self.relaxed_dict:
            # Step A: Try matching Number + Case (e.g., 's' for singular + 'g' for genitive)
            target_suffix = f"s{msd[4]}"
            for entry_msd, entry_wordform in self.relaxed_dict[lemma]:
                if entry_msd[3:5] == target_suffix:
                    return entry_wordform
            
            # Step B: Fallback to just Case (msd[4]) if Number match fails
            target_case = msd[4]
            for entry_msd, entry_wordform in self.relaxed_dict[lemma]:
                if entry_msd[4] == target_case:
                    return entry_wordform
                
        # Return the base lemma if no inflected forms are found  
        return lemma

    # --- PSEUDONYMIZATION ENGINE (random lemma) ---
    def _get_random_replacement(self, pool_key: str, msd: str, rng: random.Random, return_lemma: bool = False) -> str:
        """
        Selects a random lemma from the specified pool and inflects it to match the 
        original context's grammatical case.
        """
        pool = self.pools.get(pool_key)
        if not pool:
            return f"ERR_UNKNOWN_POOL_{pool_key}"
            
        random_lemma = rng.choice(pool)
        if return_lemma:
            return random_lemma
        return self.get_wordform(random_lemma, msd)
    
    # --- PUBLIC API WRAPPERS ---
    # These methods are called by specific Anonymizer classes (e.g., PersonAnonymizer)
    
    def anonymize_surname(self, msd: str, rng: random.Random, return_lemma = False) -> str:
        return self._get_random_replacement("surname", msd, rng, return_lemma)
    
    def anonymize_female_name(self, msd: str, rng: random.Random, return_lemma = False) -> str:
        return self._get_random_replacement("female", msd, rng, return_lemma)
    
    def anonymize_male_name(self, msd: str, rng: random.Random, return_lemma = False) -> str:
        return self._get_random_replacement("male", msd, rng, return_lemma)
    
    def anonymize_city(self, msd: str, rng: random.Random, return_lemma = False) -> str:
        return self._get_random_replacement("city", msd, rng, return_lemma)
    
    def anonymize_municipality(self, msd: str, rng: random.Random, return_lemma = False) -> str:
        return self._get_random_replacement("municipality", msd, rng, return_lemma)
    
    def anonymize_country(self, msd: str, rng: random.Random, return_lemma = False) -> str:
        return self._get_random_replacement("country", msd, rng, return_lemma)

   #RETURNING RANDOM
    
    # --- DATA INTERNAL HELPERS ---
    def _get_cached_srlex(self):
        """
        Speed optimization: Loads the lexicon from a .pkl (Pickle) file if it exists.
        Parsing the raw TSV is slow; loading binary data is almost instantaneous.
        """
        pickle_path = SRLEX_FILTERED_PATH.with_suffix('.pkl')
        if pickle_path.exists():
            try:
                with open(pickle_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Warning: Could not load binary cache, rebuilding: {e}")

        if not SRLEX_FILTERED_PATH.exists():
            raise FileNotFoundError(f"Lex missing at {SRLEX_FILTERED_PATH}")
        
        # If cache doesn't exist, parse the TSV and create the cache for next time
        lex_dict, relaxed_dict = self._build_dictionaries()
        try:
            with open(pickle_path, 'wb') as f:
                # Protocol 5 is optimized for large data structures in modern Python
                pickle.dump((lex_dict, relaxed_dict), f, protocol=5)
        except PermissionError:
            pass # Skip caching if the directory is read-only

        return lex_dict, relaxed_dict

    def _build_dictionaries(self):
        """
        Parses the raw SRLEX TSV file. 
        Optimized with raw splits to avoid the performance penalty of DictReader 
        on files with 500k+ rows.
        """
        lex_dict = {} # Key: (lemma, msd) -> Value: wordform
        relaxed_dict = {} # Key: lemma -> Value: list of (msd, wordform) tuples
        
        with open(SRLEX_FILTERED_PATH, mode='r', encoding='utf-8') as f:
            next(f) # Skip header
            for line in f:
                parts = line.rstrip('\n').split('\t')
                if len(parts) < 3:
                    continue   
                w = parts[0] # Wordform
                l = parts[1] # Lemma
                m = parts[2] # MSD

                lex_dict[(l, m)] = w
                # Group all possible forms under a single lemma for relaxed matching
                if l in relaxed_dict:
                    relaxed_dict[l].append((m, w))
                else:
                    relaxed_dict[l] = [(m, w)]
                    
        return lex_dict, relaxed_dict