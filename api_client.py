# api_client.py
import requests
import urllib3
import config

# Disabilitazione warning SSL globale per l'ambiente di test
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ApiClient:
    @staticmethod
    def send_graphql(api_key: str, query: str, variables: dict = None, timeout: int = 25) -> dict:
        """
        Invia una richiesta GraphQL. Gestisce le eccezioni di rete e standardizza l'output.
        Ritorna: {"success": bool, "data": dict, "error": str, "status": int}
        """
        headers = {
            "Authentication-Token": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        print("[API CLIENT] send_graphql() entrato")
        print("[API CLIENT] URL:", config.API_URL)
        print("[API CLIENT] TIMEOUT:", timeout)
        print("[API CLIENT] HEADERS OK:", bool(api_key))
        print("[API CLIENT] VARIABLES:", variables)
        print("[API CLIENT] requests.post in partenza...")
        try:
            response = requests.post(
                config.API_URL, 
                json=payload, 
                headers=headers, 
                verify=False, 
                timeout=timeout
            )
            print("[API CLIENT] requests.post terminata")
            print("[API CLIENT] HTTP STATUS:", response.status_code)
            print("[API CLIENT] RESPONSE TEXT:", response.text[:1000])    
            if response.status_code == 200:
                body = response.json()

                print("[API CLIENT] RAW GRAPHQL RESPONSE:", body)

                graphql_errors = body.get("errors", [])
                graphql_data = body.get("data", {})

                if graphql_errors:
                    return {
                        "success": False,
                        "error": "GraphQL error",
                        "graphql_errors": graphql_errors,
                        "data": graphql_data,
                        "status": 200
                    }

                return {
                    "success": True,
                    "data": graphql_data,
                    "status": 200
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status": response.status_code
                }   
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout: Il server di Distinta non ha risposto in tempo."}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Errore di connessione: Verifica la VPN o la rete."}
        except Exception as e:
            return {"success": False, "error": f"Eccezione di rete imprevista: {str(e)}"}

    @staticmethod
    def send_rest_get(api_key: str, endpoint: str, timeout: int = 120) -> dict:
        """
        Esegue una chiamata REST GET standardizzata verso Distinta (es. per recuperare Domini, Team).
        """
        headers = {
            "Authentication-Token": api_key,
            "Accept": "application/json"
        }
        
        # Deduciamo l'URL REST sostituendo /graphql con /api dal config.API_URL
        # Es: https://deploy.gbm.lan/graphql -> https://deploy.gbm.lan/api/domains
        base_url = config.API_URL.replace("/graphql", "/api")
        url = f"{base_url}/{endpoint}"

        try:
            response = requests.get(url, headers=headers, verify=False, timeout=timeout)
            
            if response.status_code == 200:
                # AGGIUNTO UN BLOCCO TRY-EXCEPT QUI
                try:
                    data = response.json()
                    return {"success": True, "data": data, "status": 200}
                except ValueError:
                    return {"success": False, "error": "La pagina esiste, ma non contiene dati JSON validi (URL probabilmente errato).", "status": 200}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: Endpoint non trovato.", "status": response.status_code}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout della connessione REST."}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Errore di connessione REST."}
        except Exception as e:
            return {"success": False, "error": f"Eccezione REST imprevista: {str(e)}"}