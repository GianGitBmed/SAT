# te210h.py
import flet as ft
from assets import TE210_BASE64

class TE210HunterView(ft.Container):
    def __init__(self, app_context):
        super().__init__(expand=True, padding=30)
        self.app = app_context
        self.build_ui()

    def build_ui(self):
        # --- SEZIONE TESTO ---
        testo_header = ft.Column([
            ft.Text("TE210 Hunter", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
            ft.Text("Funzionalità in fase di ragionamento...", size=18, color=ft.Colors.GREY_400),
            ft.Divider(height=40, color=ft.Colors.GREY_800),
        ])

        # --- SEZIONE IMMAGINE (FIX DATA URI per Flet 0.84+) ---
        image_row = ft.Row(
            controls=[
                ft.Image(
                    src=f"data:image/png;base64,{TE210_BASE64}",
                    width=400, # Aumentata un po' per visibilità
                    fit="contain", # <-- Usiamo la stringa, compatibile con tutte le versioni
                    border_radius=ft.border_radius.all(10),
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )

        # Layout Globale
        self.content = ft.Column(
            expand=True,
            controls=[
                testo_header,
                ft.Container(height=20), # Spazio
                image_row
            ],
            scroll=ft.ScrollMode.AUTO
        )