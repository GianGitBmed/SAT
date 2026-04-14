# settings.py
import flet as ft
import threading
import datetime
import config
from api_client import ApiClient

class SettingsView(ft.Container):
    def __init__(self, master, app_context):
        super().__init__(expand=True, padding=40)
        self.app = app_context
        self.build_ui()

    def build_ui(self):
        # --- API KEY ---
        self.entry_api_key = ft.TextField(
            label="Authentication Token (API Key)",
            value=self.app.config.get("api_key", ""),
            password=True,
            can_reveal_password=True,
            width=450,
            border_color=ft.Colors.GREY_700,
        )

        self.btn_save = ft.ElevatedButton(
            "Salva Configurazione",
            icon=ft.Icons.SAVE,
            on_click=self.save_settings,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, padding=15)
        )

        # --- SYNC DB ---
        self.btn_sync = ft.ElevatedButton(
            "Sincronizza Master Data",
            icon=ft.Icons.SYNC,
            on_click=self.sync_configuration_items,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, padding=15)
        )

        self.txt_status = ft.Text("", color=ft.Colors.AMBER_300, size=14)

        self.content = ft.Column(
            controls=[
                ft.Text("Impostazioni & Autenticazione", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_100),
                ft.Divider(height=40, color=ft.Colors.GREY_800),
                ft.Row([self.entry_api_key, self.btn_save], alignment=ft.MainAxisAlignment.START, spacing=20),
                ft.Divider(height=40, color=ft.Colors.GREY_800),
                ft.Text("Sincronizzazione Dati (Manuale)", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Scarica le liste aggiornate direttamente da Distinta in RAM locale.", color=ft.Colors.GREY_400),
                ft.Text("Tempo stimato per la sincronizzazione dai 60 ai 90s!", color=ft.Colors.ORANGE_400),
                ft.Container(height=10),
                ft.Row([self.btn_sync, self.txt_status], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
            ],
            alignment=ft.MainAxisAlignment.START,
        )

    def save_settings(self, e):
        new_key = self.entry_api_key.value.strip()
        self.app.config["api_key"] = new_key
        config.save_app_config(self.app.config)
        self.app.log("Impostazioni salvate correttamente.")
        self.show_dialog("Impostazioni", "Configurazione (API Key) salvata con successo.")

    def sync_configuration_items(self, e):
        """Avvia la sincronizzazione in un thread separato."""
        api_key = self.app.config.get("api_key", "")
        if not api_key:
            self.show_dialog("Attenzione", "Devi prima inserire e salvare la API Key.", is_error=True)
            return

        self.btn_sync.disabled = True
        self.txt_status.value = "Sincronizzazione avviata... Controlla il terminale per i dettagli."
        self.txt_status.color = ft.Colors.AMBER_300
        self.update()

        # Dialog di caricamento (non modale per evitare deadlock se il socket si appesantisce)
        self.loading_dlg = ft.AlertDialog(
            title=ft.Text("Sincronizzazione in corso"),
            content=ft.Row([
                ft.ProgressRing(width=20, height=20),
                ft.Text("Download dati massivi (24k+ record)...", size=14)
            ], spacing=20),
        )
        self.app.page.show_dialog(self.loading_dlg)

        threading.Thread(target=self._run_sync_logic, args=(api_key,), daemon=True).start()

    def _run_sync_logic(self, api_key):
        """Logica di estrazione originale ripristinata integralmente."""
        try:
            self.app.log("--- INIZIO SINCRONIZZAZIONE GLOBALE REST ---")
            self.app.local_db = {}
            elementi_totali = 0
            errori_riscontrati = []

            rest_endpoints = {
                "configuration_items": "configuration_items/search?per_page=1000000",
                "domains": "domains/search?per_page=10000",
                "solution_designs": "solution_designs?per_page=15000",
                "teams": "teams?per_page=15000",
                "bb_instances": "building_block_instances?per_page=15000",
                "technologies": "technologies?per_page=15000"
            }

            for local_key, endpoint in rest_endpoints.items():
                self.app.log(f"Scaricamento {local_key}...")
                res_rest = ApiClient.send_rest_get(api_key, endpoint)
                
                if res_rest["success"]:
                    data = res_rest["data"]
                    lista_items = []
                    
                    # Logica originale di estrazione
                    if isinstance(data, list):
                        lista_items = data
                    elif isinstance(data, dict):
                        for v in data.values():
                            if isinstance(v, list):
                                lista_items = v
                                break
                    
                    if lista_items:
                        dict_items = {}
                        for i in lista_items:
                            if 'id' not in i: continue
                            if local_key == "domains":
                                code = i.get('code', '')
                                desc = i.get('description', '')
                                label = f"{code} - {desc}".strip(" -")
                                dict_items[str(i['id'])] = label if label else f"ID: {i['id']}"
                            else:
                                dict_items[str(i['id'])] = i.get('name', f"ID: {i['id']}")

                        self.app.local_db[local_key] = dict_items
                        elementi_totali += len(dict_items)
                        self.app.log(f"[OK] {local_key} scaricati: {len(dict_items)}") # Ripristinato log

                        if local_key == "teams":
                            off_list = {str(o['id']): o.get('name', f"ID: {o['id']}") for o in lista_items if o.get('is_ict_office') is True}
                            self.app.local_db["offices"] = off_list
                            elementi_totali += len(off_list)
                            self.app.log(f"[OK] offices estratti: {len(off_list)}")
                            
                        if local_key == "bb_instances":
                            app_modules_dict = {}
                            for bb in lista_items:
                                for m in bb.get('application_modules', []):
                                    if 'id' in m:
                                        app_modules_dict[str(m['id'])] = m.get('name', m.get('short_name', f"ID: {m['id']}"))
                            self.app.local_db["app_modules"] = app_modules_dict
                            elementi_totali += len(app_modules_dict)
                            self.app.log(f"[OK] app_modules estratti: {len(app_modules_dict)}")
                    else:
                        self.app.local_db[local_key] = {}
                        self.app.log(f"[WARN] {local_key}: Nessun dato trovato.")
                else:
                    err_msg = res_rest.get('error', 'Errore API')
                    self.app.log(f"[KO] {local_key} Fallito: {err_msg}", level="ERROR")
                    errori_riscontrati.append(f"{local_key}: {err_msg}")

            # Salvataggio e chiusura
            config.save_local_db(self.app.local_db)
            self.app.config.setdefault("stats", {})["last_sync"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            config.save_app_config(self.app.config)
            
            self.app.log(f"--- SINCRONIZZAZIONE CONCLUSA: {elementi_totali} record totali ---")

            # Reset UI
            self.close_dialog(self.loading_dlg)
            self.btn_sync.disabled = False
            
            if not errori_riscontrati:
                self.txt_status.value = f"Completato: {elementi_totali} record."
                self.txt_status.color = ft.Colors.GREEN_400
                self.show_dialog("Successo", f"Database aggiornato con {elementi_totali} record.")
            else:
                self.txt_status.value = "Completato con errori parziali."
                self.txt_status.color = ft.Colors.AMBER_400
                self.show_dialog("Sync Parziale", f"Errori:\n" + "\n".join(errori_riscontrati), is_error=True)
            
            self.page.update()

        except Exception as ex:
            self.close_dialog(self.loading_dlg)
            self.btn_sync.disabled = False
            self.txt_status.value = "Errore critico durante il sync."
            self.txt_status.color = ft.Colors.RED_400
            self.page.update()
            self.app.log(f"CRASH SYNC: {str(ex)}", level="ERROR")

    def show_dialog(self, title, content, is_error=False):
        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.INFO, color=ft.Colors.RED if is_error else ft.Colors.BLUE), ft.Text(title)]),
            content=ft.Text(content),
            actions=[ft.TextButton("Chiudi", on_click=lambda e: self.close_dialog(dlg))]
        )
        self.app.page.show_dialog(dlg)

    def close_dialog(self, dlg):
        if hasattr(self.app.page, "close_dialog"):
            self.app.page.close_dialog()
        else:
            dlg.open = False
            self.app.page.update()