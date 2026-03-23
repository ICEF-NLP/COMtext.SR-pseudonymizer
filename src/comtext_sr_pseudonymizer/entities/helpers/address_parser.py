import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple, Callable, Optional

from comtext_sr_pseudonymizer.constants import ROMAN_NUMBERS

__all__ = ["AddressParser", "AddressComponent"]

@dataclass
class AddressCategory:
    """
    Represents a specific semantic category within an address (e.g., STREET_LABEL).
    
    Attributes:
        name: The unique string identifier for the category.
        items: A collection of keywords/lemmas that trigger this category.
               Using a Set/Frozenset ensures O(1) lookup performance.
    """
    name: str
    items: Set[str] = field(default_factory=set)

class AddressLexicon:
    """
    Defines the semantic categories and lookup logic for address components.
    Uses a priority-based registry to pre-compute a fast keyword index.
    """
    # --- 1. KEYWORD CATEGORIES ---
    PUNCT_SEP: AddressCategory      = AddressCategory("PUNCT_SEP", {",", "–"})
    PUNCT_NUM: AddressCategory      = AddressCategory("PUNCT_NUM", {"/", "\\"})
    PUNCT_DET: AddressCategory      = AddressCategory("PUNCT_DET", {"(", ")"})
    PREPOSITION: AddressCategory    = AddressCategory("PREPOSITION", {"ispod", "iznad", "kod", "na", "u", "za"})
    STREET_LABEL: AddressCategory   = AddressCategory("STREET_LABEL", {"bul", "bulevar", "prilaz", "put", "rue", "trg", "ul", "ulica", "venac", "via"})
    NUM_LABEL: AddressCategory      = AddressCategory("NUM_LABEL", {"br", "broj", "broja"})
    APT_LABEL: AddressCategory      = AddressCategory("APT_LABEL", {"st", "stan", "objekat"})
    FLOOR_LABEL: AddressCategory    = AddressCategory("FLOOR_LABEL", {"spr", "sprat"})
    MUNI_LABEL: AddressCategory     = AddressCategory("MUNI_LABEL", {"opstina", "opština"})
    COUNTRY_LABEL: AddressCategory  = AddressCategory("COUNTRY_LABEL", {"drzava", "država", "federacija", "republika"})
    DETAIL_LABEL: AddressCategory   = AddressCategory("DETAIL_LABEL", {"nivo", "podrum", "potkrovlje", "stambeni", "suteren"})
    AREA_LABEL: AddressCategory     = AddressCategory("AREA_LABEL", {"kvm", "površina", "povrsina"})
    CITY_LABEL: AddressCategory     = AddressCategory("CITY_LABEL", {"grad", "mesto", "naselje"})
    CONNECTING_REL: AddressCategory = AddressCategory("CONNECTING_REL", {"odnosno", "i", "to"})
    HOUSE_LABEL: AddressCategory    = AddressCategory("HOUSE_LABEL", {"kuća", "kuca", "kućni", "kucni", "ulaz", "zgrada"})
    SECTION_LABEL: AddressCategory  = AddressCategory("SECTION_LABEL", {"lamela"})

    # --- 2. VIRTUAL ROLES (Strings) ---
    UNKNOWN: AddressCategory        = AddressCategory("UNKNOWN")
    NUM_VAL: AddressCategory        = AddressCategory("NUM_VAL")
    STREET_VAL: AddressCategory     = AddressCategory("STREET_VAL")
    HOUSE_NUMBER: AddressCategory   = AddressCategory("HOUSE_NUMBER")
    APT_NUMBER: AddressCategory     = AddressCategory("APT_NUMBER")
    FLOOR_NUMBER: AddressCategory   = AddressCategory("FLOOR_NUMBER")
    SECTION_NUMBER: AddressCategory = AddressCategory("SECTION_NUMBER")
    AREA_NUMBER: AddressCategory    = AddressCategory("AREA_NUMBER")
    ZIP_NUMBER: AddressCategory     = AddressCategory("ZIP_NUMBER")
    CITY_VAL: AddressCategory       = AddressCategory("CITY_VAL")
    MUNI_VAL: AddressCategory       = AddressCategory("MUNI_VAL")
    COUNTRY_VAL: AddressCategory    = AddressCategory("COUNTRY_VAL")

    # --- 3. THE REGISTRY (Priority List) ---
    TAGGING_PRIORITY: List[AddressCategory] = [
        PUNCT_SEP, PUNCT_NUM, PUNCT_DET, PREPOSITION,
        STREET_LABEL, NUM_LABEL, APT_LABEL, FLOOR_LABEL,
        MUNI_LABEL, COUNTRY_LABEL, DETAIL_LABEL, AREA_LABEL,
        CITY_LABEL, CONNECTING_REL, HOUSE_LABEL, SECTION_LABEL
    ]

    # --- 4. THE SPEED BOOST (Fast Index) ---
    _FAST_MAP: Dict[str, str] = {}

    @classmethod
    def initialize(cls) -> None:
        """Pre-computes the keyword map for high-speed lookup."""
        if cls._FAST_MAP:
            return
        for cat in cls.TAGGING_PRIORITY:
            if not cat.items:
                continue
            for item in cat.items:
                if item not in cls._FAST_MAP:
                    cls._FAST_MAP[item] = cat.name

    @classmethod
    def get_role(cls, lemma: str) -> str:
        """
        The primary lookup method for the Parser. 
        Normalizes the input lemma and checks the pre-computed index.
        """
        clean = lemma.strip().lower().rstrip(".")
        return cls._FAST_MAP.get(clean, cls.UNKNOWN.name)
        
