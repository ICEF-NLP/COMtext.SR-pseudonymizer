ROMAN_NUMBERS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

SERBIAN_ALPHABET = "ABCČĆDĐEFGHIJKLMNOPRSŠTUVZŽ"

SERBIAN_PHONE_OPERATORS = {
    "mobile":{
        "064": "mts",
        "065": "mts",
        "066": "mts",
        "062": "Yettel",
        "063": "Yettel",
        "069": "Yettel",
        "060": "A1 Srbija",
        "061": "A1 Srbija",
        "068": "A1 Srbija",
        "0677": "Globaltel",
        "0678": "Globaltel",
    },
    "landline":
    {
        "010": "Pirot",
        "011": "Beograd",
        "012": "Požarevac",
        "013": "Pančevo",
        "014": "Valjevo",
        "015": "Šabac",
        "016": "Leskovac",
        "017": "Vranje",
        "018": "Niš",
        "019": "Zaječar",
        "020": "Novi Pazar",
        "021": "Novi Sad",
        "022": "Sremska Mitrovica",
        "023": "Zrenjanin",
        "0230": "Kikinda",
        "024": "Subotica",
        "025": "Sombor",
        "026": "Smederevo",
        "027": "Prokuplje",
        "028": "Kosovska Mitrovica",
        "0280": "Gnjilane",
        "029": "Prizren",
        "0290": "Uroševac",
        "030": "Bor",
        "031": "Užice",
        "032": "Čačak",
        "033": "Prijepolje",
        "034": "Kragujevac",
        "035": "Jagodina",
        "036": "Kraljevo",
        "037": "Kruševac",
        "038": "Priština",
        "039": "Peć",
        "0390": "Đakovica"
    }
}

NON_SERBIAN_CITIES = [
    "Amsterdam", "Ankara", "Atina", "Bagdad", "Baku", "Bangkok", 
    "Barselona", "Bazel", "Beč", "Berlin", "Bern", "Bratislava", 
    "Brisel", "Budimpešta", "Buenos Ajres", "Bukurešt", "Cirih", 
    "Čikago", "Dablin", "Damas", "Doha", "Dubai", "Firenca","Frankfurt", 
    "Hamburg", "Hag", "Helsinki", "Hong Kong", "Istanbul", "Jakurta", 
    "Jerusalim", "Johanesburg", "Kairo", "Kopenhagen", "Kuala Lumpur", 
    "Kuvajt Siti", "Kijev", "Larnaka", "Lion", "Lisabon", "London", 
    "Los Anđeles", "Madrid", "Manila", "Marsej", "Meksiko Siti", 
    "Milano", "Minhen", "Moskva", "Najrobi", "Napulj", "Nica", 
    "Njujork", "Nju Delhi", "Oslo", "Pariz", "Peking", "Podgorica", "Prag", 
    "Rejkjavik", "Riga", "Rim", "Rijad", "Sao Paolo", "Sarajevo", 
    "Seul", "Sidnej", "Singapur", "Sofija", "Solun", "Stokholm", 
    "Strazbur", "Šangaj", "Talin", "Taškent", "Tbilis", "Teheran", 
    "Tel Aviv", "Tirana", "Tokio", "Toronto", "Tripoli", "Tunis", 
    "Varšava", "Vatikan", "Venecija", "Viljnus", "Vašington", 
    "Velington", "Ženeva"
]

COUNTRIES = [
    "Albanija", "Australija", "Austrija", "Belgija", "BiH", 
    "Bosna i Hercegovina", "Brazil", "Bugarska", "Belgija", 
    "Crna Gora", "Češka", "Češka Republika", "Danska", "Egipat", 
    "Federacija BiH", "Finska", "Francuska", "Francuska Republika", 
    "Grčka", "Helenska Republika", "Holandija", "Hrvatska", "Indija", 
    "Irska", "Italija", "Italijanska Republika", "Japan", "Kanada", 
    "Kina", "Kraljevina Belgija", "Kraljevina Holandija", "Kraljevina Španija", 
    "Mađarska", "Meksiko", "Narodna Republika Kina", "Nemačka", "Nizozemska", "Norveška", 
    "Poljska", "Republika Austrija", "Republika Hrvatska", "Republika Poljska", 
    "Republika Slovenija", "Republika Srbija", "Republika Srpska", "Republika Turska", 
    "Rumunija", "Rusija", "Ruska Federacija", "SAD", "Savezna Republika Nemačka", 
    "Severna Makedonija", "Sjedinjene Američke Države", "Slovačka", "Slovenija", 
    "Srbija", "Španija", "Švedska", "Švajcarska", "Švajcarska Konfederacija", 
    "Turska", "Ujedinjeno Kraljevstvo", "Ukrajina", "Velika Britanija"
]

