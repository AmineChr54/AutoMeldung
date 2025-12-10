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

# ============================================================================
# PyInstaller Cleanup Warning Suppression
# ============================================================================
# When running as a PyInstaller one-file executable, a temporary directory
# (_MEIxxxxxx) is created. On exit, PyInstaller tries to remove it but sometimes
# files are still locked (antivirus, timing, etc.), causing a warning dialog.
# This patch suppresses that warning since the temp files will be cleaned up
# by Windows automatically.
# ============================================================================
def _patch_pyinstaller_cleanup():
    """Patch PyInstaller's cleanup to suppress 'Failed to remove temporary directory' warning."""
    try:
        import atexit
        import shutil
        
        # Check if running as a PyInstaller bundle
        if not getattr(sys, 'frozen', False):
            return
        
        # Get the MEI temp directory path
        mei_dir = getattr(sys, '_MEIPASS', None)
        if not mei_dir:
            return
        
        # Store original shutil.rmtree
        original_rmtree = shutil.rmtree
        
        def silent_rmtree(path, ignore_errors=False, onerror=None):
            """Wrapper that silently ignores errors for MEI temp directories."""
            try:
                # If this is a PyInstaller temp directory, suppress errors
                if '_MEI' in str(path):
                    original_rmtree(path, ignore_errors=True)
                else:
                    original_rmtree(path, ignore_errors=ignore_errors, onerror=onerror)
            except Exception:
                pass  # Silently ignore all cleanup errors
        
        # Replace shutil.rmtree with our silent version
        shutil.rmtree = silent_rmtree
        
        # Also patch the bootloader's cleanup function if accessible
        try:
            # PyInstaller uses _pyi_splash or similar for cleanup
            import _pyi_splash
            _pyi_splash._on_cleanup = lambda: None
        except ImportError:
            pass
            
    except Exception:
        pass  # If patching fails, continue normally