@dataclass
class AddressComponent:
    """
    An atomic unit of an address, holding both raw text and linguistic metadata.
    """
    start_token: int
    label: str
    token: str
    lemma: str
    msd: str
    
    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "AddressComponent":
        """
        Constructor that safely builds a component from a dictionary/DataFrame row.
        
        Args:
            row: A dictionary containing 'token', 'lemma', and 'msd' keys.
            
        Returns:
            An AddressComponent instance with an empty initial label.
        """
        return cls(
            start_token = int(row.get("token_id", 0)),
            label="",
            token=str(row.get("token", "")),
            lemma=str(row.get("lemma", "")),
            msd=str(row.get("msd", ""))
        )

class AddressParser:
    """
    Orchestrates the conversion of raw NLP tokens into labeled address components.
    Uses a multi-stage refinement pipeline to resolve semantic ambiguity.
    """

    def __init__(self, data_manager: Any, debug: bool = False) -> None:
        """
        Initializes the parser with necessary data lookups and optional debugging.
        
        Args:
            data_manager: Object providing geographic validation (cities, countries, etc.).
            debug: If True, writes detailed stage-by-stage transitions to a log file.
        """
        self.data_manager: Any = data_manager
        self.adr_lex: type[AddressLexicon] = AddressLexicon
        self.adr_lex.initialize()
        
        self.debug: bool = debug
        if self.debug:
            timestamp: str = datetime.datetime.now().strftime("%H_%M_%S")
            self.debug_file: str = f"debug_log_{timestamp}.txt"
            
            with open(self.debug_file, "w", encoding="utf-8") as f:
                f.write(f"ADDRESS PARSER DEBUG SESSION - {timestamp}\n")

    def get_label_for(self, category: str) -> str:
        """
        Public API to map abstract categories to internal lexicon label names.
        
        Args:
            category: High-level category name (e.g., 'CITY', 'STREET').
            
        Returns:
            The internal string name of the AddressCategory.
        """
        category = category.upper()
        mapping: Dict[str, str] = {
            "APARTMENT":      self.adr_lex.APT_NUMBER.name,
            "AREA":           self.adr_lex.AREA_NUMBER.name,
            "CITY":           self.adr_lex.CITY_VAL.name,
            "COUNTRY":        self.adr_lex.COUNTRY_VAL.name,
            "FLOOR":          self.adr_lex.FLOOR_NUMBER.name,
            "HOUSE":          self.adr_lex.HOUSE_NUMBER.name,
            "MUNI":           self.adr_lex.MUNI_VAL.name,
            "SECTION":        self.adr_lex.SECTION_NUMBER.name,
            "STREET":         self.adr_lex.STREET_VAL.name,
            "ZIP":            self.adr_lex.ZIP_NUMBER.name,
        }
        return mapping.get(category, "UNKNOWN")

    def _log_stage(self, stage_name: str, components: List[AddressComponent]) -> None:
        """
        Appends a formatted table of the current state to the debug file.
        Useful for tracking how labels evolve across stages.
        """
        if not self.debug:
            return 
            
        with open(self.debug_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f" STAGE: {stage_name}\n")
            f.write(f"{'='*80}\n")
            
            header = f"{'IDX':<5} | {'TOKEN':<15} | {'LEMMA':<15} | {'MSD':<15} | {'LABEL':<25}\n"
            f.write(header)
            f.write("-" * len(header) + "\n")
            
            for i, c in enumerate(components):
                # Truncate for table alignment
                t = (c.token[:12] + '..') if len(c.token) > 14 else c.token
                lem = (c.lemma[:12] + '..') if len(c.lemma) > 14 else c.lemma
                m = (c.msd[:12] + '..') if len(c.msd) > 14 else c.msd
                
                row = f"{i:<5} | {t:<15} | {lem:<15} | {m:<15} | {c.label:<25}\n"
                f.write(row)
                
            f.write(f"{'='*80}\n\n")

    def parse(self, entity_rows: List[Dict[str, Any]]) -> List[AddressComponent]:
        """
        The main entry point for address parsing. 
        Runs components through the refinement pipeline until fully resolved or finished.
        """
        components: List[AddressComponent] = [AddressComponent.from_row(row) for row in entity_rows]
        
        if self.debug:
            self._log_stage("01_Hydration", components)

        # The Processing Pipeline
        stages: List[Tuple[Callable, str]] = [
            (self._initial_tagging, "02_Initial_tagging"),
            (self._refine_numeric_context, "03_Refinement_numeric_context"),
            (self._resolve_remaining_identities, "04_Resolution_for_one_remaining"),
            (self._resolve_delimited_unknown_labels, "05_Unknown_resolution"),
            (self._resolve_geographic_islands, "06_Geographic_lookup_resolution"),
            (self._apply_final_strategies, "07_Clean_up_and_heuristics")
        ]

        for func, stage_name in stages:
            components = func(components)
            
            if self.debug:
                self._log_stage(stage_name, components)
            
            # If every token has a definitive label, we can skip remaining heuristics
            if self._is_fully_resolved(components):
                break

        return self._group_address_parts(components)
    
    def _is_fully_resolved(self, components: List[AddressComponent]) -> bool:
        """
        An address is only 'Fully Resolved' if:
        3. There are NO generic 'UNKNOWN' or 'NUM_VAL' tags left.
        """
        placeholder_set = {self.adr_lex.UNKNOWN.name, self.adr_lex.NUM_VAL.name, self.adr_lex.COUNTRY_LABEL.name,
                           self.adr_lex.MUNI_LABEL.name, self.adr_lex.STREET_LABEL.name}
        has_placeholders = any(c.label in placeholder_set for c in components)
        return not has_placeholders

    def _initial_tagging(self, components: List[AddressComponent]) -> List[AddressComponent]:
        """
        Stage 1: Atomic Identity. 
        Assigns initial labels based on the lexicon, regex patterns, and linguistic rules.
        """
        tagged: List[AddressComponent] = []
    
        for comp in components:
            lemma_low: str = comp.lemma.lower()

            # 1. THE SPLINTER: Handle hyphenated identifiers (e.g., "lamela-A" -> "lamela" + "A")
            # This is specific to Serbian residential complexes where labels and IDs are joined.
            if "-" in comp.token and lemma_low.startswith("lamel"):
                parts: List[str] = comp.token.split("-", 1)
                
                # Part 1: The Category Label (e.g., "lamela")
                tagged.append(AddressComponent(
                    start_token= comp.start_token,
                    label=self.adr_lex.SECTION_LABEL.name,
                    token=parts[0],
                    lemma="lamela",
                    msd=comp.msd
                ))
                # Part 2: The Specific Identifier (e.g., "A")
                tagged.append(AddressComponent(
                    start_token= comp.start_token+1,
                    label=self.adr_lex.SECTION_NUMBER.name,
                    token=parts[1],
                    lemma=parts[1].lower(),
                    msd=comp.msd
                ))
                continue

            # 2. LEXICON LOOKUP: Check if the lemma exists in pre-defined keyword categories
            role: str = self.adr_lex.get_role(comp.lemma)

            # 3. UNKNOWN RESOLUTION: Use heuristics for tokens not found in the lexicon
            if role == self.adr_lex.UNKNOWN.name:
                # A. ZIP Code (Standard 5-digit format for Serbia)
                if comp.token.isdigit() and len(comp.token) == 5:
                    role = self.adr_lex.ZIP_NUMBER.name
                
                # B. Generic Numeric Values (House numbers, apt numbers, etc.)
                elif (
                    any(c.isdigit() for c in comp.token) or          # Contains digits (12, 12a)
                    comp.token.upper() in ROMAN_NUMBERS or          # Roman numerals (IV, IX)
                    lemma_low == "bb" or                            # "bez broja" (no number)
                    (comp.msd.startswith('M') and comp.token[0].islower()) or  # MSD 'M' + lowercase
                    len(comp.lemma) == 1                            # Single characters (A, B)
                ):
                    # We use a placeholder; specific type is resolved in Stage 2/3
                    role = self.adr_lex.NUM_VAL.name

            # 4. SPECIAL EXCEPTION: Disambiguate the word 'I' (and) vs 'I' (Roman 1)
            # If 'I' has a numeric MSD, treat it as a number rather than a connecting relation.
            if (role == self.adr_lex.CONNECTING_REL.name and 
                comp.token.lower() == 'i' and 
                comp.msd.startswith('M')):
                role = self.adr_lex.NUM_VAL.name

            # Assign the determined role and update the list
            comp.label = role
            tagged.append(comp)
        return tagged

    def _refine_numeric_context(self, components: List[AddressComponent]) -> List[AddressComponent]:
        """
        Stage 2: Contextual Refinement.
        Reclassifies generic NUM_VAL labels into specific types (HOUSE_NUMBER, APT_NUMBER, etc.)
        based on nearby keywords or structural markers like slashes.
        """
        # Mapping of Label keywords to their corresponding Value roles
        SURE_LABELS: Dict[str, str] = {
            self.adr_lex.HOUSE_LABEL.name:   self.adr_lex.HOUSE_NUMBER.name,
            self.adr_lex.APT_LABEL.name:     self.adr_lex.APT_NUMBER.name,
            self.adr_lex.FLOOR_LABEL.name:   self.adr_lex.FLOOR_NUMBER.name,
            self.adr_lex.SECTION_LABEL.name: self.adr_lex.SECTION_NUMBER.name,
            self.adr_lex.AREA_LABEL.name:    self.adr_lex.AREA_NUMBER.name
        }

        refined: List[AddressComponent] = []
        
        for i in range(len(components)):
            current: AddressComponent = components[i]

            # 1. THE SLASH MERGER: Combines split numbers (e.g., "12", "/", "A" -> "12/A")
            # Logic: If current is a number/char and the previous was a slash separator.
            if (current.label == self.adr_lex.NUM_VAL.name or len(current.token) == 1) and refined:
                if refined[-1].msd.upper().startswith('Z') and "/" in refined[-1].token:
                    sep: AddressComponent = refined.pop()
                    # Ensure there is a preceding number to attach to
                    if refined and (refined[-1].label == self.adr_lex.NUM_VAL.name or 
                                    refined[-1].label.endswith("_NUMBER")):
                        old_num: AddressComponent = refined.pop()
                        current.token = f"{old_num.token}/{current.token}"
                        current.lemma = f"{old_num.lemma}/{current.lemma}"
                    else:
                        # If no preceding number, put the slash back
                        refined.append(sep)

            # 2. CONSERVATIVE INHERITANCE: Reclassify numbers based on adjacent labels
            if current.label == self.adr_lex.NUM_VAL.name:
                if refined:
                    prev: AddressComponent = refined[-1]
                    
                    # Case A: "stan 12" (Direct neighbor)
                    if prev.label in SURE_LABELS:
                        current.label = SURE_LABELS[prev.label]
                    
                    # Case B: "stan broj 12" (Bridge: skip the generic 'broj' label)
                    elif prev.label == self.adr_lex.NUM_LABEL.name:
                        if len(refined) >= 2:
                            grand: AddressComponent = refined[-2]
                            if grand.label in SURE_LABELS:
                                current.label = SURE_LABELS[grand.label]
            
            # 3. BACKWARD REFINEMENT: Handle "12 stan" (Post-fixed labels)
            elif current.label in SURE_LABELS:
                if refined and refined[-1].label == self.adr_lex.NUM_VAL.name:
                    refined[-1].label = SURE_LABELS[current.label]

            refined.append(current)

        return refined
    
    def _resolve_remaining_identities(self, components: List[AddressComponent]) -> List[AddressComponent]:
        """
        Stage 3: Logical Elevation. 
        If exactly one cluster of UNKNOWN tokens remains, it is likely the Street name.
        If exactly one generic NUM_VAL remains, it is likely the House Number.
        """
        # Quick Check: If both are already found, skip this stage
        has_house_num: bool = any(c.label == self.adr_lex.HOUSE_NUMBER.name for c in components)
        has_street_val: bool = any(c.label == self.adr_lex.STREET_VAL.name for c in components)
        
        if has_house_num and has_street_val:
            return components
        
        unknown_groups: int = 0
        number_groups: int = 0
        
        # 1. COUNT CLUSTERS: Identify how many distinct "islands" of generic data we have
        for i in range(len(components)):
            current_label: str = components[i].label
            prev_label: Optional[str] = components[i-1].label if i > 0 else None
            
            # Count a group only at the start of a sequence to avoid overcounting multi-token names
            if current_label == self.adr_lex.UNKNOWN.name and prev_label != self.adr_lex.UNKNOWN.name:
                unknown_groups += 1
            if current_label == self.adr_lex.NUM_VAL.name and prev_label != self.adr_lex.NUM_VAL.name:
                number_groups += 1

        # Ambiguity Guard: If there are multiple candidates for either, do nothing (wait for Stage 4/5)
        if unknown_groups > 1 and number_groups > 1:
            return components
        
        # 2. APPLY ELEVATION: Force assign the labels if the "Exactly One" rule is met
        for comp in components:
            # If we don't have a street yet, and there's only one unknown group, claim it
            if not has_street_val and unknown_groups == 1:
                if comp.label in [self.adr_lex.UNKNOWN.name, self.adr_lex.STREET_LABEL.name]:
                    comp.label = self.adr_lex.STREET_VAL.name
            
            # If we don't have a house number yet, and there's only one number group, claim it
            if not has_house_num and number_groups == 1:
                if comp.label == self.adr_lex.NUM_VAL.name:
                    comp.label = self.adr_lex.HOUSE_NUMBER.name

        return components
    
    def _resolve_delimited_unknown_labels(self, components: List[AddressComponent]) -> List[AddressComponent]:
        """
        Stage 4: Label Expansion.
        Propagates category labels to adjacent UNKNOWN tokens. 
        Handles both prefix (Grad Beograd) and postfix (Kralja Petra ulica) patterns.
        """
        # Optimization: If no punctuation/separators exist, expansion might be too aggressive
        if not any(c.label == self.adr_lex.PUNCT_SEP.name for c in components):
            return components
        
        n: int = len(components)
        label_map: Dict[str, str] = {
            self.adr_lex.MUNI_LABEL.name:    self.adr_lex.MUNI_VAL.name,
            self.adr_lex.CITY_LABEL.name:    self.adr_lex.CITY_VAL.name,
            self.adr_lex.COUNTRY_LABEL.name: self.adr_lex.COUNTRY_VAL.name
        }

        # 1. FORWARD EXPANSION: For City, Municipality, and Country (usually prefix-based)
        # e.g., "Grad [UNKNOWN] [UNKNOWN]" -> "Grad [CITY_VAL] [CITY_VAL]"
        for i in range(n):
            curr_label: str = components[i].label
            if curr_label in label_map:
                target_label: str = label_map[curr_label]
                components[i].label = target_label  # Convert the label itself to a value
                
                for j in range(i + 1, n):
                    if components[j].label == self.adr_lex.UNKNOWN.name:
                        components[j].label = target_label
                    else:
                        # Stop expansion as soon as we hit a different known role or separator
                        break

        # 2. BIDIRECTIONAL EXPANSION: Specifically for Streets
        # Serbian addresses often use both "Ulica [Name]" and "[Name] ulica"
        for i in range(n):
            if components[i].label == self.adr_lex.STREET_LABEL.name:
                components[i].label = self.adr_lex.STREET_VAL.name
                
                # A. Forward Expansion: e.g., "Ulica Kralja Petra"
                # Includes safety for prepositions at the start (e.g., "Ulica na vodi")
                eaten_unknowns: int = 0
                eaten_prepositions: int = 0
                for j in range(i + 1, n):
                    comp: AddressComponent = components[j]
                    if comp.label == self.adr_lex.UNKNOWN.name:
                        comp.label = self.adr_lex.STREET_VAL.name
                        eaten_unknowns += 1
                    elif comp.label == self.adr_lex.PREPOSITION.name:
                        # Only absorb a preposition if it's the very first thing after the label
                        if eaten_unknowns == 0 and eaten_prepositions == 0:
                            comp.label = self.adr_lex.STREET_VAL.name
                            eaten_prepositions += 1
                        else:
                            break
                    elif comp.label == self.adr_lex.STREET_LABEL.name:
                        comp.label = self.adr_lex.STREET_VAL.name
                    else:
                        break
                
                # B. Backward Expansion: e.g., "Kralja Petra ulica"
                for j in range(i - 1, -1, -1):
                    comp: AddressComponent = components[j]
                    if comp.label in [self.adr_lex.UNKNOWN.name, self.adr_lex.STREET_LABEL.name]:
                        comp.label = self.adr_lex.STREET_VAL.name
                    else:
                        break
        return components
    
    def _resolve_geographic_islands(self, components: List[AddressComponent]) -> List[AddressComponent]:
        """
        Stage 5: Geographic Validation.
        Groups clusters of UNKNOWN tokens and identifies them by querying the data_manager.
        Resolves identities like City, Municipality, or Country based on availability.
        """
        # 1. IDENTIFY CANDIDATES: Group contiguous UNKNOWN tokens into 'islands'
        islands: List[Dict[str, Any]] = []
        i: int = 0
        while i < len(components):
            if components[i].label == self.adr_lex.UNKNOWN.name:
                start_idx: int = i
                group_lemmas: List[str] = []
                group_word = List[str] = []
                while i < len(components) and components[i].label == self.adr_lex.UNKNOWN.name:
                    group_lemmas.append(components[i].lemma.lower())
                    group_word.append(components[i].token.lower())
                    i += 1
                
                candidate_str: str = " ".join(group_lemmas).strip()
                candidate_str_word: str = " ".join(group_word).strip()
                
                # Default fallback is always STREET_VAL (most likely for unknown text)
                possible_roles: List[str] = [self.adr_lex.STREET_VAL.name]
                
                # Check against data_manager for specific geographic identities
                if self.data_manager.is_city(candidate_str) or self.data_manager.is_city(candidate_str_word):
                    possible_roles.append(self.adr_lex.CITY_VAL.name)
                if self.data_manager.is_municipality(candidate_str) or self.data_manager.is_municipality(candidate_str_word):
                    possible_roles.append(self.adr_lex.MUNI_VAL.name)
                if self.data_manager.is_country(candidate_str) or self.data_manager.is_country(candidate_str_word):
                    possible_roles.append(self.adr_lex.COUNTRY_VAL.name)
                
                islands.append({
                    "indices": list(range(start_idx, i)),
                    "text": candidate_str,
                    "roles": possible_roles
                })
            else:
                i += 1

        if not islands:
            return components

        # 2. RESOLVE ROLES: Priority-based assignment
        # Track which roles are already filled in the address to avoid duplicates (e.g., two cities)
        assigned_roles: Set[str] = {c.label for c in components if c.label != self.adr_lex.UNKNOWN.name}
        
        priority_order: List[str] = [
            self.adr_lex.STREET_VAL.name, 
            self.adr_lex.CITY_VAL.name, 
            self.adr_lex.MUNI_VAL.name, 
            self.adr_lex.COUNTRY_VAL.name
        ]

        # Sort islands by specificity: candidates with fewer matches are handled first
        islands.sort(key=lambda x: len(x["roles"]))

        # Pass 1: Greedily assign missing roles based on data_manager matches
        for role in priority_order:
            if role in assigned_roles:
                continue
            for idx, island in enumerate(islands):
                if role in island["roles"]:
                    for component_idx in island["indices"]:
                        components[component_idx].label = role
                    assigned_roles.add(role)
                    # Safe mutation: we pop and immediately break to restart enumerate()
                    islands.pop(idx)
                    break

        # Pass 2: Fallback for leftovers (Ensures no island remains UNKNOWN)
        for island in islands:
            for role in priority_order:
                if role not in assigned_roles:
                    for component_idx in island["indices"]:
                        components[component_idx].label = role
                    assigned_roles.add(role)
                    break

        return components
    
    def _apply_final_strategies(self, components: List[AddressComponent]) -> List[AddressComponent]:
        """
        Stage 6: Final Cleanup and Heuristics.
        Resolves any lingering NUM_VALs based on proximity to Street markers
        and converts remaining Category Labels into Value roles.
        """
        n: int = len(components)

        # 1. PROXIMITY-BASED RESOLUTION: Identify House Numbers by context
        # If a number follows a street name or "ulica", it is almost certainly the house number.
        for i in range(n):
            if components[i].label == self.adr_lex.NUM_VAL.name:
                prev_label: Optional[str] = components[i-1].label if i > 0 else None
                
                # Case A: Direct neighbor ("Kralja Petra 12" or "Ulica 12")
                if prev_label in [self.adr_lex.STREET_VAL.name, self.adr_lex.STREET_LABEL.name]:
                    components[i].label = self.adr_lex.HOUSE_NUMBER.name
                
                # Case B: Bridge inheritance ("Kralja Petra br. 12")
                # Skip the generic 'NUM_LABEL' (br.) to find the street context behind it.
                elif prev_label == self.adr_lex.NUM_LABEL.name and i > 1:
                    pre_prev_label: str = components[i-2].label
                    if pre_prev_label in [self.adr_lex.STREET_VAL.name, self.adr_lex.STREET_LABEL.name]:
                        components[i].label = self.adr_lex.HOUSE_NUMBER.name

        # 2. FINAL MAPPING: Convert all remaining 'LABEL' categories into their 'VAL' equivalents
        # This ensures that even "naked" keywords are treated as parts of the specific address unit.
        for i in range(n):
            lbl: str = components[i].label
            
            # Convert structural keywords (ulica, država, opština) into data values
            if lbl == self.adr_lex.STREET_LABEL.name:
                components[i].label = self.adr_lex.STREET_VAL.name
                
            elif lbl == self.adr_lex.COUNTRY_LABEL.name:
                components[i].label = self.adr_lex.COUNTRY_VAL.name
                
            # SURVIVORSHIP RULE:
            # If a NUM_VAL survived all previous logic, it is likely an Apartment or Office number.
            # We default it to APT_NUMBER as the most statistically probable role for a "trailing" number.
            elif lbl == self.adr_lex.NUM_VAL.name:
                components[i].label = self.adr_lex.APT_NUMBER.name

        return components

    def _group_address_parts(self, components: List[AddressComponent]) -> List[AddressComponent]:
        """
        Final Stage: Structural Consolidation.
        Merges contiguous components with identical labels into a single 
        AddressComponent (e.g., 'Kralja' + 'Petra' -> 'Kralja Petra').
        """
        if not components:
            return []
            
        grouped: List[AddressComponent] = []

        for comp in components:
            # 1. NEW GROUP: If the list is empty or the label changes, start a new unit
            if not grouped or grouped[-1].label != comp.label:
                # We instantiate a new object to avoid side-effects on the original stream
                grouped.append(AddressComponent(
                    start_token= comp.start_token,
                    token=comp.token,
                    lemma=comp.lemma,
                    msd=comp.msd,
                    label=comp.label
                ))
            
            # 2. APPEND: If the label matches the previous one, merge the tokens
            else:
                last: AddressComponent = grouped[-1]
                last.token += f" {comp.token}"
                last.lemma += f" {comp.lemma}"
                
                # METADATA CARRY-OVER:
                # If the current token is a Proper Noun (Np) but the group isn't yet 
                # marked as one, elevate the group's MSD. This ensures 'Kralja Petra' 
                # retains its 'Np' status even if 'Kralja' was just a common noun.
                if not last.msd.startswith("Np") and comp.msd.startswith("Np"):
                    last.msd = comp.msd
                    
        return grouped