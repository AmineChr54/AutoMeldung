import flet as ft
import os
import sys
import logging
import json
import urllib.request
import subprocess
import update_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_update_banner(page: ft.Page, current_version: str, version_url: str):
    """
    Creates an update banner and returns it along with a function to start the update check.
    Uses a simple "Download and Swap" mechanism.
    """
    update_info_text = ft.Text("A new version is available!", size=14)
    
    # Progress bar for download
    progress_bar = ft.ProgressBar(width=200, visible=False)
    
    update_action_button = ft.ElevatedButton(
        "Update Now", 
        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_600)
    )
    
    update_banner = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.NEW_RELEASES, color=ft.Colors.AMBER),
                ft.Column([
                    ft.Text("Update Available", weight=ft.FontWeight.BOLD),
                    update_info_text,
                    progress_bar
                ], spacing=2),
            ]),
            update_action_button
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.AMBER),
        border=ft.border.all(1, ft.Colors.AMBER),
        border_radius=8,
        padding=12,
        visible=False, # Initially hidden
        margin=ft.margin.only(bottom=10)
    )

    # State to hold the download URL found during check
    update_state = {"download_url": None, "new_version": None}

    def check_for_updates():
        """Fetches version.json from the server and compares versions."""
        try:
            # Construct URL for version.json
            # Assumes UPDATE_URL points to a folder like ".../updates/"
            base_url = update_config.UPDATE_URL.rstrip('/')
            json_url = f"{base_url}/version.json"
            
            logger.info(f"Checking for updates at: {json_url}")
            
            with urllib.request.urlopen(json_url, timeout=5) as response:
                data = json.loads(response.read().decode())
                
            latest_version = data.get("version")
            download_url = data.get("url")
            
            logger.info(f"Server version: {latest_version}, Current: {current_version}")

            if latest_version and latest_version != current_version:
                # Simple string comparison. For robust semver, use packaging.version
                update_state["new_version"] = latest_version
                update_state["download_url"] = download_url
                
                # Update UI
                update_info_text.value = f"Version {latest_version} is available."
                update_action_button.text = "Update Now"
                update_action_button.on_click = perform_update
                update_banner.visible = True
                page.update()
            else:
                logger.info("App is up to date.")

        except Exception as e:
            logger.error(f"Update check failed: {e}")

    def perform_update(e):
        """Downloads the new exe and runs the batch swapper."""
        download_url = update_state["download_url"]
        if not download_url:
            return

        # If running from source, just open the URL
        if not getattr(sys, 'frozen', False):
            page.launch_url(download_url)
            return

        try:
            # UI Feedback
            update_action_button.disabled = True
            update_action_button.content = ft.Row(
                [ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE),
                 ft.Text("Downloading...", color=ft.Colors.WHITE)],
                alignment=ft.MainAxisAlignment.CENTER,
            )
            progress_bar.visible = True
            page.update()

            # 1. Determine paths
            current_exe = sys.executable
            exe_dir = os.path.dirname(current_exe)
            new_exe_path = os.path.join(exe_dir, "AutoMeldung.new")
            bat_path = os.path.join(exe_dir, "update.bat")

            # 2. Download the new file
            logger.info(f"Downloading update from {download_url}...")
            urllib.request.urlretrieve(download_url, new_exe_path, reporthook=report_progress)

            # 3. Create Batch Script to swap files
            # The script waits 2 seconds, deletes the old exe, renames the new one, and restarts it.
            batch_script = f"""
@echo off
timeout /t 2 /nobreak > NUL
del "{current_exe}"
move "{new_exe_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
            with open(bat_path, "w") as f:
                f.write(batch_script)

            # 4. Run the batch script and exit
            logger.info("Starting update script and exiting...")
            subprocess.Popen([bat_path], shell=True)
            page.window_close()
            sys.exit(0)

        except Exception as ex:
            logger.error(f"Update failed: {ex}")
            update_action_button.disabled = False
            update_action_button.content = None
            update_action_button.text = "Retry"
            progress_bar.visible = False
            page.snack_bar = ft.SnackBar(ft.Text(f"Update failed: {ex}"))
            page.snack_bar.open = True
            page.update()

    def report_progress(block_num, block_size, total_size):
        if total_size > 0:
            percent = (block_num * block_size) / total_size
            if percent > 1.0: percent = 1.0
            progress_bar.value = percent
            page.update()

    def start_check():
        # Run in a thread to not block UI
        import threading
        threading.Thread(target=check_for_updates, daemon=True).start()

    return update_banner, start_check