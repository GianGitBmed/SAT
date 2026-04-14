import flet as ft
import threading
import os
import openpyxl
import sat_service
import config
from api_queries import EXCEL_CREATE_HEADER

class CensimentoMassivoTab(ft.Container):
    def __init__(self, app_context):
        super().__init__(expand=True, padding=20)
        self.app = app_context
        self.selected_filepath = None
        self.build_ui()

    def build_ui(self):
        # UI Elements
        self.txt_file_path = ft.Text("Nessun file selezionato", color=ft.Colors.GREY_500, italic=True)
        
        self.btn_pick_file = ft.ElevatedButton(
            "Seleziona Excel Template",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self.open_file_picker,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_700, color=ft.Colors.WHITE)
        )
        
        self.btn_start = ft.ElevatedButton(
            "Avvia Censimento Massivo",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self.start_massive_import,
            disabled=True,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
        )
        
        # FilePicker Registration (se non già registrato globalmente in app.py)
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.app.page.overlay.append(self.file_picker)

        # Progress and Logs
        self.progress_bar = ft.ProgressBar(width=600, value=0, visible=False, color=ft.Colors.GREEN_400)
        self.txt_status = ft.Text("Pronto.", color=ft.Colors.AMBER_300, size=14)
        
        self.log_list = ft.ListView(expand=True, spacing=2, auto_scroll=True)
        self.log_container = ft.Container(
            content=self.log_list,
            height=300,
            bgcolor=ft.Colors.BLACK,
            border=ft.border.all(1, ft.Colors.GREY_800),
            border_radius=5,
            padding=10,
            margin=ft.margin.only(top=20)
        )

        # Layout
        self.content = ft.Column(
            controls=[
                ft.Text("Censimento Massivo CI", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_300),
                ft.Text("Importa il template Excel per creare multipli Configuration Item in un singolo job.", color=ft.Colors.GREY_400),
                ft.Divider(height=20, color=ft.Colors.GREY_800),
                ft.Row([self.btn_pick_file, self.txt_file_path], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=10),
                ft.Row([self.btn_start, self.progress_bar], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self.txt_status,
                self.log_container
            ],
            expand=True
        )

    def ui_log(self, message: str, is_error: bool = False):
        """Aggiunge un log locale alla ListView del massivo e nel log globale di app."""
        color = ft.Colors.RED_400 if is_error else ft.Colors.GREEN_400
        self.log_list.controls.append(ft.Text(message, color=color, font_family="Consolas", size=12))
        self.app.log(message, level="ERROR" if is_error else "INFO")
        self.update()

    def open_file_picker(self, e):
        self.file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["xlsx"],
            dialog_title="Seleziona il Template Excel di Creazione"
        )

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            self.selected_filepath = e.files[0].path
            self.txt_file_path.value = os.path.basename(self.selected_filepath)
            self.txt_file_path.color = ft.Colors.GREEN_300
            self.btn_start.disabled = False
            self.ui_log(f"File caricato in memoria: {self.selected_filepath}")
        else:
            self.selected_filepath = None
            self.txt_file_path.value = "Nessun file selezionato"
            self.txt_file_path.color = ft.Colors.GREY_500
            self.btn_start.disabled = True
        self.update()

    def start_massive_import(self, e):
        if not self.selected_filepath:
            return
            
        api_key = self.app.config.get("api_key", "")
        if not api_key:
            self.ui_log("ERRORE CRITICO: API Key mancante. Vai in Impostazioni per configurarla.", is_error=True)
            return

        # Lock UI
        self.btn_start.disabled = True
        self.btn_pick_file.disabled = True
        self.progress_bar.value = 0
        self.progress_bar.visible = True
        self.txt_status.value = "Analisi del file Excel in corso..."
        self.update()

        # Fire and forget nel thread
        threading.Thread(target=self._process_excel, args=(api_key,), daemon=True).start()

    def _process_excel(self, api_key: str):
        try:
            wb = openpyxl.load_workbook(self.selected_filepath, data_only=True)
            sheet = wb.active

            # Estrai l'header dalla prima riga
            headers = [str(cell.value).strip() if cell.value else "" for cell in sheet[1]]
            
            # Verifica base che l'header contenga almeno la colonna 'name'
            if "name" not in headers:
                self.ui_log("ERRORE: Il file Excel non contiene la colonna 'name'. Template non valido.", is_error=True)
                self._unlock_ui("Operazione annullata.")
                return

            # Contiamo le righe valide (saltiamo la prima riga di header)
            valid_rows = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                # Se la cella 'name' (prima colonna di solito, ma cerchiamo l'indice corretto) è vuota, fermiamo la lettura
                row_dict = dict(zip(headers, row))
                if not row_dict.get("name"):
                    continue
                    
                # Convertiamo tutti i valori in stringhe (come si aspetta sat_service)
                stringified_dict = {k: str(v).strip() if v is not None else "" for k, v in row_dict.items() if k}
                valid_rows.append(stringified_dict)

            total_cis = len(valid_rows)
            if total_cis == 0:
                self.ui_log("Nessun dato valido trovato nel file Excel.", is_error=True)
                self._unlock_ui("File vuoto.")
                return

            self.ui_log(f"Inizio elaborazione massiva: {total_cis} CI rilevati.")
            
            success_count = 0
            error_count = 0

            # Iterazione e chiamata API
            for i, snapshot in enumerate(valid_rows):
                ci_name = snapshot.get("name", "Sconosciuto")
                self.ui_log(f"[{i+1}/{total_cis}] Creazione in corso: {ci_name} ...")
                
                # Inoltro a sat_service
                res = sat_service.create_ci(api_key, snapshot)
                
                if res.get("success"):
                    self.ui_log(f" ✅ SUCCESSO: {ci_name} creato correttamente.")
                    success_count += 1
                else:
                    err_msg = res.get("message", "Errore sconosciuto")
                    details = " | ".join(res.get("errors", []))
                    self.ui_log(f" ❌ ERRORE: {ci_name} - {err_msg} -> {details}", is_error=True)
                    error_count += 1

                # Update progress
                self.progress_bar.value = (i + 1) / total_cis
                self.app.page.update()

            # Aggiornamento Statistiche nel Config
            current_stats = self.app.config.get("stats", {})
            current_stats["ci_massivi_ok"] = current_stats.get("ci_massivi_ok", 0) + success_count
            current_stats["ci_ko"] = current_stats.get("ci_ko", 0) + error_count
            self.app.config["stats"] = current_stats
            config.save_app_config(self.app.config)

            # Fine del job
            final_msg = f"Job completato. Successi: {success_count}, Errori: {error_count}"
            self.ui_log(final_msg)
            self._unlock_ui(final_msg)

        except Exception as e:
            self.ui_log(f"ERRORE CRITICO THREAD: {str(e)}", is_error=True)
            self._unlock_ui("Processo interrotto da un errore di sistema.")

    def _unlock_ui(self, status_msg: str):
        self.btn_start.disabled = False
        self.btn_pick_file.disabled = False
        self.progress_bar.visible = False
        self.txt_status.value = status_msg
        self.app.page.update()