EMAIL_ENDINGS = [
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "icloud.com"
]

MONTH_DICTIONARY = {
    "1": ["januar", "januara", "jan.", "januarom", "januaru"],
    "2": ["februar", "februara", "feb.", "februarom", "februaru"],
    "3": ["mart", "marta", "mar.", "martom", "martu"],
    "4": ["april", "aprila", "apr.", "aprilom", "aprilu"],
    "5": ["maj", "maja", "maj.", "majom", "maju"],
    "6": ["jun", "juna", "jun.", "junom", "junu"],
    "7": ["jul", "jula", "jul.", "julom", "julu"],
    "8": ["avgust", "avgusta", "avg.", "avgustom", "avgustu"],
    "9": ["septembar", "septembra", "sept.", "septembrom", "septembru"],
    "10": ["oktobar", "oktobra", "okt.", "oktobrom", "oktobru"],
    "11": ["novembar", "novembra", "nov.", "novembrom", "novembru"],
    "12": ["decembar", "decembra", "dec.", "decembrom", "decembru"]
}


IDPER_REGION_DICTIONARY = {
    # 00–09: Foreigners
    "01": ["Stranci u Bosni i Hercegovini"],
    "02": ["Stranci u Crnoj Gori"],
    "03": ["Stranci u Hrvatskoj"],
    "04": ["Stranci u Makedoniji"],
    "05": ["Stranci u Sloveniji"],
    "07": ["Stranci u Srbiji (bez pokrajina)"],
    "08": ["Stranci u Vojvodini"],
    "09": ["Stranci na Kosovu i Metohiji"],

    # 10–19: Bosnia and Herzegovina
    "10": ["Banja Luka"],
    "11": ["Bihac"],
    "12": ["Doboj"],
    "13": ["Gorazde"],
    "14": ["Livno"],
    "15": ["Mostar"],
    "16": ["Prijedor"],
    "17": ["Sarajevo"],
    "18": ["Tuzla"],
    "19": ["Zenica"],

    # 20–29: Montenegro
    "21": ["Podgorica"],
    "26": ["Niksic"],
    "29": ["Pljevlja"],

    # 30–39: Croatia
    "30": ["Osijek", "Slavonija region"],
    "31": ["Bjelovar", "Virovitica", "Koprivnica", "Pakrac", "Podravina region"],
    "32": ["Varazdin", "Medjimurje region"],
    "33": ["Zagreb"],
    "34": ["Karlovac"],
    "35": ["Gospic", "Lika region"],
    "36": ["Rijeka", "Pula", "Istra", "Primorje region"],
    "37": ["Sisak", "Banovina region"],
    "38": ["Split", "Zadar", "Dubrovnik", "Dalmacija region"],
    "39": ["Ostalo"],

    # 41–49: North Macedonia
    "41": ["Bitolj"],
    "42": ["Kumanovo"],
    "43": ["Ohrid"],
    "44": ["Prilep"],
    "45": ["Skoplje"],
    "46": ["Strumica"],
    "47": ["Tetovo"],
    "48": ["Veles"],
    "49": ["Stip"],

    # 50–59: Slovenia
    "50": ["Slovenija"],

    #70-80 Serbia central
    "71": ["Beograd"],
    "72": ["Arandjelovac", "Batocina", "Despotovac", "Jagodina", "Knic", "Kragujevac", "Lapovo", "Paracin", "Raca", "Rekovac", "Svilajnac", "Topola", "Cuprija"],
    "73": ["Aleksinac", "Babusnica", "Bela Palanka", "Blace", "Dimitrovgrad", "Doljevac", "Gadzin Han", "Kursumlija", "Merosina", "Nis", "Niska Banja", "Pirot", "Prokuplje", "Razanj", "Svrljig", "Zitoradja"],
    "74": ["Bojnik", "Bosilegrad", "Bujanovac", "Crna Trava", "Lebane", "Leskovac", "Medvedja", "Presevo", "Surdulica", "Trgoviste", "Vladicin Han", "Vlasotince", "Vranje"],
    "75": ["Boljevac", "Bor", "Kladovo", "Knjazevac", "Majdanpek", "Negotin", "Soko Banja", "Zajecar"],
    "76": ["Golubac", "Kucevo", "Malo Crnice", "Petrovac na Mlavi", "Pozarevac", "Smederevo", "Smederevska Palanka", "Velika Plana", "Veliko Gradiste", "Zabari", "Zagubica"],
    "77": ["Bogatic", "Koceljeva", "Krupanj", "Lajkovac", "Loznica", "Ljig", "Ljubovija", "Mali Zvornik", "Mionica", "Osecina", "Ub", "Valjevo", "Vladimirci", "Sabac"],
    "78": ["Aleksandrovac", "Brus", "Gornji Milanovac", "Kraljevo", "Krusevac", "Lucani", "Novi Pazar", "Raska", "Sjenica", "Trstenik", "Tutin", "Varvarin", "Vrnjacka Banja", "Cicevac", "Cacak"],
    "79": ["Arilje", "Bajina Basta", "Ivanjica", "Kosjeric", "Nova Varos", "Pozega", "Priboj", "Prijepolje", "Uzice", "Cajetina"],
    
    #80-90 Serbia vojvodina
    "80": ["Bac", "Backa Palanka", "Backi Petrovac", "Beocin", "Novi Sad", "Sremski Karlovci", "Temerin", "Titel", "Zabalj"],
    "81": ["Apatin", "Odžaci", "Sombor"],
    "82": ["Ada", "Backa Topola", "Kanjiza", "Kula", "Mali Idjos", "Senta", "Subotica"],
    "83": ["Becej", "Srbobran", "Vrbas"],
    "84": ["Kikinda", "Nova Crnja", "Novi Knezevac", "Coka"],
    "85": ["Novi Becej", "Secanj", "Zrenjanin", "Zitiste"],
    "86": ["Alibunar", "Kovacica", "Kovin", "Opovo", "Pancevo"],
    "87": ["Bela Crkva", "Plandiste", "Vrsac"],
    "88": ["Indjija", "Irig", "Pecinci", "Ruma", "Stara Pazova"],
    "89": ["Sremska Mitrovica", "Sid"],

    #90-99 Kosovo
    "91": ["Glogovac", "Kosovo Polje", "Lipljan", "Novo Brdo", "Obilic", "Podujevo", "Pristina"],
    "92": ["Kosovska Mitrovica", "Leposavic", "Srbica", "Vucitrn", "Zubin Potok", "Zvecan"],
    "93": ["Decani", "Istok", "Klina", "Pec"],
    "94": ["Djakovica"],
    "95": ["Dragas", "Gora", "Malisevo", "Opolje", "Orahovac", "Prizren", "Suva Reka"],
    "96": ["Kacanik", "Urosevac", "Stimlje", "Strpce"],
    "97": ["Gnjilane", "Kosovska Kamenica", "Vitina"]
}

