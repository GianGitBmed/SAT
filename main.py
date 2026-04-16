# main.py
import sys
import os
import traceback
import flet as ft

try:
    if sys.stdout is None: sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None: sys.stderr = open(os.devnull, 'w')
except Exception:
    pass

try:
    from app import SATApp

    def main(page: ft.Page):
        app = SATApp(page)

    if __name__ == "__main__":
        # Fix: In Flet 0.84+ la funzione va passata come argomento posizionale
        ft.run(main)

except Exception as e:
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"FATAL ERROR:\n{traceback.format_exc()}\n")