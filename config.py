# config.py
import json
import os
import sys

# ==============================================================================
# SEZIONE 1: RISOLUZIONE PATH PER COMPILAZIONE (PYINSTALLER / FLET PACK)
# ==============================================================================
def get_app_dir():
    """
    Risolve la cartella reale dell'applicativo, bypassando la cartella temp 
    di PyInstaller creata a runtime quando si usa --onefile.
    """
    if getattr(sys, 'frozen', False):
        # Se stiamo girando dal file .exe compilato
        return os.path.dirname(sys.executable)
    else:
        # Se stiamo girando dallo script Python in locale
        return os.path.abspath(os.path.dirname(__file__))

# ==============================================================================
# SEZIONE 2: COSTANTI DI SISTEMA E PATH
# ==============================================================================
CONFIG_FILE = os.path.join(get_app_dir(), "sat_config.json")
DB_FILE = os.path.join(get_app_dir(), "distinta_db.json")

# Endpoint per le chiamate GraphQL e REST API
API_URL = "https://deploy.gbm.lan/graphql"
REST_API_BASE_URL = "https://deploy.gbm.lan/api"

# ==============================================================================
# SEZIONE 3: GESTIONE CONFIGURAZIONE APPLICATIVO (sat_config.json)
# ==============================================================================
def load_app_config():
    """
    Carica la configurazione dal file JSON. 
    Se il file non esiste o mancano chiavi, effettua un merge con i default.
    """
    default_config = {
        "app_settings": {
            "name": "Solution Architect Tools",
            "version": "3.0"
        },
        "api_key": "",
        "disclaimer_accepted": False,
        "risorse_utili": [
            {
                "label": "Linee Guida Ark",
                "url": "https://notebooklm.google.com/notebook/718d8e8a-d0df-41a8-99b1-c084c9420c7c?authuser=3"
            }
        ],
        "stats": {
            "last_sync": "Mai effettuata",
            "ci_singoli_ok": 0,
            "ci_massivi_ok": 0,
            "ci_ko": 0
        }
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: 
                config = json.load(f)
            
            needs_save = False
            
            if "risorse_utili" not in config:
                config["risorse_utili"] = default_config["risorse_utili"]
                needs_save = True
            if "app_settings" not in config:
                config["app_settings"] = default_config["app_settings"]
                needs_save = True
            if "disclaimer_accepted" not in config:
                config["disclaimer_accepted"] = False
                needs_save = True
            if "stats" not in config:
                config["stats"] = default_config["stats"]
                needs_save = True
            
            if needs_save: 
                save_app_config(config)
            
            return config
            
        except Exception:
            pass
            
    save_app_config(default_config)
    return default_config

def save_app_config(config_data):
    """Salva i dati di configurazione nel file sat_config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f: 
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print(f"Errore durante il salvataggio della configurazione: {e}")

# ==============================================================================
# SEZIONE 4: GESTIONE DATABASE LOCALE (distinta_db.json)
# ==============================================================================
def load_local_db():
    """
    Carica i dati dei Configuration Item salvati localmente.
    Restituisce un dizionario con strutture vuote se il file non esiste.
    """
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f: 
                return json.load(f)
        except Exception:
            pass
            
    return {
        "domains": {}, 
        "solution_designs": {}, 
        "teams": {}, 
        "offices": {}, 
        "bb_instances": {}, 
        "app_modules": {}, 
        "technologies": {}
    }

def save_local_db(db_data):
    """Salva i dati sincronizzati dalle API nel file distinta_db.json."""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f: 
            json.dump(db_data, f, indent=4)
    except Exception as e:
        print(f"Errore durante il salvataggio del database locale: {e}")