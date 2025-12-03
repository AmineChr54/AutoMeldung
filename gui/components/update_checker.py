import flet as ft
import requests
import os
import sys
import subprocess
import logging
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_update_banner(page: ft.Page, current_version: str, update_url: str):
    """
    Creates an update banner with modern styling.
    """
    update_container = ft.Container(visible=False)
    
    # UI Elements with improved styling
    update_icon = ft.Icon(ft.Icons.SYSTEM_UPDATE, color=ft.Colors.GREEN_400, size=24)
    update_text = ft.Text("Checking for updates...", size=14, weight=ft.FontWeight.W_500)
    status_text = ft.Text("", size=12, color=ft.Colors.GREY_400, italic=True)
    
    def start_update(e):
        """Triggers the update process via Launcher.exe"""
        update_btn.disabled = True
        update_btn.text = "Starting..."
        status_text.value = "⏳ Please close this window for the update to start."
        status_text.color = ft.Colors.AMBER_400
        page.update()

        try:
            # Determine launcher path
            launcher_exe = "Launcher.exe"
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
                launcher_path = os.path.join(base_dir, launcher_exe)
            else:
                # Dev mode: assume launcher.py is in project root
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                launcher_path = os.path.join(base_dir, "launcher.py")

            logger.info(f"Launching updater: {launcher_path}")

            # Hide console window on Windows
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            if getattr(sys, 'frozen', False):
                if os.path.exists(launcher_path):
                    subprocess.Popen([launcher_path, "--install-update"], startupinfo=startupinfo)
                else:
                    raise FileNotFoundError(f"Launcher not found at {launcher_path}")
            else:
                # Run python launcher.py
                subprocess.Popen([sys.executable, launcher_path, "--install-update"], startupinfo=startupinfo)

            # Update UI to inform user
            update_text.value = "Update ready!"
            update_icon.name = ft.Icons.CHECK_CIRCLE
            update_icon.color = ft.Colors.GREEN_400
            update_btn.visible = False
            status_text.value = "✕ Please close this window now for the update to install."
            status_text.color = ft.Colors.GREEN_400
            status_text.weight = ft.FontWeight.BOLD
            page.update()

        except Exception as ex:
            logger.error(f"Failed to start launcher: {ex}")
            status_text.value = f"❌ Error: {ex}"
            status_text.color = ft.Colors.RED_400
            update_btn.disabled = False
            update_btn.text = "Retry Update"
            page.update()

    update_btn = ft.ElevatedButton(
        "Update Now",
        icon=ft.Icons.DOWNLOAD,
        on_click=start_update,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN_700,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
        ),
        visible=False
    )

    # Layout with better styling
    content = ft.Column([
        ft.Row([
            update_icon,
            ft.Column([
                update_text,
                status_text,
            ], spacing=2, expand=True),
            update_btn,
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
    ], spacing=4)
    
    update_container.content = ft.Container(
        content=content,
        padding=ft.padding.all(16),
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN_400),
        border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.GREEN_400)),
        border_radius=10,
    )

    def check_for_updates():
        """Checks version.json on the server."""
        # If launched with --update-available, show banner immediately
        if os.environ.get("UPDATE_AVAILABLE") == "1":
            update_text.value = "🎉 New version available!"
            update_btn.visible = True
            update_container.visible = True
            page.update()
            return

        # Otherwise, check manually (e.g. if app is left open)
        try:
            version_url = update_url.rstrip("/") + "/version.json"
            logger.info(f"Checking for updates at {version_url}")
            
            resp = requests.get(version_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                latest_version = data.get("version")
                
                if latest_version != current_version:
                    logger.info(f"Update found: {latest_version}")
                    update_text.value = f"🎉 New version {latest_version} available!"
                    update_btn.visible = True
                    update_container.visible = True
                    page.update()
                else:
                    logger.info("App is up to date.")
            else:
                logger.warning(f"Could not check updates. Status: {resp.status_code}")
        except Exception as e:
            logger.error(f"Update check failed: {e}")

    return update_container, check_for_updates

