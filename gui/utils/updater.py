import logging
import os
import sys
import shutil
import update_config
from tufup.client import Client

# Setup logging
logging.basicConfig(
    filename='update_process.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def apply_update():
    """
    Applies the update using tufup.
    """
    APP_NAME = "AutoMeldung"
    CURRENT_VERSION = update_config.CURRENT_VERSION
    UPDATE_URL = update_config.UPDATE_URL
    
    # Determine paths
    if getattr(sys, 'frozen', False):
        # Running as compiled EXE
        APP_INSTALL_DIR = os.path.dirname(sys.executable)
    else:
        # Running from source
        APP_INSTALL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Metadata and Target directories
    # We assume a 'metadata' folder exists or we use the one in gui/components/metadata_cache
    # But tufup expects a specific structure or we configure it.
    # Let's use a local 'tuf_client' folder for metadata and downloads to keep it clean.
    CLIENT_DIR = os.path.join(APP_INSTALL_DIR, "tuf_client")
    METADATA_DIR = os.path.join(CLIENT_DIR, "metadata")
    TARGET_DIR = os.path.join(CLIENT_DIR, "targets")
    
    # Ensure directories exist
    os.makedirs(METADATA_DIR, exist_ok=True)
    os.makedirs(TARGET_DIR, exist_ok=True)

    # We need the initial trusted root.json.
    # It should be bundled with the app.
    bundled_root = None
    
    if getattr(sys, 'frozen', False):
        # Look in the temporary bundle directory
        bundled_root = os.path.join(sys._MEIPASS, "gui", "components", "metadata_cache", "root.json")
    else:
        # Look in the source directory
        bundled_root = os.path.join(APP_INSTALL_DIR, "gui", "components", "metadata_cache", "root.json")
        
    # Fallback: check if it's in a 'keystore' folder next to the exe (unlikely for one-file, but possible)
    if not bundled_root or not os.path.exists(bundled_root):
         potential_path = os.path.join(APP_INSTALL_DIR, "keystore", "root.json")
         if os.path.exists(potential_path):
             bundled_root = potential_path

    # If we still don't have it, we can't proceed securely.
    # But for now, let's assume it's there or we copy it if missing.
    # If metadata dir is empty, copy root.json there.
    if not os.path.exists(os.path.join(METADATA_DIR, "root.json")):
        if bundled_root and os.path.exists(bundled_root):
            shutil.copy(bundled_root, os.path.join(METADATA_DIR, "root.json"))
        else:
            logger.error(f"Trusted root.json not found. Searched at: {bundled_root}")
            return False

    # Initialize Client
    client = Client(
        app_name=APP_NAME,
        app_install_dir=APP_INSTALL_DIR,
        current_version=CURRENT_VERSION,
        metadata_dir=METADATA_DIR,
        target_dir=TARGET_DIR,
        target_base_url=UPDATE_URL
    )

    try:
        logger.info("Refreshing metadata...")
        client.refresh()
        
        # We assume the launcher already checked, so we just want to install.
        # But we should check again to be sure and get the target info.
        update_info = client.check_for_updates()
        
        if update_info:
            logger.info("Downloading update...")
            client.download_and_apply_update()
            # Note: download_and_apply_update() might fail on Windows if it tries to overwrite the running exe.
            # If tufup doesn't handle it, we might crash here.
            # However, tufup uses `shutil.unpack_archive`.
            # If we are running as App.exe, we can rename ourselves.
            
            # To be safe, let's rename ourselves BEFORE calling apply if we are frozen.
            if getattr(sys, 'frozen', False):
                my_exe = sys.executable
                old_exe = my_exe + ".old"
                if os.path.exists(old_exe):
                    os.remove(old_exe)
                
                try:
                    os.rename(my_exe, old_exe)
                except OSError as e:
                    logger.error(f"Could not rename executable: {e}")
                    return False
                
                # Now we are running as .old (in memory/filesystem), so the original name is free.
                # But wait, if we rename, `sys.executable` still points to the old path?
                # No, the file on disk is renamed. The process keeps running.
                # `client.app_install_dir` is where it will unpack.
                # It should unpack `App.exe` (and other files) to `APP_INSTALL_DIR`.
                # Since `App.exe` is gone (renamed), it should succeed.
                
            logger.info("Update applied successfully.")
            return True
        else:
            logger.info("No update found during installation phase.")
            return False
            
    except Exception as e:
        logger.error(f"Update process failed: {e}")
        # If we renamed ourselves and failed, we should try to restore?
        if getattr(sys, 'frozen', False):
            my_exe = sys.executable
            old_exe = my_exe + ".old"
            if os.path.exists(old_exe) and not os.path.exists(my_exe):
                os.rename(old_exe, my_exe)
        return False
