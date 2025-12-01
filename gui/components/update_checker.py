import flet as ft
import os
import sys
import logging
import shutil
import threading
import time
import subprocess
from tufup.client import Client
import update_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_update_banner(page: ft.Page, current_version: str, version_url: str):
    """
    Creates an update banner and returns it along with a function to start the update check.
    Uses tufup for secure updates.
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

    # --- Tufup Configuration ---
    APP_NAME = "AutoMeldung"
    # Use a local directory for metadata cache
    if getattr(sys, 'frozen', False):
        # Running as compiled EXE
        app_install_dir = os.path.dirname(sys.executable)
        # Store metadata in user data directory to avoid permission issues in Program Files
        metadata_dir = os.path.join(os.getenv('LOCALAPPDATA'), APP_NAME, 'metadata')
    else:
        # Running from source
        app_install_dir = os.path.dirname(os.path.abspath(__file__))
        metadata_dir = os.path.join(app_install_dir, 'metadata_cache')

    # Ensure metadata dir exists
    os.makedirs(metadata_dir, exist_ok=True)

    # URL for the TUF repository
    # update_config.UPDATE_URL should point to the folder containing 'metadata' and 'targets'
    METADATA_BASE_URL = f"{update_config.UPDATE_URL.rstrip('/')}/metadata/"
    TARGET_BASE_URL = f"{update_config.UPDATE_URL.rstrip('/')}/targets/"

    def get_tuf_client():
        # Ensure root.json exists in metadata_dir
        # In a real scenario, the initial root.json should be bundled with the app.
        # We look for it in the app's resources.
        root_json_path = os.path.join(metadata_dir, 'root.json')
        
        if not os.path.exists(root_json_path):
            # Try to find bundled root.json
            bundled_root = None
            if getattr(sys, 'frozen', False):
                # Look in sys._MEIPASS
                bundled_root = os.path.join(sys._MEIPASS, 'metadata', 'root.json')
            else:
                # Look in project root/tuf_repo/metadata/root.json (dev mode)
                # We are in gui/components/
                # Project root is ../../
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                possible_root = os.path.join(project_root, 'tuf_repo', 'metadata', 'root.json')
                if os.path.exists(possible_root):
                    bundled_root = possible_root
                    logger.info(f"Found dev root.json at {bundled_root}")
            
            if bundled_root and os.path.exists(bundled_root):
                logger.info(f"Copying root.json from {bundled_root} to {root_json_path}")
                shutil.copy(bundled_root, root_json_path)
            else:
                logger.warning("No bundled root.json found. Update check might fail if not initialized.")

        return Client(
            app_name=APP_NAME,
            app_install_dir=app_install_dir,
            current_version=current_version,
            metadata_dir=metadata_dir,
            metadata_base_url=METADATA_BASE_URL,
            target_dir=app_install_dir,
            target_base_url=TARGET_BASE_URL,
        )

    def perform_update(e):
        if not getattr(sys, 'frozen', False):
            page.launch_url(update_config.UPDATE_URL)
            return

        try:
            update_action_button.disabled = True
            update_action_button.content = ft.Row(
                [
                    ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE),
                    ft.Text("Updating...", color=ft.Colors.WHITE),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
            progress_bar.visible = True
            page.update()

            client = get_tuf_client()
            
            # Download and install update
            # tufup handles the secure download and verification
            client.download_and_apply_update(
                progress_hook=lambda bytes_downloaded, total_bytes: report_progress(bytes_downloaded, total_bytes)
            )

            update_action_button.content = ft.Row(
                [
                    ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE),
                    ft.Text("Restarting...", color=ft.Colors.WHITE),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
            page.update()

            # Restart the application
            # Tufup has moved the old exe to .old and the new one is in place.
            # We just need to restart.
            restart_app()

        except Exception as ex:
            logger.error(f"Update failed: {ex}")
            update_action_button.disabled = False
            update_action_button.content = None
            update_action_button.text = "Retry Update"
            progress_bar.visible = False
            page.snack_bar = ft.SnackBar(ft.Text(f"Update failed: {ex}"))
            page.snack_bar.open = True
            page.update()

    def report_progress(current, total):
        if total > 0:
            percent = current / total
            progress_bar.value = percent
            page.update()

    def restart_app():
        """Restart the current application."""
        logger.info("Restarting application...")
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def check_loop():
        time.sleep(1) # Wait for UI
        try:
            logger.info(f"Checking for updates from {METADATA_BASE_URL}")
            client = get_tuf_client()
            
            # Refresh metadata from server
            # logger.info("Refreshing metadata...")
            # client.refresh()
            
            # Check for updates
            logger.info("Checking for updates...")
            update_info = client.check_for_updates()
            
            if update_info:
                logger.info(f"Update found: {update_info}")
                update_info_text.value = f"New version available."
                
                update_action_button.text = "Update Now"
                update_action_button.on_click = perform_update
                
                update_banner.visible = True
                page.update()
            else:
                logger.info(f"No updates available. Current version: {current_version}")

        except Exception as e:
            logger.error(f"Update check failed: {e}", exc_info=True)
            # Don't show error to user in banner, just log it
            # Unless it's a critical error, but for updates, silent fail is often better

    def start_check():
        threading.Thread(target=check_loop, daemon=True).start()

    return update_banner, start_check