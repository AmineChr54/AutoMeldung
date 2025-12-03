"""
Launcher for AutoMeldung
========================
A simple, standalone launcher that:
1. Checks for updates on startup
2. Downloads and installs updates (when requested by the main app)
3. Launches the main application

This keeps the main app simple - it doesn't need to know how to update itself.
"""

import sys
import os
import subprocess
import time
import argparse
import requests
import logging
import hashlib

# Configure logging
logging.basicConfig(
    filename='launcher.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
APP_EXECUTABLE = "AutoMeldung.exe"

# Update URL - try to import, fallback to hardcoded
UPDATE_URL = None
try:
    import update_config
    UPDATE_URL = update_config.UPDATE_URL
except ImportError:
    pass

if not UPDATE_URL:
    UPDATE_URL = "https://aminechr54.github.io/AutoMeldung/updates/"


def get_main_app_command():
    """Determines the command to run the main app."""
    if os.path.exists(APP_EXECUTABLE):
        return [APP_EXECUTABLE]
    elif os.path.exists("gui/app.py"):
        return [sys.executable, "gui/app.py"]
    else:
        logging.error("Main application not found.")
        sys.exit(1)


def get_app_version():
    """Gets the version of the main application."""
    cmd = get_main_app_command() + ["--version"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
        return result.stdout.strip()
    except Exception as e:
        logging.error(f"Error getting app version: {e}")
        return None


def check_for_updates(current_version):
    """Checks for updates and returns update info if available."""
    if not current_version:
        return None
    
    try:
        version_url = UPDATE_URL.rstrip("/") + "/version.json"
        logging.info(f"Checking for updates at {version_url}")
        response = requests.get(version_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get("version")
            logging.info(f"Current: {current_version}, Latest: {latest_version}")
            if latest_version and latest_version != current_version:
                return {
                    "version": latest_version,
                    "sha256": data.get("sha256"),
                    "url": data.get("url")  # Optional direct URL
                }
    except Exception as e:
        logging.error(f"Update check failed: {e}")
    
    return None


def wait_for_app_to_close(max_wait=30):
    """Waits for the main app to close by checking file lock."""
    logging.info("Waiting for main app to close...")
    
    for i in range(max_wait):
        try:
            if os.path.exists(APP_EXECUTABLE):
                # Try to open for exclusive write access
                with open(APP_EXECUTABLE, "a+b") as f:
                    pass
            logging.info("App file is accessible.")
            return True
        except PermissionError:
            logging.info(f"App still running. Retrying {i+1}/{max_wait}...")
            time.sleep(1)
        except Exception as e:
            logging.warning(f"Error checking file lock: {e}")
            time.sleep(1)
    
    logging.error("Timed out waiting for app to close.")
    return False


def download_update(sha256_expected=None):
    """Downloads the new executable from the server."""
    exe_url = UPDATE_URL.rstrip("/") + f"/{APP_EXECUTABLE}"
    new_exe_path = APP_EXECUTABLE + ".new"
    
    logging.info(f"Downloading update from {exe_url}")
    
    try:
        response = requests.get(exe_url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Write to .new file
        with open(new_exe_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify it's a valid PE file
        with open(new_exe_path, "rb") as f:
            header = f.read(2)
            if header != b'MZ':
                logging.error("Downloaded file is not a valid executable.")
                os.remove(new_exe_path)
                return None
        
        # Verify SHA256 if provided
        if sha256_expected:
            sha256_hash = hashlib.sha256()
            with open(new_exe_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            calculated = sha256_hash.hexdigest()
            
            if calculated.lower() != sha256_expected.lower():
                logging.error(f"Hash mismatch! Expected: {sha256_expected}, Got: {calculated}")
                os.remove(new_exe_path)
                return None
            logging.info("Hash verified successfully.")
        
        logging.info(f"Download complete: {new_exe_path}")
        return new_exe_path
        
    except Exception as e:
        logging.error(f"Download failed: {e}")
        if os.path.exists(new_exe_path):
            os.remove(new_exe_path)
        return None


def apply_update(new_exe_path):
    """Replaces the old executable with the new one."""
    old_exe_path = APP_EXECUTABLE + ".old"
    
    try:
        # Remove old backup if exists
        if os.path.exists(old_exe_path):
            os.remove(old_exe_path)
        
        # Rename current to .old
        if os.path.exists(APP_EXECUTABLE):
            os.rename(APP_EXECUTABLE, old_exe_path)
            logging.info(f"Renamed {APP_EXECUTABLE} -> {old_exe_path}")
        
        # Rename .new to current
        os.rename(new_exe_path, APP_EXECUTABLE)
        logging.info(f"Renamed {new_exe_path} -> {APP_EXECUTABLE}")
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to apply update: {e}")
        # Try to restore
        if os.path.exists(old_exe_path) and not os.path.exists(APP_EXECUTABLE):
            os.rename(old_exe_path, APP_EXECUTABLE)
            logging.info("Restored original executable.")
        return False


def main_startup():
    """Default startup: check for updates, then launch app."""
    logging.info("=== Starting main_startup ===")
    
    current_version = get_app_version()
    update_info = check_for_updates(current_version)
    
    cmd = get_main_app_command()
    if update_info:
        logging.info(f"Update available: {update_info['version']}")
        cmd.append("--update-available")
    else:
        logging.info("No update available. Launching normally.")
    
    # Hide console window on Windows
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    
    subprocess.Popen(cmd, startupinfo=startupinfo)
    sys.exit(0)


def install_update():
    """Called by main app: download and install the update."""
    logging.info("=== Starting install_update ===")
    
    # 1. Wait for the main app to close
    if not wait_for_app_to_close():
        logging.error("Could not proceed - app still running.")
        # Launch app anyway so user isn't left with nothing
        subprocess.Popen(get_main_app_command())
        sys.exit(1)
    
    # 2. Get update info
    current_version = get_app_version()
    update_info = check_for_updates(current_version)
    
    if not update_info:
        logging.info("No update found. Launching app normally.")
        subprocess.Popen(get_main_app_command())
        sys.exit(0)
    
    # 3. Download the update
    new_exe = download_update(sha256_expected=update_info.get("sha256"))
    
    if not new_exe:
        logging.error("Download failed. Launching current app.")
        subprocess.Popen(get_main_app_command())
        sys.exit(1)
    
    # 4. Apply the update
    if apply_update(new_exe):
        logging.info("Update applied successfully!")
    else:
        logging.error("Failed to apply update. Launching current app.")
    
    # 5. Launch the (hopefully new) app
    logging.info("Launching updated app...")
    
    # Hide console window on Windows
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    
    subprocess.Popen(get_main_app_command(), startupinfo=startupinfo)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Launcher for AutoMeldung")
    parser.add_argument("--install-update", action="store_true", help="Download and install update")
    args = parser.parse_args()
    
    if args.install_update:
        install_update()
    else:
        main_startup()


if __name__ == "__main__":
    main()
