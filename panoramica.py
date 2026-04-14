# panoramica.py
import flet as ft

# Assicurati che assets.py esista nella stessa cartella e contenga LOGO_BASE64
from assets import LOGO_BASE64

class PanoramicaView(ft.Container):
    def __init__(self, app_context):
        super().__init__(expand=True, padding=30)
        self.app = app_context
        self.build_ui()

    def create_stat_card(self, title: str, value: str, icon: str, color: str):
        return ft.Card(
            elevation=4,
            content=ft.Container(
                bgcolor=ft.Colors.GREY_900, 
                padding=20,
                width=280,
                border_radius=ft.border_radius.all(10), # Bordo arrotondato
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, color=color, size=30),
                        ft.Text(title, size=16, color=ft.Colors.GREY_400, weight=ft.FontWeight.W_500)
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ])
            )
        )

    def build_ui(self):
        # 1. Recupero Dati Configurazione
        app_ver = self.app.config.get("app_settings", {}).get("version", "2.1")
        stats = self.app.config.get("stats", {})
        
        # 2. Recupero Dati DB Locale (Conta chiavi)
        db = self.app.local_db
        db_stats = {
            "CI in Distinta": len(db.get("configuration_items", {})),
            "Domini": len(db.get("domains", {})),
            "Solution Designs": len(db.get("solution_designs", {})),
            "Teams": len(db.get("teams", {})),
            "Offices": len(db.get("offices", {})),
            "Building Blocks": len(db.get("bb_instances", {})),
            "App Modules": len(db.get("app_modules", {})),
            "Tecnologie": len(db.get("technologies", {}))
        }

        # --- SEZIONE LOGO ---
        # Rimuovendo l'altezza fissa, l'immagine prenderà la sua dimensione naturale
        # Adattandosi fluidamente fino ai margini del contenitore
        from assets import LOGO_BASE64
        logo_row = ft.Row(
            [ft.Image(src=f"data:image/png;base64,{LOGO_BASE64}")],
            alignment=ft.MainAxisAlignment.CENTER,
            margin=ft.margin.only(bottom=10) 
        )

        # --- SEZIONE INFO APPLICATIVO (Senza Titolo Testuale) ---
        header_section = ft.Column([
            ft.Text(f"Versione: {app_ver}", size=16, color=ft.Colors.GREY_400),
            ft.Text(f"Ultima Sincronizzazione Master Data: {stats.get('last_sync', 'Mai effettuata')}", size=14, color=ft.Colors.GREEN_400 if "Mai" not in stats.get('last_sync', 'Mai') else ft.Colors.AMBER_400),
            ft.Divider(height=30, color=ft.Colors.GREY_800)
        ])

        # --- SEZIONE STATISTICHE DATABASE ---
        db_cards = ft.Row(wrap=True, spacing=15, run_spacing=15)
        
        db_cards.controls.append(self.create_stat_card("CI in Distinta", str(db_stats.pop("CI in Distinta")), ft.Icons.DNS, ft.Colors.BLUE_400))
        
        for k, v in db_stats.items():
            db_cards.controls.append(self.create_stat_card(k, str(v), ft.Icons.DATA_OBJECT, ft.Colors.CYAN_700))

        # --- SEZIONE STATISTICHE OPERATIVE (SAT TOOL) ---
        op_cards = ft.Row(wrap=True, spacing=15, run_spacing=15, controls=[
            self.create_stat_card("CI Censiti (Singoli)", str(stats.get('ci_singoli_ok', 0)), ft.Icons.ADD_TASK, ft.Colors.GREEN_500),
            self.create_stat_card("CI Censiti (Massivi)", str(stats.get('ci_massivi_ok', 0)), ft.Icons.LIBRARY_ADD, ft.Colors.PURPLE_400),
            self.create_stat_card("Errori / Fallimenti", str(stats.get('ci_ko', 0)), ft.Icons.WARNING_AMBER_ROUNDED, ft.Colors.RED_400)
        ])

        # Costruzione Layout Globale
        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                logo_row,
                header_section,
                ft.Text("Contenuto Database Locale (Cache)", size=20, weight=ft.FontWeight.BOLD),
                db_cards,
                ft.Divider(height=40, color=ft.Colors.GREY_800),
                ft.Text("Statistiche Operative SAT", size=20, weight=ft.FontWeight.BOLD),
                op_cards
            ]
        )