NUMBERS_TO_WORDS_DICT = {
    "1": "jedan",
    "2": "dva",
    "3": "tri",
    "4": "četiri",
    "5": "pet",
    "6": "šest",
    "7": "sedam",
    "8": "osam",
    "9": "devet",
    "10": "deset",
    "11": "jedanaest",
    "12": "dvanaest",
    "13": "trinaest",
    "14": "četrnaest",
    "15": "petnaest",
    "16": "šesnaest",
    "17": "sedamnaest",
    "18": "osamnaest",
    "19": "devetnaest",
    "20": "dvadeset",   
    "30": "trideset",
    "40": "četrdeset",
    "50": "pedeset",
    "60": "šezdeset",
    "70": "sedamdeset",
    "80": "osamdeset",
    "90": "devedeset",
    "100": "sto",
    "200": "dvesta",
    "300": "trista",      
    "400": "četiristo",  
    "500": "petsto",
    "600": "šeststo",
    "700": "sedamsto",
    "800": "osamsto",
    "900": "devetsto",
    "1000": "hiljadu"
}
NUMBER_STEMS = ["jedan", "jedn", "dve", "hiljad", "milion", "milijard"]

MONEY_CURRENCY_DICT = {
    "RSD": ["dinara", "dinar"],
    "EUR": ["evra", "evro"],
    "DEM": ["nemačkih maraka", "nemačka marka"],
    "FFR": ["francuskih franaka", "francuski franak"],
    "USD": ["dolara", "dolar"],
    "GBP": ["funti", "funta"],
    "KM":  ["konvertibilnih maraka", "konvertibilna marka"],
    "BAM": ["konvertibilnih maraka", "konvertibilna marka"],
    "CHF": ["švajcarskih franaka", "švajcarski franak"],
    "JPY": ["jena", "jen"],
    "CNY": ["juana", "juan"],
    "HUF": ["forinti", "forinta"],
    "RUB": ["rubalja", "rublja"],
    "AED": ["dirhama", "dirham"],
    "INR": ["rupija", "rupija"],
    "MKD": ["denara", "denar"],
    "CAD": ["kanadskih dolara", "kanadski dolar"],
    "AUD": ["australijskih dolara", "australijski dolar"],
    "CZK": ["čeških kruna", "češka kruna"],
    "DKK": ["danskih kruna", "danska kruna"],
    "NOK": ["norveških kruna", "norveška kruna"],
    "SEK": ["švedskih kruna", "švedska kruna"],
    "TRY": ["turskih lira", "turska lira"],
    "PLN": ["poljskih zlota", "poljski zlot"],
    "KWD": ["kuvajtskih dinara", "kuvajtski dinar"],
    "RON": ["rumunskih leja", "rumunski lej"],
    "BGN": ["bugarskih leva", "bugarski lev"]
}

