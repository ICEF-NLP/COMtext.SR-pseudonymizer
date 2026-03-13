import random
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.constants import MONTH_DICTIONARY
from comtext_sr_pseudonymizer.entities.entity_schema import Entity
from comtext_sr_pseudonymizer.patterns import (
    TEXT_DAY_DOT_MONTH_DOT_YEAR_DOT_TEXT, 
    TEXT_MONTH_SPACE_YEAR_DOT_TEXT,
    TEXT_YEAR_DOT_TEXT,
    TEXT_MONTH_TEXT,
    )

class DateAnonymizer(BaseAnonymizer):
    """
    Anonymizes dates while preserving Serbian linguistic styles.
    Supports full dates, month-year combos, years, and isolated month names.
    """
    
    def __init__(self, timestamp: str, rng: random.Random) -> None:
        super().__init__(timestamp, rng)
        # Create a reverse lookup: 'januar' -> 1, 'januara' -> 1, 'januaru' -> 1
        self.month_lookup = {}
        for month_num, names in MONTH_DICTIONARY.items():
            for name in names:
                self.month_lookup[name.lower()] = int(month_num)
    
    def _anonymize_entity(self, entity: Entity) -> str:
        """Main loop that scans text for date patterns and replaces them."""
        final_result = ""
        remaining_text = entity.original_text
        
        while True:
            # 1. Identify the first date pattern in the string
            date_values, format_meta = self._detect_date_type(remaining_text)
            
            if not date_values:
                # No more dates found
                final_result += remaining_text
                break
                
            # 2. Shift the date (e.g., move it back 2 years and 15 days)
            shifted_values = self._shift_date(date_values, entity.doc_id)
            # 3. Rebuild the string using the original punctuation and month style
            new_date_string = self._reconstruct_date(format_meta, shifted_values)
            
            # Attach prefix (text before date) and move to the suffix (text after date)
            final_result += format_meta["prefix"] + new_date_string
            remaining_text = format_meta["suffix"]

        return final_result
        
    def _detect_date_type(self, text: str) -> Tuple[Optional[Dict[str, int]], Optional[Dict[str, Any]]]:
        """Uses Regex to find date patterns and capture their metadata (separators, etc.)."""
        format_meta = {
            "prefix": "", "suffix": "",
            "day": {"val": None, "sep": ""},
            "month": {"val": None, "sep": ""},
            "year": {"val": None, "sep": ""}
        }

        # Case 1: Full Date (e.g., 01.01.2024. or 1. januar 2024.)
        match = TEXT_DAY_DOT_MONTH_DOT_YEAR_DOT_TEXT.match(text)
        if match:
            prefix, d, sep1, m, sep2, y, dot, suffix = match.groups()
            m_int = int(m) if m.isdigit() else self.month_lookup.get(m.lower(), 1)
            date_values = {"day": int(d), "month": m_int, "year": int(y)}
            format_meta.update({
                "prefix": prefix, "suffix": suffix,
                "day": {"val": d, "sep": sep1}, "month": {"val": m, "sep": sep2}, "year": {"val": y, "sep": dot}
            })
            return date_values, format_meta
        
        # Case 2: Month and Year (e.g., 'januar 2024.')
        match = TEXT_MONTH_SPACE_YEAR_DOT_TEXT.match(text)
        if match:
            prefix, m, sep2, y, dot, suffix = match.groups()
            m_int = self.month_lookup.get(m.lower(), 1)
            date_values = {"day": 1, "month": m_int, "year": int(y)}
            format_meta.update({
                "prefix": prefix, "suffix": suffix,
                "month": {"val": m, "sep": sep2}, "year": {"val": y, "sep": dot}
            })
            return date_values, format_meta
        
        # Case 3: Year Only (e.g., '2024.')
        match = TEXT_YEAR_DOT_TEXT.match(text)
        if match:
            prefix, y_val, y_dot, suffix = match.groups()
            date_values = {"day": 1, "month": 1, "year": int(y_val)}
            format_meta.update({
                "prefix": prefix, "suffix": suffix,
                "year": {"val": y_val, "sep": y_dot} 
            })
            return date_values, format_meta

        # Case 4: Isolated Month (e.g., 'u oktobru')
        match = TEXT_MONTH_TEXT.match(text)
        if match:
            prefix, mon, suffix = match.groups()
            m_int = self.month_lookup.get(mon.lower(), 1)
            date_values = {"day": 1, "month": m_int, "year": 2000} # Default year for jitter
            format_meta.update({
                "prefix": prefix, "suffix": suffix,
                "month": {"val": mon, "sep": ""}
            })
            return date_values, format_meta
        
        return None, None
    
    def _shift_date(self, date_values: Dict[str, int], doc_id:str) -> Dict[str, int]:
        """Calculates a deterministic jitter to shift the date in time."""
        seed_str = f"{doc_id}{self.timestamp}"
        self.rng.seed(seed_str)
        
        for attempt in range(2):
            year_jump = self.rng.choice([-1, 1]) * self.rng.randint(1, 5)
            day_jitter = self.rng.randint(1, 90)
            direction = self.rng.choice([-1, 1])
            
            # If first attempt results in a future date, try forced past shift
            if attempt == 1:
                year_jump = -abs(year_jump)
                
            try:
                original_dt = datetime(date_values["year"], date_values["month"], date_values["day"])
                target_year = original_dt.year + year_jump

                # Handle Leap Years: Feb 29 doesn't exist in most years
                target_day = original_dt.day
                if original_dt.month == 2 and original_dt.day == 29:
                    is_leap = (target_year % 4 == 0 and (target_year % 100 != 0 or target_year % 400 == 0))
                    if not is_leap:
                        target_day = 28
                
                # Apply Year Jump
                intermediate_dt = original_dt.replace(year=target_year, day=target_day)
                # Apply Day Jitter (handles month/year rollovers automatically)
                final_dt = intermediate_dt + timedelta(days=day_jitter * direction)
                
                # Constraint: We usually want to ensure we don't 'leak' info by shifting to the future
                if final_dt < datetime.now():
                    return {"day": final_dt.day, "month": final_dt.month, "year": final_dt.year}
            except (ValueError, OverflowError):
                continue
        return date_values

    def _reconstruct_date(self, format_meta: Dict[str, Any], shifted: Dict[str, int]) -> str:
        """Assembles the new date string while mimicking the original style."""
        # --- 1. Reconstruct Day ---
        day_part = ""
        if format_meta["day"]["val"] is not None:
            day_part = f"{shifted['day']:02d}"
            day_part += format_meta["day"]["sep"]
        
        # --- 2. Reconstruct Month (Preserving Serbian Grammar) ---
        month_part = ""
        if format_meta["month"]["val"] is not None:
            m_orig = format_meta["month"]["val"]
            if m_orig.isdigit():
                month_part = f"{shifted['month']:02d}"
            else:
                # Style Detection: Find if the original was 'oktobar', 'oktobra', or 'oktobru'
                m_int_orig = self.month_lookup.get(m_orig.lower())
                try:
                    # Look up the index of the specific declension in the constant dictionary
                    style_idx = MONTH_DICTIONARY[str(m_int_orig)].index(m_orig.lower())
                    # Apply that same index to the NEW month number
                    month_part = MONTH_DICTIONARY[str(shifted["month"])][style_idx]
                except (ValueError, IndexError, KeyError):
                    month_part = MONTH_DICTIONARY[str(shifted["month"])][0]
            month_part += format_meta["month"]["sep"]
            
        # --- 3. Reconstruct Year ---
        year_part = ""
        if format_meta["year"]["val"] is not None:
            year_part = str(shifted["year"]) + format_meta["year"]["sep"]
            
        return f"{day_part}{month_part}{year_part}"