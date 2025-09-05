import os
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from robot.libraries.BuiltIn import BuiltIn
import json


# CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_PATH = "/usr/bin/google-chrome"
DEBUGGING_PORT = 9222
USER_DATA_DIR = os.path.abspath("chrome-profile")

# Ensure profile dir exists
os.makedirs(USER_DATA_DIR, exist_ok=True)


def fix_restore_popup(profile_path):
    """Patch exit_type in Preferences to avoid 'Chrome crashed' popup."""
    prefs_file = os.path.join(profile_path, "Default", "Preferences")
    if os.path.exists(prefs_file):
        try:
            with open(prefs_file, "r+", encoding="utf-8") as f:
                prefs = json.load(f)
                if prefs.get("profile", {}).get("exit_type") == "Crashed":
                    prefs["profile"]["exit_type"] = "Normal"
                    f.seek(0)
                    json.dump(prefs, f, indent=2)
                    f.truncate()
        except Exception as e:
            print("Failed to patch Preferences:", e)


class ChromeLibrary:
    ROBOT_LIBRARY_SCOPE = "SUITE"   # One instance per test suite

    def __init__(self):
        self.chrome_process = None
        self.driver = None
        self.download_dir = None

    def _write_prefs(self, download_dir):
        """Merge custom prefs into Chrome Preferences file before launch."""
        prefs_file = os.path.join(USER_DATA_DIR, "Default", "Preferences")
        os.makedirs(os.path.dirname(prefs_file), exist_ok=True)

        custom_prefs = {
            "printing": {
                "print_preview_sticky_settings.appState": {
                    "recentDestinations": [{"id": "Save as PDF", "origin": "local"}],
                    "selectedDestinationId": "Save as PDF",
                    "version": 2
                }
            },
            "savefile": {"default_directory": download_dir},
            "download": {
                "default_directory": download_dir,
                "prompt_for_download": False
            },
            "plugins": {
                "always_open_pdf_externally": True
            },
            "profile": {
                "default_content_setting_values": {"popups": 1},
                "password_manager_enabled": False
            },
            "credentials_enable_service": False
        }

        # Load existing prefs if present
        if os.path.exists(prefs_file):
            try:
                with open(prefs_file, "r", encoding="utf-8") as f:
                    prefs = json.load(f)
            except Exception:
                prefs = {}
        else:
            prefs = {}

        # Deep merge (shallow here, enough for most cases)
        prefs.update(custom_prefs)

        with open(prefs_file, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)

    def launch_chrome(self, download_dir):
        """Launch Chrome with remote debugging enabled."""
        if self.chrome_process and self.chrome_process.poll() is None:
            return "Chrome already running"

        self.download_dir = download_dir
        fix_restore_popup(USER_DATA_DIR)

        # Clean leftover lock files
        for f in os.listdir(USER_DATA_DIR):
            if f.startswith("Singleton"):
                try:
                    os.remove(os.path.join(USER_DATA_DIR, f))
                except Exception:
                    pass

        # ✅ Write prefs before Chrome starts
        self._write_prefs(download_dir)

        chrome_args = [
            CHROME_PATH,
            f'--remote-debugging-port={DEBUGGING_PORT}',
            f'--user-data-dir={USER_DATA_DIR}',
            '--start-maximized',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-session-crashed-bubble',
            '--disable-infobars',

            # 🔽 extra options
            "--disable-extensions",
            "--disable-dev-shm-usage",
            "--kiosk-printing",
            "--disable-password-manager",
        ]

        self.chrome_process = subprocess.Popen(
            chrome_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(3)
        return "Chrome launched"

    def connect_driver(self):
        """Attach Selenium driver to running Chrome session and register with SeleniumLibrary."""
        options = Options()
        options.debugger_address = f"127.0.0.1:{DEBUGGING_PORT}"

        self.driver = webdriver.Chrome(options=options)

        # Get Robot's SeleniumLibrary instance
        seleniumlib = BuiltIn().get_library_instance("SeleniumLibrary")

        # Register this driver
        seleniumlib.register_driver(self.driver, alias="ChromeDebug")

        return "Driver connected"

    def close_chrome(self):
        """Close Selenium driver and kill Chrome process."""
        # Close Selenium driver if open
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

        # Kill Chrome process
        if self.chrome_process and self.chrome_process.poll() is None:
            self.chrome_process.terminate()
            try:
                self.chrome_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.chrome_process.kill()
            self.chrome_process = None
            return "Chrome closed"

        return "No Chrome process to close"
