import flet as ft
import urllib.request
import json
import threading
import time
import os
import sys
import subprocess
import zipfile
import shutil
import tempfile

def create_update_banner(page: ft.Page, current_version: str, version_url: str):
    """
    Creates an update banner and returns it along with a function to start the update check.
    Checks against a remote JSON file for updates.
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

    def download_and_install(download_url: str):
        if not getattr(sys, 'frozen', False):
            # If running from source, just open the browser
            page.launch_url(download_url)
            return

        try:
            update_action_button.disabled = True
            update_action_button.text = "Downloading..."
            progress_bar.visible = True
            page.update()

            # 1. Download the file
            temp_dir = tempfile.mkdtemp()
            # We don't know the filename yet, will determine from headers or default
            
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = (block_num * block_size) / total_size
                    progress_bar.value = percent
                    page.update()

            # Custom download with headers
            req = urllib.request.Request(download_url)
            req.add_header('User-Agent', 'Automeldung-App')

            with urllib.request.urlopen(req) as response:
                # Try to get filename from header
                content_disposition = response.getheader('Content-Disposition')
                filename = "update.exe" # Default
                if content_disposition:
                    # filename="Automeldung.exe"
                    import re
                    fname = re.findall(r'filename="?([^"]+)"?', content_disposition)
                    if fname:
                        filename = fname[0]
                
                download_path = os.path.join(temp_dir, filename)
                
                total_size = int(response.getheader('Content-Length', 0))
                block_size = 8192
                downloaded = 0
                
                with open(download_path, 'wb') as out_file:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        downloaded += len(buffer)
                        out_file.write(buffer)
                        report_progress(0, downloaded, total_size)

            update_action_button.text = "Installing..."
            page.update()

            # 2. Extract if zip
            new_exe_path = None
            if filename.endswith(".zip"):
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find the .exe in the extracted files
                current_exe_name = os.path.basename(sys.executable)
                
                # Search recursively for the exe
                for root, dirs, files in os.walk(temp_dir):
                    if current_exe_name in files:
                        new_exe_path = os.path.join(root, current_exe_name)
                        break
                    # Fallback: look for any exe if exact match not found
                    for f in files:
                        if f.endswith(".exe"):
                            new_exe_path = os.path.join(root, f)
                            break
                    if new_exe_path: break
            else:
                # Assume it's the exe itself
                new_exe_path = download_path

            if not new_exe_path or not os.path.exists(new_exe_path):
                raise Exception("Could not find executable in update.")

            # 3. Rename current exe and move new one
            current_exe = sys.executable
            old_exe = current_exe + ".old"
            
            if os.path.exists(old_exe):
                try:
                    os.remove(old_exe)
                except:
                    pass # Might be locked, ignore

            os.rename(current_exe, old_exe)
            shutil.move(new_exe_path, current_exe)

            # 4. Restart
            update_action_button.text = "Restarting..."
            page.update()
            
            subprocess.Popen([current_exe] + sys.argv[1:])
            os._exit(0)

        except Exception as e:
            print(f"Update failed: {e}")
            update_action_button.disabled = False
            update_action_button.text = "Retry Update"
            progress_bar.visible = False
            page.snack_bar = ft.SnackBar(ft.Text(f"Update failed: {e}"))
            page.snack_bar.open = True
            page.update()

    def check_loop():
        time.sleep(0.5) # Give the UI a moment to render
        try:
            # 1. Fetch the version info from JSON URL
            req = urllib.request.Request(version_url, headers={'User-Agent': 'Automeldung-App'})
            
            with urllib.request.urlopen(req, timeout=10) as url:
                data = json.loads(url.read().decode())
            
            remote_version = data.get("version", "0.0.0")
            download_url = data.get("download_url", "")
            
            # 2. Compare versions
            # Helper to convert "1.0.0" to (1, 0, 0) for comparison
            def to_tuple(v):
                return tuple(map(int, (v.split("."))))

            if to_tuple(remote_version) > to_tuple(current_version):
                print(f"Update found: v{remote_version}")
                
                # Update banner content
                update_info_text.value = f"Version {remote_version} is available. You have v{current_version}."
                
                # If running from source, we can't self-update easily, so keep the link behavior
                if getattr(sys, 'frozen', False):
                    update_action_button.text = "Update Now"
                    update_action_button.on_click = lambda e: threading.Thread(target=download_and_install, args=(download_url,), daemon=True).start()
                else:
                    update_action_button.text = "Download"
                    update_action_button.on_click = lambda e: page.launch_url(download_url) # Always open release page in dev
                
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
