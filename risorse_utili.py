# ============================================================================
# risorse_utili.py
# Modulo SAT per la gestione dei preferiti e link utili (NotebookLM, Docs, ecc.)
# ============================================================================

import flet as ft
import webbrowser
import config

class RisorseUtiliView(ft.Container):
    def __init__(self, app_context):
        super().__init__(expand=True, padding=30)
        self.app = app_context
        self.build_ui()

    def build_ui(self):
        # --- HEADER ---
        self.btn_add = ft.ElevatedButton(
            "Nuova Risorsa",
            icon=ft.Icons.ADD,
            on_click=self.show_add_dialog,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
        )

        header = ft.Row(
            controls=[
                ft.Column([
                    ft.Text("Risorse Utili", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                    ft.Text("Gestisci i collegamenti rapidi a documentazioni, linee guida e tool esterni.", color=ft.Colors.GREY_400),
                ]),
                self.btn_add
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # --- CONTENITORE LISTA ---
        self.bookmarks_grid = ft.Row(wrap=True, spacing=20, run_spacing=20)
        
        # Renderizza i bookmark iniziali SENZA chiamare self.update()
        self.render_bookmarks()

        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                header,
                ft.Divider(height=40, color=ft.Colors.GREY_800),
                self.bookmarks_grid
            ]
        )

    # =========================================================================
    # RENDER E LOGICA RISORSE
    # =========================================================================
    def render_bookmarks(self):
        """Ricostruisce la griglia basandosi sul config. Non esegue MAI update grafici."""
        self.bookmarks_grid.controls.clear()
        
        # Recupera la lista dal config in RAM
        risorse = self.app.config.get("risorse_utili", [])

        if not risorse:
            self.bookmarks_grid.controls.append(
                ft.Text("Nessuna risorsa configurata. Aggiungine una!", color=ft.Colors.GREY_500, italic=True)
            )
            return

        for index, item in enumerate(risorse):
            label = item.get("label", "Senza Titolo")
            url = item.get("url", "#")

            # Costruzione della Card per ogni risorsa
            card = ft.Card(
                elevation=4,
                content=ft.Container(
                    bgcolor=ft.Colors.GREY_900,
                    width=350,
                    padding=15,
                    border=ft.border.all(1, ft.Colors.GREY_800),
                    border_radius=8,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.BOOKMARK, color=ft.Colors.BLUE_400),
                            ft.Text(label, weight=ft.FontWeight.BOLD, size=16, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=ft.Colors.RED_400,
                                tooltip="Rimuovi",
                                on_click=lambda e, idx=index: self.delete_bookmark(idx)
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(url, size=12, color=ft.Colors.GREY_500, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Container(height=5),
                        ft.ElevatedButton(
                            "Apri nel Browser",
                            icon=ft.Icons.OPEN_IN_NEW,
                            on_click=lambda e, link=url: webbrowser.open_new_tab(link),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_800, color=ft.Colors.WHITE)
                        )
                    ])
                )
            )
            self.bookmarks_grid.controls.append(card)

    def delete_bookmark(self, index):
        """Elimina la risorsa, aggiorna il file JSON e ridisegna la UI."""
        risorse = self.app.config.get("risorse_utili", [])
        if 0 <= index < len(risorse):
            rimossa = risorse.pop(index)
            self.app.config["risorse_utili"] = risorse
            config.save_app_config(self.app.config)
            self.app.log(f"Risorsa rimossa: {rimossa.get('label')}")
            
            # Ricostruisce la lista e forza l'aggiornamento grafico
            self.render_bookmarks()
            self.update()

    # =========================================================================
    # DIALOG INSERIMENTO NUOVA RISORSA
    # =========================================================================
    def show_add_dialog(self, e):
        self.entry_label = ft.TextField(label="Nome Risorsa (es. Linee Guida Ark)", autofocus=True)
        self.entry_url = ft.TextField(label="URL (es. https://...)")
        self.txt_dialog_err = ft.Text("", color=ft.Colors.RED_400, size=12)

        self.add_dialog = ft.AlertDialog(
            title=ft.Text("Aggiungi Nuova Risorsa"),
            content=ft.Column([self.entry_label, self.entry_url, self.txt_dialog_err], tight=True, spacing=10),
            actions=[
                ft.TextButton("Annulla", on_click=self.close_add_dialog),
                ft.ElevatedButton("Salva", on_click=self.save_new_bookmark, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=8),
            bgcolor=ft.Colors.GREY_900
        )
        self.app.page.show_dialog(self.add_dialog)

    def close_add_dialog(self, e=None):
        if hasattr(self.app.page, "close_dialog"):
            self.app.page.close_dialog()
        else:
            self.add_dialog.open = False
            self.app.page.update()

    def save_new_bookmark(self, e):
        """Salva la nuova risorsa, aggiorna il JSON e ridisegna la UI."""
        label = self.entry_label.value.strip()
        url = self.entry_url.value.strip()

        if not label or not url:
            self.txt_dialog_err.value = "Entrambi i campi sono obbligatori."
            self.add_dialog.update()
            return

        if not url.startswith("http://") and not url.startswith("https://"):
            self.txt_dialog_err.value = "L'URL deve iniziare con http:// o https://"
            self.add_dialog.update()
            return

        # Aggiorna in RAM e salva su disco
        self.app.config.setdefault("risorse_utili", []).append({"label": label, "url": url})
        config.save_app_config(self.app.config)
        
        self.app.log(f"Nuova risorsa aggiunta: {label}")
        
        self.close_add_dialog()
        
        # Ricostruisce la lista e forza l'aggiornamento grafico
        self.render_bookmarks()
        self.update()