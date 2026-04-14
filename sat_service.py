# ============================================================================
# sat_service.py
# Servizi applicativi SAT per il modulo CIometro
# - Validazione form
# - Costruzione payload API
# - Snapshot export Excel
# - Chiamate Distinta GraphQL
# ============================================================================

from api_client import ApiClient
import api_queries
import excel_handler
import utils


# ============================================================================
# SEZIONE 1 - VALIDAZIONE
# ============================================================================

REQUIRED_FIELDS = [
    ("name", "Nome CI"),
    ("description", "Descrizione"),
    ("solutionDesignId", "Solution Design"),
    ("domainIds", "Domini"),
    ("maintenanceDevelopmentTeamId", "Maintenance Dev Team"),
    ("changeDevelopmentTeamIds", "Change Dev Teams"),
    ("maintenanceIctOfficeId", "Maintenance ICT Office"),
    ("changeIctOfficeIds", "Change ICT Offices"),
    ("buildingBlockInstanceId", "Building Block"),
    ("applicationModuleIds", "Application Modules"),
    ("technologyId", "Tecnologia"),
]


def validate_snapshot(snapshot: dict) -> list:
    """
    Ritorna la lista dei campi mancanti.
    Se vuota, la validazione è OK.
    """
    missing = []

    for key, label in REQUIRED_FIELDS:
        value = snapshot.get(key)

        if isinstance(value, list):
            if len(value) == 0:
                missing.append(label)
        else:
            if not str(value or "").strip():
                missing.append(label)

    return missing


def is_snapshot_empty(snapshot: dict) -> bool:
    """Ritorna True se tutti i campi dello snapshot sono vuoti."""
    for value in snapshot.values():
        if isinstance(value, list):
            if value:
                return False
        else:
            if str(value or "").strip():
                return False
    return True


# ============================================================================
# SEZIONE 2 - COSTRUZIONE SNAPSHOT E PAYLOAD
# ============================================================================

def build_snapshot_from_form(form_data: dict) -> dict:
    """
    Costruisce uno snapshot testuale dei valori del form,
    adatto sia alla validazione che all'export Excel.
    """
    return {
        "name": (form_data.get("name") or "").strip(),
        "description": (form_data.get("description") or "").strip(),
        "solutionDesignId": utils.extract_id(form_data.get("solution_design") or ""),
        "domainIds": "|".join([utils.extract_id(x) for x in form_data.get("domains", [])]),
        "maintenanceDevelopmentTeamId": utils.extract_id(form_data.get("maintenance_team") or ""),
        "changeDevelopmentTeamIds": "|".join([utils.extract_id(x) for x in form_data.get("change_teams", [])]),
        "maintenanceIctOfficeId": utils.extract_id(form_data.get("maintenance_office") or ""),
        "changeIctOfficeIds": "|".join([utils.extract_id(x) for x in form_data.get("change_offices", [])]),
        "buildingBlockInstanceId": utils.extract_id(form_data.get("building_block") or ""),
        "applicationModuleIds": "|".join([utils.extract_id(x) for x in form_data.get("application_modules", [])]),
        "technologyId": utils.extract_id(form_data.get("technology") or "")
    }


def build_api_payload_from_snapshot(snapshot: dict) -> dict:
    """
    Converte lo snapshot testuale in payload tipizzato per GraphQL.
    """
    return {
        "state": "published",
        "environments": ["integration", "test", "preprod", "prod"],
        "type": "created",
        "configurationItemId": None,
        "calledConfigurationItemIds": [],
        "warningsAccepted": False,
        "name": snapshot.get("name", "").strip(),
        "description": snapshot.get("description", "").strip(),
        "solutionDesignId": _to_int(snapshot.get("solutionDesignId", "")),
        "domainIds": _pipe_str_to_int_list(snapshot.get("domainIds", "")),
        "maintenanceDevelopmentTeamId": _to_int(snapshot.get("maintenanceDevelopmentTeamId", "")),
        "changeDevelopmentTeamIds": _pipe_str_to_int_list(snapshot.get("changeDevelopmentTeamIds", "")),
        "maintenanceIctOfficeId": _to_int(snapshot.get("maintenanceIctOfficeId", "")),
        "changeIctOfficeIds": _pipe_str_to_int_list(snapshot.get("changeIctOfficeIds", "")),
        "buildingBlockInstanceId": _to_int(snapshot.get("buildingBlockInstanceId", "")),
        # Ora la funzione è definita correttamente
        "applicationModuleIds": _pipe_str_to_str_list(snapshot.get("applicationModuleIds", "")),
        "technologyId": _to_int(snapshot.get("technologyId", ""))
    }


