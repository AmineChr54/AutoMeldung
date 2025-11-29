import flet as ft
import urllib.request
import json
import threading
import time

def create_update_banner(page: ft.Page, current_version: str, update_url: str):
    """
    Creates an update banner and returns it along with a function to start the update check.
    """
    update_info_text = ft.Text("A new version is available!", size=14)
    update_action_button = ft.ElevatedButton(
        "Download", 
        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_600)
    )
    
    update_banner = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.NEW_RELEASES, color=ft.Colors.AMBER),
                ft.Column([
                    ft.Text("Update Available", weight=ft.FontWeight.BOLD),
                    update_info_text
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

    def check_loop():
        time.sleep(0.5) # Give the UI a moment to render
        try:
            # 1. Fetch the JSON from the cloud
            # Add a User-Agent just in case the server requires it
            req = urllib.request.Request(update_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as url:
                data = json.loads(url.read().decode())
            
            remote_version = data.get("version", "0.0.0")
            download_url = data.get("download_url", "")

            # 2. Compare versions
            if remote_version > current_version:
                print(f"Update found: v{remote_version}")
                
                # Update banner content
                update_info_text.value = f"Version {remote_version} is available. You have v{current_version}."
                update_action_button.on_click = lambda e: page.launch_url(download_url)
                
                # Show banner
                update_banner.visible = True
                page.update()
                print(f"Update banner shown for v{remote_version}")
            else:
                print(f"No update needed. Remote: {remote_version}, Local: {current_version}")

        except Exception as e:
            print(f"Update check failed: {e}")

    def start_check():
        threading.Thread(target=check_loop, daemon=True).start()

    return update_banner, start_check