SERBIAN_BANK_CODES = {
    "active":
        {
        "105": "AIK Banka",
        "115": "Yettel Bank",
        "145": "Adriatic Bank",
        "155": "Halkbank",
        "160": "Banca Intesa",
        "165": "Addiko Bank",
        "170": "UniCredit Bank Srbija",
        "190": "Alta banka",
        "200": "Banka Poštanska štedionica",
        "205": "NLB Komercijalna banka",
        "220": "ProCredit Bank",
        "250": "Eurobank Direktna",
        "265": "Raiffeisen banka",
        "295": "Srpska banka",
        "325": "OTP Banka Srbija",
        "340": "Erste Bank",
        "370": "3 Banka",
        "375": "API Bank",
        "380": "Mirabank",
        "385": "Bank of China Srbija",
        },
    "special":
    {
        "840": "Uprava za trezor",
        "908": "Narodna banka Srbije",
    },
    "legacy":
    {
        "310": "NLB Banka (now 205)",
        "355": "Vojvođanska banka (now 325)",
        "125": "Piraeus Bank (now 325)",
        "240": "Findomestic banka (now 325)",
        "140": "JUBMES banka (now 190)"
    }    
}
STATEHOOD_INDICATORS = ['drzav', 'držav', 'republika', 'federacija', 'kraljevina', 'kraljevstvo']

NUMCAR_PLATE_LIST = [
    "AC", "AL", "AR", "BB", "BG", "BO", "BP", "BT", "BU", "BĆ", "BČ", "DE", 
    "GL", "GM", "IC", "IN", "JA", "KA", "KC", "KG", "KI", "KL", "KM", "KO", 
    "KU", "KV", "KŠ", "KŽ", "LB", "LE", "LO", "LU", "NG", "NI", "NP", "NS", 
    "NV", "PA", "PB", "PE", "PI", "PK", "PN", "PO", "PP", "PR", "PT", "PZ", 
    "PŽ", "RA", "RU", "SA", "SC", "SD", "SJ", "SM", "SO", "SP", "ST", "SU", 
    "SV", "SV", "TO", "TS", "TT", "UB", "UE", "UR", "VA", "VB", "VL", "VP", 
    "VR", "VS", "VŠ", "ZA", "ZR", "ĆU", "ČA", "ĐA", "ŠA", "ŠI"
]