def _pipe_str_to_int_list(value: str) -> list:
    """Converte una stringa '1|2' in [1, 2]"""
    value = str(value or "").strip()
    return [int(item.strip()) for item in value.split("|") if item.strip().isdigit()]

def _pipe_str_to_str_list(value: str) -> list:
    """Converte una stringa 'A|B' in ['A', 'B']"""
    value = str(value or "").strip()
    return [item.strip() for item in value.split("|") if item.strip()]

def _to_int(value: str):
    """Conversione sicura a int o None"""
    value = str(value or "").strip()
    return int(value) if value.isdigit() else None


# ============================================================================
# SEZIONE 3 - EXPORT EXCEL
# ============================================================================

def export_snapshot_to_excel(filepath: str, snapshot: dict, template_type: str = "create") -> bool:
    """
    Esporta uno snapshot del form in Excel.
    Richiede excel_handler.generate_filled_template().
    """
    if not hasattr(excel_handler, "generate_filled_template"):
        raise Exception("Metodo excel_handler.generate_filled_template() non trovato.")

    return excel_handler.generate_filled_template(filepath, snapshot, template_type)


# ============================================================================
# SEZIONE 4 - CHIAMATE DISTINTA / API
# ============================================================================

def create_ci(api_key: str, snapshot: dict) -> dict:
    """
    Valida snapshot, costruisce payload e invia la mutation GraphQL.
    Ritorna un dict standardizzato:
    {
        "success": bool,
        "message": str,
        "errors": list[str],
        "raw": dict
    }
    """
    api_key = (api_key or "").strip()
    if not api_key:
        return {
            "success": False,
            "message": "API Key mancante.",
            "errors": ["Inserisci e salva prima la API Key nelle Impostazioni."],
            "raw": {}
        }

    missing = validate_snapshot(snapshot)
    if missing:
        return {
            "success": False,
            "message": "Validazione fallita.",
            "errors": [f"Campo obbligatorio mancante: {field}" for field in missing],
            "raw": {}
        }

    payload = build_api_payload_from_snapshot(snapshot)

    print("\n================ API CALL DEBUG ================")
    print("[SAT SERVICE] API KEY PRESENTE:", bool(api_key))
    print("[SAT SERVICE] PAYLOAD:", payload)
    print("[SAT SERVICE] QUERY:", api_queries.GRAPHQL_CREATE_CI_NEED[:200], "...")
    print("================================================\n")

    res = ApiClient.send_graphql(
        api_key,
        api_queries.GRAPHQL_CREATE_CI_NEED,
        {"input": payload}
    )
    if not res.get("success") and res.get("graphql_errors"):
        return {
            "success": False,
            "message": "Errore GraphQL.",
            "errors": [x.get("message", "Errore GraphQL non specificato.") for x in res.get("graphql_errors", [])],
            "raw": res
        }

    print("\n================ API RESPONSE ==================")
    print("[SAT SERVICE] RESPONSE:", res)
    print("================================================\n")
    if not res.get("success"):
        return {
            "success": False,
            "message": res.get("error", "Errore di comunicazione verso Distinta."),
            "errors": [res.get("error", "Errore di comunicazione verso Distinta.")],
            "raw": res
        }

    data = res.get("data", {}).get("createConfigurationItemNeed", {})

    if data.get("successful"):
        return {
            "success": True,
            "message": "Il nuovo CI è stato correttamente censito a sistema.",
            "errors": [],
            "raw": res
        }

    api_errors = [x.get("message", "Errore non specificato.") for x in data.get("errors", [])]
    api_warnings = [x.get("message", "Warning non specificato.") for x in data.get("warnings", [])]

    all_messages = api_errors + api_warnings
    if not all_messages:
        all_messages = ["L'API ha rifiutato l'inserimento senza dettagli."]

    return {
        "success": False,
        "message": "L'API ha rifiutato l'inserimento.",
        "errors": all_messages,
        "raw": res
    }
