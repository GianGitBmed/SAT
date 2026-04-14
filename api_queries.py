# api_queries.py

# ==============================================================================
# MUTATIONS & QUERIES GRAPHQL
# ==============================================================================

# Mutation per Censimento EX-NOVO
GRAPHQL_CREATE_CI_NEED = """
mutation CreateConfigurationItemNeed($input: CreateConfigurationItemNeedInput!) {
    createConfigurationItemNeed(input: $input) {
        successful
        warnings { fieldName message }
        errors { fieldName message }
    }
}
"""

# Mutation specifica per ASSOCIAZIONE (come richiamata nel tuo app.py)
GRAPHQL_ASSOC_CI_QUERY = """
mutation CreateConfigurationItemNeed($input: CreateConfigurationItemNeedInput!) {
    createConfigurationItemNeed(input: $input) {
        successful
        warnings { fieldName message }
        errors { fieldName message }
    }
}
"""

# Query usata dal tuo app.py per scaricare SOLO i Configuration Items (Funzionante)
GRAPHQL_SYNC_CIS = """
query {
    configurationItems {
        id
        name
        domains {
            id
            code
            description
        }
    }
}
"""

# ==============================================================================
# COSTANTI EXCEL (TEMPLATE)
# ==============================================================================

EXCEL_CREATE_HEADER = [
    "name", "description", "solutionDesignId", "domainIds", 
    "maintenanceDevelopmentTeamId", "changeDevelopmentTeamIds", 
    "maintenanceIctOfficeId", "changeIctOfficeIds", 
    "buildingBlockInstanceId", "applicationModuleIds", "technologyId"
]
EXCEL_CREATE_EXAMPLE = [
    ["App_ExNovo_01", "Censimento Massivo", "123", "456|789", "111", "222", "333", "444", "555", "666|777", "888"]
]

EXCEL_ASSOC_HEADER = [
    "configurationItemId", "solutionDesignId", "applicationModuleIds", "description"
]
EXCEL_ASSOC_EXAMPLE = [
    ["999", "123", "666|777", "Associazione massiva di CI esistente"]
]