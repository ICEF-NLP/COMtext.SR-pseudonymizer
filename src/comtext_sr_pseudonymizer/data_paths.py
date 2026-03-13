from importlib import resources

# This points to the 'data' directory inside your installed package
# Change "anonymizer" to match the name of your package folder
DATA_ROOT = resources.files("comtext_sr_pseudonymizer").joinpath("data")

# --- BASE DIRECTORIES ---
# Organized by function: 'lookup' for identifying, 'replacement' for pseudonymizing
LOOKUP_DIR = DATA_ROOT.joinpath("lookup")
REPLACEMENT_DIR = DATA_ROOT.joinpath("replacement")

# --- GENERAL PATHS ---
# Main morphological dictionary used for Serbian case-matching.
SRLEX_FILTERED_PATH = DATA_ROOT.joinpath("srlex_filtered.tsv")

# --- LOOKUP DATA ---
# Simple text files used for existence checks (e.g., is this a known city?).
LOOKUP_CITY_PATH = LOOKUP_DIR.joinpath("city_lookup.txt")
LOOKUP_MUNICIPALITY_PATH = LOOKUP_DIR.joinpath("municipality_lookup.txt")
LOOKUP_COUNTRY_PATH = LOOKUP_DIR.joinpath("country_lookup.txt")
LOOKUP_FEMALE_NAME_PATH = LOOKUP_DIR.joinpath("per_female_lookup.txt")
LOOKUP_MALE_NAME_PATH = LOOKUP_DIR.joinpath("per_male_lookup.txt")
LOOKUP_SURNAME_PATH = LOOKUP_DIR.joinpath("per_surname_lookup.txt")

# --- REPLACEMENT DATA ---
# TSV/CSV files used to pull random synthetic values.
POOL_TOP_CITY_PATH = REPLACEMENT_DIR.joinpath("top_city_pool.tsv")
POOL_TOP_MUNICIPALITY_PATH = REPLACEMENT_DIR.joinpath("top_municipality_pool.tsv")
POOL_ADR_STREET_PATH = REPLACEMENT_DIR.joinpath("adr_street_pool.tsv")
POOL_ADR_ZIP_PATH = REPLACEMENT_DIR.joinpath("adr_zip_pool.tsv")
POOL_FEMALE_NAME_PATH = REPLACEMENT_DIR.joinpath("per_female_pool.tsv")
POOL_MALE_NAME_PATH = REPLACEMENT_DIR.joinpath("per_male_pool.tsv")
POOL_SURNAME_PATH = REPLACEMENT_DIR.joinpath("per_surname_pool.tsv")
POOL_COM_PATH = REPLACEMENT_DIR.joinpath("com_company_pool.tsv")
POOL_NGO_PATH = REPLACEMENT_DIR.joinpath("orgoth_ngo_pool.tsv")
POOL_IDCOM_COM_PATH = REPLACEMENT_DIR.joinpath("idcom_company_pool.tsv")
POOL_IDCOM_NGO_PATH = REPLACEMENT_DIR.joinpath("idcom_ngo_pool.tsv")

def read_file(file_resource, lower=False, set_output=False):
    """
    Utility to load resource files. 
    Supports returning a 'set' for O(1) lookups or a 'list' for random selection.
    """
    with file_resource.open("r", encoding="utf-8") as f:
        lines = (line.strip() for line in f if line.strip())
        if lower:
            lines = (line.lower() for line in lines)
            
        return set(lines) if set_output else list(lines)