import flet as ft
import config
import datetime

class SATApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.ciometro_expanded = False  # Stato del sottomenu
        self.config = config.load_app_config()
        self.local_db = config.load_local_db()

        self.setup_window()
        self.setup_services()
        self.build_layout()
# =========================================================
    # INSERISCI QUI I DUE METODI (ATTENZIONE AGLI SPAZI!)
    # =========================================================
    def load_nuovo_ci(self, e):
        self.floating_menu.visible = False # Chiudi il menu fluttuante
        from ciometro import CiometroView
        self.work_area.content = CiometroView(self)
        self.log("Navigazione: Modulo 'Nuovo CI' caricato.")
        self.page.update()

    def load_ci_esistenti(self, e):
        self.floating_menu.visible = False # Chiudi il menu fluttuante
        from ci_esistenti import CiEsistentiView
        self.work_area.content = CiEsistentiView(self)
        self.log("Navigazione: Modulo 'CI Esistenti' caricato.")
        self.page.update()
    # =========================================================
    def setup_services(self):
        try:
            self.file_picker = ft.FilePicker()
        except Exception as e:
            self.file_picker = None
            self.log(f"FilePicker non disponibile: {e}")

    def setup_window(self):
        app_name = self.config.get("app_settings", {}).get("name", "SAT")
        app_ver = self.config.get("app_settings", {}).get("version", "3.1")

        self.page.title = "SAT - Solution Architect Tool v3.1"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.width = 1500
        self.page.window.height = 1000
        self.page.padding = 0
        self.page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    def get_rail_destinations(self):
        """Genera dinamicamente le voci del menu in base allo stato di espansione."""
        dests = [
            ft.NavigationRailDestination(
                icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Panoramica"
            ),
            ft.NavigationRailDestination(
                    icon=ft.Icons.BOOKMARK, # <-- Nuova icona (vuota)
                    selected_icon=ft.Icons.BOOKMARK, # <-- Nuova icona (piena quando selezionata)
                    label="CIometro"
                ),
        ]



        # Aggiungiamo le restanti voci che slitteranno in basso
        dests.extend([
            ft.NavigationRailDestination(
                icon=ft.Icons.SEARCH_OUTLINED, selected_icon=ft.Icons.SEARCH, label="TE210 Hunter"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.BOOKMARK_BORDER, selected_icon=ft.Icons.BOOKMARK, label="Risorse utili"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Impostazioni"
            ),
        ])
        return dests
    def build_layout(self):
        # 1. Menu Laterale Pulito (Originale)
        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Panoramica"),
                ft.NavigationRailDestination(icon=ft.Icons.SWITCH_ACCESS_SHORTCUT_ADD_SHARP, selected_icon=ft.Icons.SWITCH_ACCESS_SHORTCUT_ADD, label="CIometro"),
                ft.NavigationRailDestination(icon=ft.Icons.CONTENT_PASTE_SEARCH, selected_icon=ft.Icons.CONTENT_PASTE_GO, label="TE210 Hunter"),
                ft.NavigationRailDestination(icon=ft.Icons.BOOKMARK_BORDER, selected_icon=ft.Icons.BOOKMARK, label="Risorse utili"),
                ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Impostazioni"),
            ],
            on_change=self.on_nav_change,
        )

        self.work_area = ft.Container(expand=True, alignment=ft.Alignment.TOP_LEFT)

        from panoramica import PanoramicaView
        self.work_area.content = PanoramicaView(self)

        self.terminal_list = ft.ListView(expand=True, spacing=2, auto_scroll=True)
        self.terminal_container = ft.Container(
            content=self.terminal_list, height=200, bgcolor=ft.Colors.BLACK,
            border=ft.border.all(1, ft.Colors.GREY_800), border_radius=ft.border_radius.only(top_left=8, top_right=8),
            padding=10, margin=ft.margin.only(top=10, left=10, right=10),
            visible=False
        )

        right_column = ft.Column(
            controls=[self.work_area, self.terminal_container],
            expand=True, spacing=0
        )

        # --- IL NUOVO MENU FLUTTUANTE ---
        self.floating_menu = ft.Container(
            content=ft.Column([
                ft.TextButton("Nuovo CI", icon=ft.Icons.ADD_BOX, on_click=self.load_nuovo_ci, 
                              style=ft.ButtonStyle(color=ft.Colors.WHITE, padding=15, shape=ft.RoundedRectangleBorder(radius=5))),
                ft.TextButton("CI Esistenti", icon=ft.Icons.LIBRARY_BOOKS, on_click=self.load_ci_esistenti, 
                              style=ft.ButtonStyle(color=ft.Colors.WHITE, padding=15, shape=ft.RoundedRectangleBorder(radius=5))),
            ], tight=True, spacing=5),
            bgcolor=ft.Colors.GREY_900,
            border=ft.border.all(1, ft.Colors.GREY_700),
            border_radius=8,
            padding=10,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.BLACK54),
            # Coordinate assolute per posizionarlo accanto all'icona CIometro
            left=105, 
            top=90,  
            visible=False # Nasce invisibile
        )

        # 2. Struttura base della pagina
        main_layout = ft.Row(
            controls=[self.rail, ft.VerticalDivider(width=1), right_column],
            expand=True, spacing=0
        )

        # 3. Stack per permettere la sovrapposizione del menu fluttuante
        self.page.add(
            ft.Stack(
                controls=[main_layout, self.floating_menu],
                expand=True
            )
        )
        
        self.log("Sistema SAT Inizializzato. Terminale pronto.")

    def on_nav_change(self, e):
        idx = e.control.selected_index

        # Gestione visibilità Terminale
        self.terminal_container.visible = (idx != 0)

        # Nascondiamo sempre il menu fluttuante di default ad ogni click...
        self.floating_menu.visible = False

        if idx == 0:
            from panoramica import PanoramicaView
            self.work_area.content = PanoramicaView(self)
            self.log("Navigazione: Modulo Panoramica caricato.")
            
        elif idx == 1:
            # ...tranne se cliccano su CIometro: in tal caso lo mostriamo!
            self.floating_menu.visible = True
            self.log("Navigazione: Menu CIometro aperto in sovraimpressione.")
            
            
        elif idx == 2:
            # Caricamento nuovo modulo TE210 Hunter
            from te210h import TE210HunterView
            self.work_area.content = TE210HunterView(self)
            self.log("Navigazione: Modulo TE210 Hunter caricato.")
            
        elif idx == 3:
            from risorse_utili import RisorseUtiliView
            self.work_area.content = RisorseUtiliView(self)
            self.log("Navigazione: Modulo Risorse caricato.")
            
        elif idx == 4:
            from settings import SettingsView
            self.work_area.content = SettingsView(self.work_area, self)
            self.log("Navigazione: Modulo Impostazioni caricato.")

        self.page.update()

    def log(self, message: str, level: str = "INFO"):
        """Scrive nel terminale GUI, nella console standard e su file log.txt"""
        verbosity_level = self.config.get("verbosity", "INFO")
        
        levels = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
        curr_lvl = levels.get(level, 20)
        max_lvl = levels.get(verbosity_level, 20)
        
        if curr_lvl < max_lvl:
            return

        # Millisecondi utilissimi per calcolare i colli di bottiglia e latenze GUI
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}] [{level}] {message}"
        print(f"[SAT LOG] {log_line}")
        
        # Log sempre su file
        try:
            with open("log.txt", "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except Exception:
            pass
        
        color = ft.Colors.GREEN_400
        if level == "ERROR":
            color = ft.Colors.RED_400
        elif level == "WARN":
            color = ft.Colors.AMBER_400
        elif level == "DEBUG":
            color = ft.Colors.BLUE_GREY_400

        if hasattr(self, 'terminal_list'):
            self.terminal_list.controls.append(
                ft.Text(log_line, color=color, font_family="Consolas", size=12)
            )
            # Auto-scroll terminale
            try:
                self.page.update()
            except Exception:
                pass