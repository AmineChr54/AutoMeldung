import flet as ft
import os
import sys
import update_config


# Ensure project root is on sys.path so `import automeldung...` works when running from gui/
if getattr(sys, 'frozen', False):
    # Running as compiled EXE
    PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    # Running from source
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

from gui.utils.settings import load_settings
from gui.components.inputs import create_inputs_section
from gui.components.export import create_export_section
from gui.components.status import create_status_section
from gui.components.update_checker import create_update_banner
from gui.logic.runner import setup_runner

def cleanup_old_executable():
    """Removes the .old file left behind by the update process."""
    if getattr(sys, 'frozen', False):
        old_exe = sys.executable + ".old"
        if os.path.exists(old_exe):
            try:
                os.remove(old_exe)
                print(f"Removed old version: {old_exe}")
            except Exception as e:
                print(f"Could not remove old version: {e}")

def main(page: ft.Page):
    # Cleanup any old executable from a previous update
    cleanup_old_executable()

    # Page setup
    page.title = "Automeldung — PDF Automation"
    
    # ----- App Versioning -----
    CURRENT_VERSION = update_config.CURRENT_VERSION
    VERSION_URL = update_config.VERSION_URL

    page.padding = 8
    page.window.width = 859
    page.window.height = 539
    page.theme_mode = "dark"

    # Load settings
    settings = load_settings()
    # Reset creation_date on startup so it doesn't persist
    settings["creation_date"] = ""

    # Create components
    inputs_card, input_refs = create_inputs_section(page, settings)
    export_card, export_refs = create_export_section(page, settings)
    status_card, status_refs = create_status_section()
    update_banner, start_update_check = create_update_banner(page, CURRENT_VERSION, VERSION_URL)

    # Setup logic
    setup_runner(page, settings, input_refs, export_refs, status_refs)

    # Layout
    header = ft.Row([
        ft.Icon(ft.Icons.DESCRIPTION, color=ft.Colors.BLUE_400),
        ft.Column([
            ft.Text("Automeldung – PDF Automation", style=ft.TextThemeStyle.HEADLINE_MEDIUM, size=20),
            ft.Text(f"v{CURRENT_VERSION}", size=10, color=ft.Colors.GREY_500)
        ], spacing=0),
        ft.Container(expand=True),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    content_column = ft.Column(
        controls=[
            header,
            ft.Divider(),
            update_banner, # Add banner here
            ft.ResponsiveRow([
                ft.Column([inputs_card], col={'sm': 12, 'md': 12, 'lg': 6}),
                ft.Column([export_card], col={'sm': 12, 'md': 12, 'lg': 6}),
                ft.Column([status_card], col={'sm': 12, 'md': 12, 'lg': 12}),
            ], columns=12, run_spacing=12, spacing=12),
            ft.Container(content=ft.Text("Automeldung", color=ft.Colors.GREY), padding=8, alignment=ft.alignment.center_right),
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    page.add(content_column)
    
    # Run update check in a background thread to avoid blocking the UI
    start_update_check()

if __name__ == "__main__":
    ft.app(target=main)
