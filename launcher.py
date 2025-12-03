"""
AutoMeldung Launcher
====================
A modern launcher with a sleek loading screen that:
1. Shows fun facts while loading
2. Checks for updates on startup
3. Downloads and installs updates (when requested by the main app)
4. Launches the core application

This will be compiled as AutoMeldung.exe (user-facing)
The actual app is core.exe (internal)
"""

import sys
import os
import subprocess
import time
import argparse
import requests
import logging
import hashlib
import threading
import random

# Hide console window immediately on Windows
if sys.platform == "win32":
    import ctypes
    # Hide console
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    # Enable DPI awareness for sharp rendering
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

import tkinter as tk
from tkinter import font as tkfont

# Configure logging (to file only, no console)
logging.basicConfig(
    filename='launcher.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration - core.exe is the actual application
CORE_EXECUTABLE = "core.exe"

# Fun facts to display while loading
FUN_FACTS = [
    "Did you know? PDFs were invented by Adobe in 1993.",
    "The average office worker uses 10,000 sheets of paper per year.",
    "Tip: You can drag and drop files directly into the app!",
    "'Automeldung' means 'auto-report' in German.",
    "The first PDF viewer was called Acrobat Reader.",
    "Tip: Keep your templates organized for faster exports.",
    "Digital documents save trees! 🌲",
    "A paperless office saves about 50% in storage costs.",
    "Tip: Check for updates regularly to get new features!",
    "This app was built with Python and Flet.",
    "The PDF format is now an open ISO standard.",
    "Tip: Use descriptive filenames for easier searching.",
    "Over 2.5 trillion PDFs are created every year.",
    "Tip: Press Tab to navigate between fields quickly.",
]

# Update URL
UPDATE_URL = None
try:
    import update_config
    UPDATE_URL = update_config.UPDATE_URL
except ImportError:
    pass

if not UPDATE_URL:
    UPDATE_URL = "https://aminechr54.github.io/AutoMeldung/updates/"


class ModernSplashScreen:
    """A modern, sleek loading splash screen."""
    
    def __init__(self, mode="startup"):
        self.mode = mode
        self.root = None
        self.status_label = None
        self.fact_label = None
        self.canvas = None
        self.should_close = False
        self.update_available = False
        self.progress_angle = 0
        self.dots = 0
        
    def create_window(self):
        """Creates the modern splash screen window."""
        self.root = tk.Tk()
        self.root.title("AutoMeldung")
        
        # Window settings - larger for better readability
        width, height = 480, 280
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Remove window decorations (borderless)
        self.root.overrideredirect(True)
        
        # Make window stay on top initially
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
        # Modern dark theme colors
        self.bg_color = "#0f0f1a"
        self.fg_color = "#ffffff"
        self.accent_color = "#6366f1"  # Indigo
        self.accent_light = "#818cf8"
        self.muted_color = "#6b7280"
        self.card_color = "#1a1a2e"
        
        self.root.configure(bg=self.bg_color)
        
        # Create canvas for custom drawing
        self.canvas = tk.Canvas(
            self.root,
            width=width,
            height=height,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Draw rounded rectangle background
        self.draw_rounded_rect(10, 10, width-10, height-10, 20, self.card_color)
        
        # Draw subtle border
        self.draw_rounded_rect_outline(10, 10, width-10, height-10, 20, "#2a2a4a")
        
        # App icon (simple geometric shape)
        self.draw_app_icon(width // 2, 70)
        
        # App title
        title_font = tkfont.Font(family="Segoe UI", size=22, weight="bold")
        self.canvas.create_text(
            width // 2, 120,
            text="AutoMeldung",
            font=title_font,
            fill=self.fg_color
        )
        
        # Version text
        version_font = tkfont.Font(family="Segoe UI", size=9)
        try:
            version = update_config.CURRENT_VERSION
        except:
            version = "1.0.0"
        self.canvas.create_text(
            width // 2, 145,
            text=f"v{version}",
            font=version_font,
            fill=self.muted_color
        )
        
        # Status text
        status_font = tkfont.Font(family="Segoe UI", size=11)
        status_text = "Checking for updates" if self.mode == "startup" else "Installing update"
        self.status_text_id = self.canvas.create_text(
            width // 2, 180,
            text=status_text,
            font=status_font,
            fill=self.accent_light
        )
        
        # Loading dots animation
        self.dots_id = self.canvas.create_text(
            width // 2 + 80, 180,
            text="",
            font=status_font,
            fill=self.accent_light,
            anchor="w"
        )
        
        # Progress bar background
        bar_width = 300
        bar_height = 4
        bar_x = (width - bar_width) // 2
        bar_y = 205
        
        self.draw_rounded_rect(bar_x, bar_y, bar_x + bar_width, bar_y + bar_height, 2, "#2a2a4a")
        
        # Progress bar fill (animated)
        self.progress_bar = self.canvas.create_rectangle(
            bar_x, bar_y, bar_x + 50, bar_y + bar_height,
            fill=self.accent_color, outline=""
        )
        self.bar_x = bar_x
        self.bar_width = bar_width
        self.bar_y = bar_y
        self.bar_height = bar_height
        
        # Fun fact
        fact_font = tkfont.Font(family="Segoe UI", size=9)
        self.fact_id = self.canvas.create_text(
            width // 2, 245,
            text=random.choice(FUN_FACTS),
            font=fact_font,
            fill=self.muted_color,
            width=400
        )
        
        # Start animations
        self.animate_progress()
        self.animate_dots()
        self.rotate_facts()
        
    def draw_rounded_rect(self, x1, y1, x2, y2, radius, color):
        """Draws a rounded rectangle."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        self.canvas.create_polygon(points, fill=color, smooth=True, outline="")
        
    def draw_rounded_rect_outline(self, x1, y1, x2, y2, radius, color):
        """Draws a rounded rectangle outline."""
        # Top
        self.canvas.create_line(x1 + radius, y1, x2 - radius, y1, fill=color)
        # Right
        self.canvas.create_line(x2, y1 + radius, x2, y2 - radius, fill=color)
        # Bottom
        self.canvas.create_line(x1 + radius, y2, x2 - radius, y2, fill=color)
        # Left
        self.canvas.create_line(x1, y1 + radius, x1, y2 - radius, fill=color)
        # Corners (arcs)
        self.canvas.create_arc(x1, y1, x1 + 2*radius, y1 + 2*radius, start=90, extent=90, style="arc", outline=color)
        self.canvas.create_arc(x2 - 2*radius, y1, x2, y1 + 2*radius, start=0, extent=90, style="arc", outline=color)
        self.canvas.create_arc(x2 - 2*radius, y2 - 2*radius, x2, y2, start=270, extent=90, style="arc", outline=color)
        self.canvas.create_arc(x1, y2 - 2*radius, x1 + 2*radius, y2, start=180, extent=90, style="arc", outline=color)
        
    def draw_app_icon(self, cx, cy):
        """Draws a modern app icon."""
        # Outer circle (gradient effect with multiple circles)
        for i in range(3):
            offset = i * 2
            color = ["#4f46e5", "#6366f1", "#818cf8"][i]
            self.canvas.create_oval(
                cx - 25 + offset, cy - 25 + offset,
                cx + 25 - offset, cy + 25 - offset,
                fill=color, outline=""
            )
        
        # Document icon in center
        doc_color = "#ffffff"
        # Document body
        self.canvas.create_rectangle(cx - 8, cy - 12, cx + 8, cy + 12, fill=doc_color, outline="")
        # Folded corner
        self.canvas.create_polygon(
            cx + 8, cy - 12,
            cx + 8, cy - 6,
            cx + 2, cy - 12,
            fill="#c7d2fe", outline=""
        )
        # Lines on document
        for i in range(3):
            y = cy - 4 + i * 6
            self.canvas.create_line(cx - 5, y, cx + 5, y, fill="#6366f1", width=1)
    
    def animate_progress(self):
        """Animates the progress bar (back and forth)."""
        if self.should_close or not self.root:
            return
            
        # Calculate position (oscillating)
        import math
        self.progress_angle += 0.05
        progress = (math.sin(self.progress_angle) + 1) / 2  # 0 to 1
        
        fill_width = 80
        x_pos = self.bar_x + progress * (self.bar_width - fill_width)
        
        self.canvas.coords(
            self.progress_bar,
            x_pos, self.bar_y,
            x_pos + fill_width, self.bar_y + self.bar_height
        )
        
        self.root.after(16, self.animate_progress)  # ~60fps
    
    def animate_dots(self):
        """Animates the loading dots."""
        if self.should_close or not self.root:
            return
            
        self.dots = (self.dots + 1) % 4
        dots_text = "." * self.dots
        self.canvas.itemconfig(self.dots_id, text=dots_text)
        
        self.root.after(400, self.animate_dots)
    
    def rotate_facts(self):
        """Changes the fun fact periodically."""
        if self.should_close or not self.root:
            return
            
        self.canvas.itemconfig(self.fact_id, text=random.choice(FUN_FACTS))
        self.root.after(4000, self.rotate_facts)
    
    def set_status(self, text):
        """Updates the status text."""
        if self.canvas and self.status_text_id:
            self.canvas.itemconfig(self.status_text_id, text=text)
            self.root.update()
    
    def close(self):
        """Closes the splash screen."""
        self.should_close = True
        if self.root:
            self.root.destroy()
            self.root = None
    
    def run(self):
        """Runs the splash screen main loop."""
        if self.root:
            self.root.mainloop()


# Global splash reference
splash = None


def get_main_app_command():
    """Determines the command to run the core app."""
    if os.path.exists(CORE_EXECUTABLE):
        return [CORE_EXECUTABLE]
    elif os.path.exists("gui/app.py"):
        return [sys.executable, "gui/app.py"]
    else:
        logging.error("Core application not found.")
        return None


def get_app_version():
    """Gets the version of the core application."""
    cmd = get_main_app_command()
    if not cmd:
        return None
    cmd = cmd + ["--version"]
    try:
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10, startupinfo=startupinfo)
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
                    "url": data.get("url")
                }
    except Exception as e:
        logging.error(f"Update check failed: {e}")
    
    return None


def wait_for_app_to_close(max_wait=30, callback=None):
    """Waits for the core app to close by checking file lock."""
    logging.info("Waiting for core app to close...")
    
    for i in range(max_wait):
        try:
            if os.path.exists(CORE_EXECUTABLE):
                with open(CORE_EXECUTABLE, "a+b") as f:
                    pass
            logging.info("Core app file is accessible.")
            return True
        except PermissionError:
            if callback:
                callback(f"Waiting for app to close ({i+1}s)")
            logging.info(f"Core app still running. Retrying {i+1}/{max_wait}...")
            time.sleep(1)
        except Exception as e:
            logging.warning(f"Error checking file lock: {e}")
            time.sleep(1)
    
    logging.error("Timed out waiting for core app to close.")
    return False


def download_update(sha256_expected=None, callback=None):
    """Downloads the new core executable from the server."""
    # Server still hosts as core.exe
    exe_url = UPDATE_URL.rstrip("/") + f"/{CORE_EXECUTABLE}"
    new_exe_path = CORE_EXECUTABLE + ".new"
    
    logging.info(f"Downloading update from {exe_url}")
    if callback:
        callback("Downloading update")
    
    try:
        response = requests.get(exe_url, stream=True, timeout=120)
        response.raise_for_status()
        
        with open(new_exe_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify PE file
        with open(new_exe_path, "rb") as f:
            header = f.read(2)
            if header != b'MZ':
                logging.error("Downloaded file is not a valid executable.")
                os.remove(new_exe_path)
                return None
        
        # Verify SHA256
        if sha256_expected:
            if callback:
                callback("Verifying download")
            sha256_hash = hashlib.sha256()
            with open(new_exe_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            calculated = sha256_hash.hexdigest()
            
            if calculated.lower() != sha256_expected.lower():
                logging.error(f"Hash mismatch!")
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


def apply_update(new_exe_path, callback=None):
    """Replaces the old core executable with the new one."""
    old_exe_path = CORE_EXECUTABLE + ".old"
    
    if callback:
        callback("Installing update")
    
    try:
        if os.path.exists(old_exe_path):
            os.remove(old_exe_path)
        
        if os.path.exists(CORE_EXECUTABLE):
            os.rename(CORE_EXECUTABLE, old_exe_path)
            logging.info(f"Renamed {CORE_EXECUTABLE} -> {old_exe_path}")
        
        os.rename(new_exe_path, CORE_EXECUTABLE)
        logging.info(f"Renamed {new_exe_path} -> {CORE_EXECUTABLE}")
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to apply update: {e}")
        if os.path.exists(old_exe_path) and not os.path.exists(CORE_EXECUTABLE):
            os.rename(old_exe_path, CORE_EXECUTABLE)
            logging.info("Restored original executable.")
        return False


def launch_app(with_update_flag=False):
    """Launches the core application."""
    cmd = get_main_app_command()
    if not cmd:
        return
    
    if with_update_flag:
        cmd.append("--update-available")
    
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    
    subprocess.Popen(cmd, startupinfo=startupinfo)


def startup_worker():
    """Background worker for startup mode."""
    global splash
    
    try:
        if splash:
            splash.set_status("Getting version info")
        
        current_version = get_app_version()
        
        if splash:
            splash.set_status("Checking for updates")
        
        update_info = check_for_updates(current_version)
        
        time.sleep(0.5)
        
        if splash:
            if update_info:
                splash.set_status(f"Update {update_info['version']} available!")
                splash.update_available = True
            else:
                splash.set_status("Starting application")
        
        time.sleep(0.3)
        
        launch_app(with_update_flag=bool(update_info))
        
    except Exception as e:
        logging.error(f"Startup error: {e}")
    finally:
        if splash:
            splash.root.after(100, splash.close)


def update_worker():
    """Background worker for update installation mode."""
    global splash
    
    def set_status(text):
        if splash:
            try:
                splash.root.after(0, lambda: splash.set_status(text))
            except:
                pass
    
    try:
        set_status("Waiting for app to close")
        
        if not wait_for_app_to_close(callback=set_status):
            logging.error("Could not proceed - app still running.")
            launch_app()
            return
        
        set_status("Getting version info")
        current_version = get_app_version()
        update_info = check_for_updates(current_version)
        
        if not update_info:
            logging.info("No update found. Launching app normally.")
            set_status("Starting application")
            time.sleep(0.5)
            launch_app()
            return
        
        set_status(f"Downloading v{update_info['version']}")
        new_exe = download_update(sha256_expected=update_info.get("sha256"), callback=set_status)
        
        if not new_exe:
            logging.error("Download failed. Launching current app.")
            set_status("Download failed")
            time.sleep(1)
            launch_app()
            return
        
        set_status("Installing update")
        if apply_update(new_exe, callback=set_status):
            logging.info("Update applied successfully!")
            set_status("Update complete!")
        else:
            logging.error("Failed to apply update.")
            set_status("Update failed")
        
        time.sleep(0.5)
        set_status("Starting application")
        time.sleep(0.3)
        
        launch_app()
        
    except Exception as e:
        logging.error(f"Update error: {e}")
        launch_app()
    finally:
        if splash:
            splash.root.after(100, splash.close)


def main_startup():
    """Default startup with splash screen."""
    global splash
    logging.info("=== Starting main_startup ===")
    
    splash = ModernSplashScreen(mode="startup")
    splash.create_window()
    
    worker = threading.Thread(target=startup_worker, daemon=True)
    worker.start()
    
    splash.run()
    
    sys.exit(0)


def install_update():
    """Update installation with splash screen."""
    global splash
    logging.info("=== Starting install_update ===")
    
    splash = ModernSplashScreen(mode="update")
    splash.create_window()
    
    worker = threading.Thread(target=update_worker, daemon=True)
    worker.start()
    
    splash.run()
    
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="AutoMeldung Launcher")
    parser.add_argument("--install-update", action="store_true", help="Download and install update")
    args = parser.parse_args()
    
    if args.install_update:
        install_update()
    else:
        main_startup()


if __name__ == "__main__":
    main()
