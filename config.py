# config.py

# -------------------------
# ACTIVE PROVIDER
# -------------------------
ACTIVE_PROVIDER = "investingdotcom"   # ilboursa | bvmt | tunisie_valeurs | investingdotcom

# -------------------------
# DATABASE
# -------------------------
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASSWORD = "root"
DB_NAME = "tunindex"


# Stock dictionary from our mapping
TUNISIAN_STOCKS = {
    "AB": {"symbol": "AB", "name": "AMEN BANK", "url": "/equities/amen-bank"},
    "AL": {"symbol": "AL", "name": "AIR LIQUIDE Tun", "url": "/equities/air-liquide-tunisie"},
    "ARTES": {"symbol": "ARTES", "name": "Automobile Reseau Tunisien Et Service", "url": "/equities/artes-renault"},
    "AST": {"symbol": "AST", "name": "ASTREE SA", "url": "/equities/com.-dassur.et-de-reassur."},
    "ATB": {"symbol": "ATB", "name": "ATB", "url": "/equities/arab-tunisian-bank"},
    "ATL": {"symbol": "ATL", "name": "ATL", "url": "/equities/arab-tunisian-lease"},
    "BH": {"symbol": "BH", "name": "BH Bank", "url": "/equities/banque-de-lhabitat"},
    "BIAT": {"symbol": "BIAT", "name": "BIAT", "url": "/equities/banque-inter.-arabe-de-tunisie"},
    "BNA": {"symbol": "BNA", "name": "BNA", "url": "/equities/banque-nationale-agricole"},
    "BS": {"symbol": "BS", "name": "ATTIJARI BANK", "url": "/equities/banque-attijari-de-tunisie"},
    "BT": {"symbol": "BT", "name": "BT", "url": "/equities/banque-de-tunisie"},
    "BTEI": {"symbol": "BTEI", "name": "BTEI", "url": "/equities/bq-de-tunisie-et-des-emirats"},
    "CC": {"symbol": "CC", "name": "Carthage Cement", "url": "/equities/carthage-cement"},
    "CIL": {"symbol": "CIL", "name": "CIL", "url": "/equities/compagnie-int.-de-leasing"},
    "ICF": {"symbol": "ICF", "name": "ICF", "url": "/equities/soc.-des-ind.-chimiu.-du-fluor"},
    "MGR": {"symbol": "MGR", "name": "Societe Tunisienne des Marches de Gros", "url": "/equities/sotumag"},
    "BHL": {"symbol": "BHL", "name": "BH Leasing", "url": "/equities/modern-leasing"},
    "MNP": {"symbol": "MNP", "name": "Societe Nouvelle Maison de la Ville de Tunis", "url": "/equities/monoprix"},
    "NAKL": {"symbol": "NAKL", "name": "Ennakl Automobiles", "url": "/equities/ennakl-automobiles"},
    "PLTU": {"symbol": "PLTU", "name": "PLACEMENT DE TUNISIE", "url": "/equities/placements-de-tunisie"},
    "POULA": {"symbol": "POULA", "name": "POULINA GROUP HLD", "url": "/equities/poulina-group-holding"},
    "SCB": {"symbol": "SCB", "name": "Les Ciments de Bizerte", "url": "/equities/ciments-de-bizerte"},
    "SFBT": {"symbol": "SFBT", "name": "SFBT", "url": "/equities/sfbt"},
    "SIAM": {"symbol": "SIAM", "name": "STE Ind d'appareillage Et De Materiels Elec", "url": "/equities/siame"},
    "SIMP": {"symbol": "SIMP", "name": "SIMPAR", "url": "/equities/soc.-immob.-et-de-part."},
    "SITS": {"symbol": "SITS", "name": "SITS", "url": "/equities/soc.-immob.-tuniso-seoud."},
    "SMG": {"symbol": "SMG", "name": "MAGASIN GENERAL", "url": "/equities/magazin-gneral"},
    "SOKNA": {"symbol": "SOKNA", "name": "ESSOUKNA", "url": "/equities/societe-essoukna"},
    "SOMOC": {"symbol": "SOMOC", "name": "SOMOCER", "url": "/equities/societe-moderne-de-ceramique"},
    "SOTE": {"symbol": "SOTE", "name": "STE Tunisienne d'entreprises De Telecommunications", "url": "/equities/sotetel"},
    "SPDI": {"symbol": "SPDI", "name": "SPDIT-SICAF", "url": "/equities/spdit"},
    "STAR": {"symbol": "STAR", "name": "STAR", "url": "/equities/star"},
    "STB": {"symbol": "STB", "name": "S.T.B", "url": "/equities/societe-tunisienne-de-banque"},
    "STIP": {"symbol": "STIP", "name": "Societe Tunisienne des Industries de Pneumatiques", "url": "/equities/soc.-tun.-des-ind.-de-pneumatiques"},
    "STPIL": {"symbol": "STPIL", "name": "SOTRAPIL", "url": "/equities/sotrapil"},
    "TINV": {"symbol": "TINV", "name": "TUN INVEST - SICAR", "url": "/equities/tuninvest"},
    "TJL": {"symbol": "TJL", "name": "ATTIJARI LEASING", "url": "/equities/attijari-leasing"},
    "TLNET": {"symbol": "TLNET", "name": "TELNET", "url": "/equities/telnet-holding"},
    "TLS": {"symbol": "TLS", "name": "TUNISIE LEASING", "url": "/equities/tunisie-leasing"},
    "TPR": {"symbol": "TPR", "name": "TPR", "url": "/equities/soc.-tun.-profiles-aluminium"},
    "TRE": {"symbol": "TRE", "name": "Tunis Re", "url": "/equities/soc.-tun.-de-reassurance"},
    "UBCI": {"symbol": "UBCI", "name": "Union Bancaire pour le Commerce et l'Industrie", "url": "/equities/u.b.c.i"},
    "UIB": {"symbol": "UIB", "name": "UIB", "url": "/equities/union-internationale-de-banque"},
    "WIFAK": {"symbol": "WIFAK", "name": "EL WIFACK LEASING", "url": "/equities/el-wifack-leasing"},
    "STVR": {"symbol": "STVR", "name": "Societe Tunisienne De Verreries", "url": "/equities/soc-tunisienne-de-verreries"},
    "BHASS": {"symbol": "BHASS", "name": "BH Assurance", "url": "/equities/salim"},
    "LNDOR": {"symbol": "LNDOR", "name": "Land Or", "url": "/equities/land-or"},
    "NBL": {"symbol": "NBL", "name": "New Body Li", "url": "/equities/new-body-li"},
    "OTH": {"symbol": "OTH", "name": "One Tech Ho", "url": "/equities/one-tech-ho"},
    "STPAP": {"symbol": "STPAP", "name": "Societe Tunisienne Industrielle Du Papier Et Du Ca", "url": "/equities/sotipapier"},
    "SOTEM": {"symbol": "SOTEM", "name": "Sotemail", "url": "/equities/sotemail"},
    "SAH": {"symbol": "SAH", "name": "Sah", "url": "/equities/sah"},
    "HANL": {"symbol": "HANL", "name": "Hannibal Lease", "url": "/equities/hannibal-lease"},
    "CITY": {"symbol": "CITY", "name": "City Cars", "url": "/equities/city-cars"},
    "ECYCL": {"symbol": "ECYCL", "name": "Euro-Cycles", "url": "/equities/euro-cycles"},
    "MPBS": {"symbol": "MPBS", "name": "Manufacture de Panneaux Bois du Sud", "url": "/equities/mpbs"},
    "BL": {"symbol": "BL", "name": "Best Lease", "url": "/equities/best-lease"},
    "DH": {"symbol": "DH", "name": "Societe Delice Holding", "url": "/equities/societe-delice-holding"},
    "PLAST": {"symbol": "PLAST", "name": "OfficePlast", "url": "/equities/officeplast"},
    "UMED": {"symbol": "UMED", "name": "Unite de Fabrication de Medicaments", "url": "/equities/unimed-sa"},
    "SAMAA": {"symbol": "SAMAA", "name": "Atelier Meuble Interieurs", "url": "/equities/atelier-meuble-interieurs"},
    "ASSMA": {"symbol": "ASSMA", "name": "Ste Assurances Magrebia", "url": "/equities/ste-assurances-magrebia"},
    "SMART": {"symbol": "SMART", "name": "Smart Tunisie", "url": "/equities/smart-tunisie"},
    "STAS": {"symbol": "STAS", "name": "Societe Tunisienne D Automobiles", "url": "/equities/societe-tunisienne-d-automobiles"},
    "AMV": {"symbol": "AMV", "name": "Assurances Maghrebia Vie", "url": "/equities/assurances-maghrebia-vie"},
}
# -------------------------
# SCRAPING SETTINGS
# -------------------------
USE_PROXY = False
USE_BROWSER = True

REQUEST_TIMEOUT = 10
RETRY_COUNT = 3
RATE_LIMIT_DELAY = 1.5

# -------------------------
# CACHE
# -------------------------
CACHE_TTL = 3600  # seconds

# -------------------------
# PARALLELISM
# -------------------------
MAX_WORKERS = 10         # Max threads for run_parallel (increase for faster BVPS fetch)
BVPS_SKIP_IF_EXISTS = True  # Skip scraping BVPS if stock already has book_value_per_share