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
        # --- API KEY & LOGS ---
        self.entry_api_key = ft.TextField(
            label="Authentication Token (API Key)",
            value=self.app.config.get("api_key", ""),
            password=True,
            can_reveal_password=True,
            width=450,
            border_color=ft.Colors.GREY_700,
        )

        self.dropdown_verbosity = ft.Dropdown(
            label="Livello Log",
            options=[
                ft.dropdown.Option("DEBUG"),
                ft.dropdown.Option("INFO"),
                ft.dropdown.Option("WARN"),
                ft.dropdown.Option("ERROR")
            ],
            value=self.app.config.get("verbosity", "INFO"),
            width=150,
            border_color=ft.Colors.GREY_700,
        )

        self.btn_save = ft.ElevatedButton(
            "Salva Configurazione",
            icon=ft.Icons.SAVE,
            on_click=self.save_settings,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, padding=15)
        )

        # --- SYNC DB ---
        self.chk_ci = ft.Checkbox(label="Configuration Items (20k+)", value=True)
        self.chk_do = ft.Checkbox(label="Domains", value=True)
        self.chk_sd = ft.Checkbox(label="Solution Designs", value=True)
        self.chk_te = ft.Checkbox(label="Teams & Offices", value=True)
        self.chk_bb = ft.Checkbox(label="BB Instances & App Modules", value=True)
        self.chk_tc = ft.Checkbox(label="Technologies", value=True)
        
        self.chk_col1 = ft.Column([self.chk_ci, self.chk_do, self.chk_sd], spacing=2)
        self.chk_col2 = ft.Column([self.chk_te, self.chk_bb, self.chk_tc], spacing=2)
        self.chk_row = ft.Row([self.chk_col1, self.chk_col2], spacing=30, alignment=ft.MainAxisAlignment.START)

        self.btn_sync = ft.ElevatedButton(
            "Sincronizza Selezionati",
            icon=ft.Icons.SYNC,
            on_click=self.sync_configuration_items,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, padding=15)
        )

        self.txt_status = ft.Text("", color=ft.Colors.AMBER_300, size=14)

        self.content = ft.Column(
            controls=[
                ft.Text("Impostazioni & Autenticazione", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_100),
                ft.Divider(height=40, color=ft.Colors.GREY_800),
                ft.Row([self.entry_api_key, self.dropdown_verbosity, self.btn_save], alignment=ft.MainAxisAlignment.START, spacing=20),
                ft.Divider(height=40, color=ft.Colors.GREY_800),
                ft.Text("Sincronizzazione Dati Modulare", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Seleziona i master data da aggiornare. L'estrazione avverrà in sequenza iterativa.", color=ft.Colors.GREY_400),
                self.chk_row,
                ft.Container(height=10),
                ft.Row([self.btn_sync, self.txt_status], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
            ],
            alignment=ft.MainAxisAlignment.START,
        )

    def save_settings(self, e):
        new_key = self.entry_api_key.value.strip()
        self.app.config["api_key"] = new_key
        self.app.config["verbosity"] = self.dropdown_verbosity.value
        config.save_app_config(self.app.config)
        self.app.log("Impostazioni e preferenze salvate correttamente.")
        self.show_dialog("Impostazioni", "Configurazione salvata con successo.")

    def sync_configuration_items(self, e):
        """Avvia la sincronizzazione in un thread separato."""
        api_key = self.app.config.get("api_key", "")
        if not api_key:
            self.show_dialog("Attenzione", "Devi prima inserire e salvare la API Key.", is_error=True)
            return

        # Raccogliamo la lista dei target dal frontend
        targets = []
        if self.chk_ci.value: targets.append("configuration_items")
        if self.chk_do.value: targets.append("domains")
        if self.chk_sd.value: targets.append("solution_designs")
        if self.chk_te.value: targets.append("teams")
        if self.chk_bb.value: targets.append("bb_instances")
        if self.chk_tc.value: targets.append("technologies")
        
        if not targets:
            self.show_dialog("Attenzione", "Seleziona almeno un dominio da sincronizzare.", is_error=True)
            return

        self.btn_sync.disabled = True
        self.txt_status.value = "Sincronizzazione avviata... Controlla il terminale per i dettagli."
        self.txt_status.color = ft.Colors.AMBER_300
        self.update()

        # Dialog di caricamento
        self.progress_text = ft.Text("Inizializzazione...", size=14, weight=ft.FontWeight.BOLD)
        self.loading_dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.WARNING_ROUNDED, color=ft.Colors.YELLOW_600), ft.Text("Sincronizzazione Modulare")]),
            content=ft.Column([
                ft.Row([
                    ft.ProgressRing(width=30, height=30, value=None), 
                    self.progress_text
                ], spacing=20),
                ft.Text(f"Download e salvataggio di {len(targets)} domini in sequenza...", size=12, color=ft.Colors.GREY_400)
            ], tight=True, spacing=10),
        )
        self.app.page.show_dialog(self.loading_dlg)

        # Gestore Eventi Architetturale per UI
        def handle_sync_event(msg):
            self.progress_text.value = str(msg)
            self.app.page.update()
            
        self.app.page.pubsub.subscribe(handle_sync_event)

        self.app.page.run_thread(self._run_sync_logic, api_key, targets)

    def _run_sync_logic(self, api_key, targets):
        """Logica iterativa per domini selezionati."""
        try:
            self.app.log("--- INIZIO SINCRONIZZAZIONE MODULARE REST ---")
            
            # NOTA BENE: Non riazzero più app.local_db per non cancellare la ram pregressa
            if not hasattr(self.app, "local_db") or not isinstance(self.app.local_db, dict):
                self.app.local_db = {}
                
            elementi_totali_estratti = 0
            errori_riscontrati = []

            all_endpoints = {
                "configuration_items": "configuration_items/search?per_page=1000000",
                "domains": "domains/search?per_page=10000",
                "solution_designs": "solution_designs?per_page=15000",
                "teams": "teams?per_page=15000",
                "bb_instances": "building_block_instances?per_page=15000",
                "technologies": "technologies?per_page=15000"
            }
            
            rest_endpoints = {k: v for k, v in all_endpoints.items() if k in targets}
            total_steps = len(rest_endpoints)

            for i, (local_key, endpoint) in enumerate(rest_endpoints.items(), start=1):
                # Update interfaccia intermedio tramite Event Handler
                self.app.page.pubsub.send_all(f"[{i}/{total_steps}] Staging '{local_key}'...")
                
                # Pausa voluta da architettura Flet & spec user
                import time
                time.sleep(0.5)
                
                # Esecuzione chiamata REST effettiva bloccante
                self.app.log(f"Scaricamento {local_key}...")
                self.app.log(f"[NET] Chiamando ApiClient.send_rest_get per {local_key}...", level="DEBUG")
                res_rest = ApiClient.send_rest_get(api_key, endpoint)
                self.app.log(f"[NET] Risposta da ApiClient per {local_key} completata.", level="DEBUG")
                
                if res_rest["success"]:
                    data = res_rest["data"]
                    lista_items = []
                    
                    if isinstance(data, list):
                        lista_items = data
                    elif isinstance(data, dict):
                        for v in data.values():
                            if isinstance(v, list):
                                lista_items = v
                                break
                    
                    if lista_items:
                        dict_items = {}
                        for item in lista_items:
                            if 'id' not in item: continue
                            if local_key == "domains":
                                code = item.get('code', '')
                                desc = item.get('description', '')
                                label = f"{code} - {desc}".strip(" -")
                                dict_items[str(item['id'])] = label if label else f"ID: {item['id']}"
                            else:
                                dict_items[str(item['id'])] = item.get('name', f"ID: {item['id']}")

                        self.app.local_db[local_key] = dict_items
                        elementi_totali_estratti += len(dict_items)
                        self.app.log(f"[OK] {local_key} scaricati: {len(dict_items)}")

                        if local_key == "teams":
                            off_list = {str(o['id']): o.get('name', f"ID: {o['id']}") for o in lista_items if o.get('is_ict_office') is True}
                            self.app.local_db["offices"] = off_list
                            elementi_totali_estratti += len(off_list)
                            self.app.log(f"[OK] offices estratti: {len(off_list)}")
                            
                        if local_key == "bb_instances":
                            app_modules_dict = {}
                            for bb in lista_items:
                                for m in bb.get('application_modules', []):
                                    if 'id' in m:
                                        app_modules_dict[str(m['id'])] = m.get('name', m.get('short_name', f"ID: {m['id']}"))
                            self.app.local_db["app_modules"] = app_modules_dict
                            elementi_totali_estratti += len(app_modules_dict)
                            self.app.log(f"[OK] app_modules estratti: {len(app_modules_dict)}")
                    else:
                        self.app.local_db[local_key] = {}
                        self.app.log(f"[WARN] {local_key}: Nessun dato trovato.")
                        
                    # === SALVATAGGIO PROGRESSIVO IMMEDIATO ===
                    self.app.page.pubsub.send_all(f"[{i}/{total_steps}] Scrittura su disco '{local_key}'...")
                    
                    config.save_local_db(self.app.local_db)
                    self.app.log(f"[SYS] Salvato stadio intermedio DB dopo operazione su {local_key}.")
                else:
                    err_msg = res_rest.get('error', 'Errore API')
                    self.app.log(f"[KO] {local_key} Fallito: {err_msg}", level="ERROR")
                    errori_riscontrati.append(f"{local_key}: {err_msg}")

            # Chiusura finale
            self.app.config.setdefault("stats", {})["last_sync"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            config.save_app_config(self.app.config)
            self.app.log(f"--- SINCRONIZZAZIONE MODULARE CONCLUSA: {elementi_totali_estratti} record processati in questa run ---")

            # Reset UI
            try: self.app.page.pubsub.unsubscribe_all() 
            except Exception: pass
            
            self.close_dialog(self.loading_dlg)
            self.btn_sync.disabled = False
            
            if not errori_riscontrati:
                self.txt_status.value = f"Completato batch da: {elementi_totali_estratti} record."
                self.txt_status.color = ft.Colors.GREEN_400
                self.show_dialog("Successo", f"Elaborazione conclusa regolarmente.\nImportati {elementi_totali_estratti} record durante questo giro.")
            else:
                self.txt_status.value = "Completato con errori in uno o più moduli."
                self.txt_status.color = ft.Colors.AMBER_400
                self.show_dialog("Sync Parziale", f"Errori riscontrati sui seguenti domini:\n" + "\n".join(errori_riscontrati), is_error=True)
            
            self.page.update()

        except Exception as ex:
            self.sync_running = False
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