# Apply the patch immediately
_patch_pyinstaller_cleanup()

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
    "'AutoMeldung' means 'auto-report' in German.",
    "The first PDF viewer was called Acrobat Reader.",
    "Tip: Keep your templates organized for faster exports.",
    "Digital documents save trees! 🌲",
    "A paperless office saves about 50% in storage costs.",
    "Tip: Check for updates regularly to get new features!",
    "This app was built with Python and Flet.",
    "The PDF format is now an open ISO standard.",
    "Tip: Use descriptive filenames for easier searching.",
    "Over 2.5 trillion PDFs are created every year."
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
    """A modern, sleek loading splash screen with smooth edges."""
    
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
        self.glow_phase = 0
        self.scale = 1.0  # Raw DPI scale factor (screen)
        self.win_scale = 1.0  # Window element scale (clamped)
        self.font_scale = 1.0  # Font scale (clamped, slightly lower than DPI)
        
    def get_dpi_scale(self):
        """Calculate scale factor based on screen DPI."""
        try:
            # Get the actual DPI
            dpi = self.root.winfo_fpixels('1i')
            # Standard DPI is 96, scale proportionally
            # For high-DPI displays, this will be > 1
            scale = dpi / 96.0
            # Clamp between 1.0 and 2.5 for reasonable scaling
            return max(1.0, min(2.5, scale))
        except:
            return 1.0
    
    def s(self, value):
        """Scale a value for window geometry based on clamped DPI."""
        return int(value * self.win_scale)

    def fs(self, value):
        """Scale a font size based on clamped font DPI."""
        return int(max(1, round(value * self.font_scale)))
        
    def create_window(self):
        """Creates the modern splash screen window."""
        self.root = tk.Tk()
        self.root.title("AutoMeldung")
        
        # Calculate DPI scale factor and derive UI scales
        self.scale = self.get_dpi_scale()
        # Keep window scaling reasonable; very large displays won't explode the UI
        self.win_scale = max(1.0, min(1.6, self.scale))
        # Fonts usually feel too large at full DPI; cap and slightly reduce
        self.font_scale = max(1.0, min(1.25, self.scale * 0.9))

        # Base dimensions (smaller and then scaled)
        base_width, base_height = 520, 360
        width = self.s(base_width)
        height = self.s(base_height)
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Remove window decorations (borderless)
        self.root.overrideredirect(True)
        
        # Make window transparent for smooth edges
        self.root.attributes('-transparentcolor', '#010101')
        
        # Make window stay on top initially
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
        # Modern Flet-like dark theme colors (matching your app)
        self.bg_color = "#010101"  # Transparent color
        self.fg_color = "#ffffff"
        self.accent_color = "#7c4dff"  # Purple accent like Flet
        self.accent_light = "#b388ff"
        self.accent_glow = "#9c6fff"
        self.muted_color = "#9e9e9e"
        self.card_color = "#1e1e2e"  # Dark surface color
        self.surface_color = "#252536"  # Slightly lighter surface
        self.border_color = "#3d3d5c"
        
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
        
        # Draw smooth rounded rectangle with shadow effect
        self.draw_shadow(self.s(20), self.s(20), width-self.s(20), height-self.s(20), self.s(28))
        
        # Draw main card with smooth rounded corners
        self.draw_smooth_rounded_rect(self.s(16), self.s(16), width-self.s(16), height-self.s(16), self.s(28), self.card_color)
        
        # Draw inner highlight for depth
        self.draw_inner_glow(self.s(18), self.s(18), width-self.s(18), height-self.s(18), self.s(26), "#2a2a3e")
        
        # Draw subtle border with gradient feel
        self.draw_smooth_border(self.s(16), self.s(16), width-self.s(16), height-self.s(16), self.s(28), self.border_color)
        
        # App icon (modern geometric shape with glow)
        self.draw_modern_app_icon(width // 2, self.s(92))
        
        # App title with modern font - scale font size (slightly smaller)
        title_size = self.fs(22)
        title_font = tkfont.Font(family="Segoe UI Variable", size=title_size, weight="bold")
        # Try fallback fonts if Segoe UI Variable not available
        try:
            self.canvas.create_text(width // 2, self.s(176), text="AutoMeldung", font=title_font, fill=self.fg_color)
        except:
            title_font = tkfont.Font(family="Segoe UI", size=title_size, weight="bold")
            self.canvas.create_text(width // 2, self.s(176), text="AutoMeldung", font=title_font, fill=self.fg_color)
        
        # Version badge
        try:
            version = update_config.CURRENT_VERSION
        except:
            version = "1.0.0"
        
        # Version tag removed per request
        
        # Status text with modern font
        status_size = self.fs(12)
        status_font = tkfont.Font(family="Segoe UI", size=status_size)
        status_text = "Checking for updates" if self.mode == "startup" else "Installing update"
        self.status_text_id = self.canvas.create_text(
            width // 2, self.s(232),
            text=status_text,
            font=status_font,
            fill=self.accent_light
        )
        
        # Loading dots removed per request
        
        # Modern progress bar with rounded ends
        bar_width = self.s(360)
        bar_height = self.s(6)
        bar_x = (width - bar_width) // 2
        bar_y = self.s(266)
        
        # Progress bar track
        self.draw_smooth_rounded_rect(bar_x, bar_y, bar_x + bar_width, bar_y + bar_height, self.s(4), self.surface_color)
        
        # Progress bar fill (animated) with glow
        self.progress_bar = self.canvas.create_rectangle(
            bar_x + 2, bar_y + 1, bar_x + self.s(90), bar_y + bar_height - 1,
            fill=self.accent_color, outline=""
        )
        self.bar_x = bar_x
        self.bar_width = bar_width
        self.bar_y = bar_y
        self.bar_height = bar_height
        
        # Fun fact (icon removed per request)
        fact_size = self.fs(10)
        fact_font = tkfont.Font(family="Segoe UI", size=fact_size)
        self.fact_id = self.canvas.create_text(
            width // 2, self.s(304),
            text=random.choice(FUN_FACTS),
            font=fact_font,
            fill=self.muted_color,
            width=self.s(520),
            justify="center"
        )
        
        # Start animations (dots animation removed)
        self.animate_progress()
        self.rotate_facts()
        self.animate_glow()
        
    def draw_smooth_rounded_rect(self, x1, y1, x2, y2, radius, color):
        """Draws a smooth rounded rectangle using multiple overlapping shapes."""
        # Use create_polygon with more points for smoother corners
        import math
        points = []
        
        # Number of points for each corner arc
        steps = 12
        
        # Top-right corner
        for i in range(steps + 1):
            angle = math.pi * 1.5 + (math.pi / 2) * (i / steps)
            px = x2 - radius + radius * math.cos(angle)
            py = y1 + radius + radius * math.sin(angle)
            points.extend([px, py])
        
        # Bottom-right corner
        for i in range(steps + 1):
            angle = 0 + (math.pi / 2) * (i / steps)
            px = x2 - radius + radius * math.cos(angle)
            py = y2 - radius + radius * math.sin(angle)
            points.extend([px, py])
        
        # Bottom-left corner
        for i in range(steps + 1):
            angle = math.pi / 2 + (math.pi / 2) * (i / steps)
            px = x1 + radius + radius * math.cos(angle)
            py = y2 - radius + radius * math.sin(angle)
            points.extend([px, py])
        
        # Top-left corner
        for i in range(steps + 1):
            angle = math.pi + (math.pi / 2) * (i / steps)
            px = x1 + radius + radius * math.cos(angle)
            py = y1 + radius + radius * math.sin(angle)
            points.extend([px, py])
        
        self.canvas.create_polygon(points, fill=color, outline="", smooth=False)
    
    def draw_shadow(self, x1, y1, x2, y2, radius):
        """Draws a soft shadow effect."""
        # Inset shadow to avoid drawing past the card bounds
        shadow_colors = ["#0a0a12", "#0c0c15", "#0e0e18"]
        for i, color in enumerate(shadow_colors):
            inset = (len(shadow_colors) - i) * 2
            self.draw_smooth_rounded_rect(
                x1 + inset, y1 + inset,
                x2 - inset, y2 - inset,
                max(0, radius - inset // 2), color
            )
    
    def draw_inner_glow(self, x1, y1, x2, y2, radius, color):
        """Draws an inner highlight for depth."""
        # Top edge highlight
        self.draw_smooth_rounded_rect(x1, y1, x2, y1 + 2, radius, color)
    
    def draw_smooth_border(self, x1, y1, x2, y2, radius, color):
        """Draws a smooth border around the rectangle."""
        import math
        points = []
        steps = 14  # slightly more steps for cleaner corners
        
        # Top-right corner
        for i in range(steps + 1):
            angle = math.pi * 1.5 + (math.pi / 2) * (i / steps)
            px = x2 - radius + radius * math.cos(angle)
            py = y1 + radius + radius * math.sin(angle)
            points.extend([px, py])
        
        # Bottom-right corner
        for i in range(steps + 1):
            angle = 0 + (math.pi / 2) * (i / steps)
            px = x2 - radius + radius * math.cos(angle)
            py = y2 - radius + radius * math.sin(angle)
            points.extend([px, py])
        
        # Bottom-left corner
        for i in range(steps + 1):
            angle = math.pi / 2 + (math.pi / 2) * (i / steps)
            px = x1 + radius + radius * math.cos(angle)
            py = y2 - radius + radius * math.sin(angle)
            points.extend([px, py])
        
        # Top-left corner
        for i in range(steps + 1):
            angle = math.pi + (math.pi / 2) * (i / steps)
            px = x1 + radius + radius * math.cos(angle)
            py = y1 + radius + radius * math.sin(angle)
            points.extend([px, py])
        
        # Draw border line with rounded caps/joints to prevent tips
        self.canvas.create_line(points, fill=color, width=1, smooth=True, capstyle="round", joinstyle="round")

    # position_dots removed (loading dots no longer used)
    
    def draw_pill_badge(self, cx, cy, text, bg_color, text_color):
        """Draws a pill-shaped badge with text."""
        font_size = int(10 * self.scale)
        font = tkfont.Font(family="Segoe UI", size=font_size)
        # Measure text
        text_width = font.measure(text)
        padding = self.s(14)
        height = self.s(26)
        
        x1 = cx - text_width // 2 - padding
        x2 = cx + text_width // 2 + padding
        y1 = cy - height // 2
        y2 = cy + height // 2
        
        self.draw_smooth_rounded_rect(x1, y1, x2, y2, height // 2, bg_color)
        self.canvas.create_text(cx, cy, text=text, font=font, fill=text_color)
    
    def draw_modern_app_icon(self, cx, cy):
        """Draws a modern, cleaner document-in-circle icon."""
        # Outer soft glow (layered circles)
        outer_colors = ["#3f2e84", "#4b3a98", "#5a47ae"]
        for i, color in enumerate(outer_colors):
            r = self.s(50 - i * 6)
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")

        # Main circular badge (simulated gradient via layers)
        badge_layers = ["#5e35b1", "#6c3fe0", "#7c4dff", "#8b66ff"]
        for i, color in enumerate(badge_layers):
            r = self.s(34 - i * 4)
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")

        # Accent ring
        ring_r = self.s(34)
        self.canvas.create_oval(cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r, outline="#a78bfa", width=self.s(2))

        # Document card (rounded)
        doc_w, doc_h = self.s(28), self.s(36)
        rx, ry = self.s(7), self.s(7)
        x1, y1 = cx - doc_w // 2, cy - doc_h // 2
        x2, y2 = x1 + doc_w, y1 + doc_h

        # Subtle shadow behind doc
        self.draw_smooth_rounded_rect(x1 + self.s(1), y1 + self.s(2), x2 + self.s(1), y2 + self.s(2), rx, "#d2c6f7")
        # Document face
        self.draw_smooth_rounded_rect(x1, y1, x2, y2, rx, "#ffffff")

        # Folded corner (smaller, cleaner)
        fold = self.s(8)
        self.canvas.create_polygon(x2 - fold, y1, x2, y1, x2, y1 + fold, fill="#ede7f6", outline="")

        # Header bullet
        bullet_r = self.s(3)
        bx = x1 + self.s(6)
        by = y1 + self.s(8)
        self.canvas.create_oval(bx - bullet_r, by - bullet_r, bx + bullet_r, by + bullet_r, fill="#7c4dff", outline="")

        # Document lines (rounded ends)
        line_color = "#7c4dff"
        lw = max(2, self.s(2))
        start_x = x1 + self.s(10)
        line_lengths = [self.s(12), self.s(16), self.s(10)]
        for i, length in enumerate(line_lengths):
            y = y1 + self.s(12) + self.s(i * 8)
            self.canvas.create_line(start_x, y, start_x + length, y, fill=line_color, width=lw, capstyle="round")
    
    def animate_progress(self):
        """Animates the progress bar with smooth easing."""
        if self.should_close or not self.root:
            return
            
        # Calculate position with smooth easing
        import math
        self.progress_angle += 0.03
        
        # Use sine wave for smooth back-and-forth motion
        progress = (math.sin(self.progress_angle) + 1) / 2  # 0 to 1
        # Apply easing for smoother feel
        eased = progress * progress * (3 - 2 * progress)  # Smoothstep
        
        fill_width = self.s(100)  # Scaled progress bar fill width (slightly smaller)
        x_pos = self.bar_x + 2 + eased * (self.bar_width - fill_width - 4)
        
        self.canvas.coords(
            self.progress_bar,
            x_pos, self.bar_y + 1,
            x_pos + fill_width, self.bar_y + self.bar_height - 1
        )
        
        self.root.after(16, self.animate_progress)  # ~60fps
    
    # animate_dots removed per request
    
    def animate_glow(self):
        """Animates a subtle glow effect on the accent elements."""
        if self.should_close or not self.root:
            return
            
        import math
        self.glow_phase += 0.05
        
        # Pulse the progress bar color slightly
        intensity = int(77 + 20 * math.sin(self.glow_phase))  # 77 is base for #4d in hex
        glow_color = f"#7c{intensity:02x}ff"
        
        try:
            self.canvas.itemconfig(self.progress_bar, fill=glow_color)
        except:
            pass
        
        self.root.after(50, self.animate_glow)
    
    def rotate_facts(self):
        """Changes the fun fact periodically with transition."""
        if self.should_close or not self.root:
            return
            
        self.canvas.itemconfig(self.fact_id, text=random.choice(FUN_FACTS))
        self.root.after(5000, self.rotate_facts)
    
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
    
    os._exit(0)  # Use os._exit to skip atexit handlers and prevent PyInstaller cleanup warning


def install_update():
    """Update installation with splash screen."""
    global splash
    logging.info("=== Starting install_update ===")
    
    splash = ModernSplashScreen(mode="update")
    splash.create_window()
    
    worker = threading.Thread(target=update_worker, daemon=True)
    worker.start()
    
    splash.run()
    
    os._exit(0)  # Use os._exit to skip atexit handlers and prevent PyInstaller cleanup warning


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
