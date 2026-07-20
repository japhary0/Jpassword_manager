import os
import sys
import time
import threading
import sqlite3
import getpass
import secrets
import string
import subprocess
import shutil
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# =====================================================================
# ANSI COLOR THEME CONSTANTS
# =====================================================================

class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[1;31m"
    GREEN   = "\033[1;32m"
    YELLOW  = "\033[1;33m"
    BLUE    = "\033[1;34m"
    MAGENTA = "\033[1;35m"
    CYAN    = "\033[1;36m"
    GRAY    = "\033[0;90m"


# =====================================================================
# SYSTEM CLIPBOARD PURGE UTILITY
# =====================================================================

def purge_system_clipboard():
    """Flushes the system clipboard selection across Wayland and X11 display servers."""
    try:
        if os.environ.get("WAYLAND_DISPLAY") and shutil.which("wl-copy"):
            subprocess.run(['wl-copy', '--clear'], check=False)
            subprocess.run(['wl-copy', ''], check=False)
        elif shutil.which("xclip"):
            subprocess.run(['xclip', '-selection', 'clipboard', '/dev/null'], check=False)
            subprocess.run(['xclip', '-selection', 'primary', '/dev/null'], check=False)

        print(f"\n{Colors.CYAN}[⚡] Volatile timer expired: System clipboard purged successfully.{Colors.RESET}\n{Colors.BOLD}Command >> {Colors.RESET}", end="", flush=True)
    except Exception:
        pass


def synchronize_system_clipboard(payload: str):
    """Pipes decrypted plaintext to system clipboard."""
    try:
        if os.environ.get("WAYLAND_DISPLAY") and shutil.which("wl-copy"):
            process = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE)
            process.communicate(input=payload.encode('utf-8'))
        elif shutil.which("xclip"):
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
            process.communicate(input=payload.encode('utf-8'))
    except Exception as err:
        print(f"{Colors.RED}[-] Clipboard sync warning: {err}{Colors.RESET}")


# =====================================================================
# ADVANCED CRYPTOGRAPHIC ENGINE
# =====================================================================

class AdvancedCryptoEngine:
    ITERATIONS = 600000

    @staticmethod
    def derive_key(master_password: str, salt: bytes) -> bytes:
        """Derives a cryptographic key using PBKDF2-HMAC-SHA256."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=AdvancedCryptoEngine.ITERATIONS,
        )
        return kdf.derive(master_password.encode('utf-8'))

    @staticmethod
    def encrypt_data(master_password: str, plaintext: str) -> Tuple[bytes, bytes, bytes]:
        """Encrypts data using AES-256-GCM."""
        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = AdvancedCryptoEngine.derive_key(master_password, salt)
        
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        del key
        return salt, nonce, ciphertext

    @staticmethod
    def decrypt_data(master_password: str, salt: bytes, nonce: bytes, ciphertext: bytes) -> str:
        """Decrypts data encrypted with AES-256-GCM."""
        key = AdvancedCryptoEngine.derive_key(master_password, salt)
        aesgcm = AESGCM(key)
        
        try:
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            plaintext = decrypted_bytes.decode('utf-8')
            del key
            return plaintext
        except Exception:
            del key
            raise ValueError("Authentication tag mismatch or invalid master password.")


# =====================================================================
# DATABASE STORAGE ENGINE
# =====================================================================

class VaultDatabase:
    def __init__(self, db_path: str = "encrypted_vault.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initializes database schema and tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vault_canary (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    salt BLOB NOT NULL,
                    nonce BLOB NOT NULL,
                    ciphertext BLOB NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vault_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource TEXT UNIQUE NOT NULL,
                    salt BLOB NOT NULL,
                    nonce BLOB NOT NULL,
                    ciphertext BLOB NOT NULL
                )
            """)
            conn.commit()

    def is_initialized(self) -> bool:
        """Checks if a vault canary record exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM vault_canary WHERE id = 1")
            return cursor.fetchone() is not None

    def initialize_master_canary(self, master_password: str):
        """Creates the canary block for zero-knowledge password authentication."""
        canary_text = "CANARY_VERIFICATION_BLOCK_OK"
        salt, nonce, ciphertext = AdvancedCryptoEngine.encrypt_data(master_password, canary_text)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO vault_canary (id, salt, nonce, ciphertext) VALUES (1, ?, ?, ?)",
                (salt, nonce, ciphertext)
            )
            conn.commit()

    def verify_master_password(self, master_password: str) -> bool:
        """Validates master password against the canary block."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT salt, nonce, ciphertext FROM vault_canary WHERE id = 1")
            row = cursor.fetchone()
            if not row:
                return False
            
            salt, nonce, ciphertext = row
            try:
                decrypted = AdvancedCryptoEngine.decrypt_data(master_password, salt, nonce, ciphertext)
                return decrypted == "CANARY_VERIFICATION_BLOCK_OK"
            except ValueError:
                return False

    def store_credential_record(self, resource: str, salt: bytes, nonce: bytes, ciphertext: bytes):
        """Stores or updates an encrypted credential record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vault_records (resource, salt, nonce, ciphertext)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(resource) DO UPDATE SET
                    salt=excluded.salt,
                    nonce=excluded.nonce,
                    ciphertext=excluded.ciphertext
            """, (resource, salt, nonce, ciphertext))
            conn.commit()

    def fetch_credential_record(self, resource: str) -> Optional[Tuple[bytes, bytes, bytes]]:
        """Retrieves salt, nonce, and ciphertext for a given resource."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT salt, nonce, ciphertext FROM vault_records WHERE resource = ?", (resource,))
            return cursor.fetchone()

    def list_monitored_resources(self):
        """Returns all stored resource names."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT resource FROM vault_records ORDER BY resource ASC")
            return [row[0] for row in cursor.fetchall()]


# =====================================================================
# UTILITIES & COLORFUL UI
# =====================================================================

def generate_high_entropy_password(length: int = 24) -> str:
    """Generates a cryptographically strong random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def render_banner():
    banner = f"""
    {Colors.CYAN}.--------.{Colors.RESET}
   {Colors.CYAN}/ .------. \\{Colors.RESET}
  {Colors.CYAN}/ /        \\ \\{Colors.RESET}
  {Colors.CYAN}| |        | |{Colors.RESET}
{Colors.CYAN}__| |________| |__{Colors.RESET}
{Colors.GREEN}[=================]{Colors.RESET}
{Colors.GREEN}|     {Colors.YELLOW}MR_J.FO{Colors.GREEN}     |{Colors.RESET}
{Colors.GREEN}|      {Colors.MAGENTA}[  ]{Colors.GREEN}       |{Colors.RESET}
{Colors.GREEN}|      {Colors.MAGENTA}/  \\{Colors.GREEN}       |{Colors.RESET}
{Colors.GREEN}|     {Colors.MAGENTA}'----'{Colors.GREEN}      |{Colors.RESET}
{Colors.GREEN}|                 |{Colors.RESET}
{Colors.GREEN}[=================]{Colors.RESET}
{Colors.CYAN}================================================================={Colors.RESET}
🛡  {Colors.BOLD}{Colors.GREEN}ADVANCED PRIVACY VAULT CORE — HIGH SECURITY ENGINE{Colors.RESET}
{Colors.CYAN}================================================================={Colors.RESET}
"""
    print(banner)


# =====================================================================
# MAIN RUNTIME LOOP
# =====================================================================

def main():
    render_banner()
    db = VaultDatabase()

    # Zero-knowledge initialization check
    if not db.is_initialized():
        print(f"{Colors.YELLOW}[*] Uninitialized Vault detected. Creating new Master Vault...{Colors.RESET}")
        while True:
            pwd1 = getpass.getpass(f"{Colors.CYAN}Set New Master Password: {Colors.RESET}")
            pwd2 = getpass.getpass(f"{Colors.CYAN}Confirm Master Password: {Colors.RESET}")
            if pwd1 == pwd2 and pwd1.strip():
                db.initialize_master_canary(pwd1)
                print(f"{Colors.GREEN}[+] Vault initialized with cryptographic canary block.{Colors.RESET}\n")
                del pwd1, pwd2
                break
            print(f"{Colors.RED}[-] Passwords do not match or empty. Retry.{Colors.RESET}")

    # Master Authentication Loop
    attempts = 0
    master_password = ""
    while attempts < 3:
        master_password = getpass.getpass(f"{Colors.BOLD}Provide Vault Master Password: {Colors.RESET}")
        if db.verify_master_password(master_password):
            print(f"{Colors.GREEN}[+] Cryptographic verification clear. Vault access unlocked.{Colors.RESET}\n")
            break
        else:
            print(f"{Colors.RED}[-] Verification failed. Invalid Master Password.{Colors.RESET}")
            attempts += 1

    if attempts == 3:
        print(f"{Colors.RED}[!] Too many failed authentication attempts. Terminating session.{Colors.RESET}")
        sys.exit(1)

    # Command Execution Interface Loop
    while True:
        print(f"{Colors.GRAY}" + "-" * 65 + f"{Colors.RESET}")
        print(f"[{Colors.CYAN}1{Colors.RESET}] {Colors.BOLD}Securely Encrypt and Store New Password{Colors.RESET}")
        print(f"[{Colors.CYAN}2{Colors.RESET}] {Colors.BOLD}Generate a Random High-Entropy Password{Colors.RESET}")
        print(f"[{Colors.CYAN}3{Colors.RESET}] {Colors.BOLD}Decrypt and Sync Password to Clipboard (Auto-Wipes){Colors.RESET}")
        print(f"[{Colors.CYAN}4{Colors.RESET}] {Colors.BOLD}List Monitored Resources{Colors.RESET}")
        print(f"[{Colors.CYAN}5{Colors.RESET}] {Colors.BOLD}Terminate Secure Session{Colors.RESET}")
        print(f"{Colors.GRAY}" + "-" * 65 + f"{Colors.RESET}")

        user_choice = input(f"{Colors.BOLD}Command >> {Colors.RESET}").strip()

        if user_choice == "1":
            resource = input(f"{Colors.CYAN}Enter resource identifier (e.g., github): {Colors.RESET}").strip().lower()
            if not resource:
                print(f"{Colors.RED}[-] Resource identifier cannot be blank.{Colors.RESET}")
                continue
            
            pwd = getpass.getpass(f"{Colors.CYAN}Enter password for '{resource}': {Colors.RESET}")
            salt, nonce, ciphertext = AdvancedCryptoEngine.encrypt_data(master_password, pwd)
            db.store_credential_record(resource, salt, nonce, ciphertext)
            del pwd
            print(f"{Colors.GREEN}[+] Record for '{resource}' securely encrypted and saved.{Colors.RESET}")

        elif user_choice == "2":
            generated_pwd = generate_high_entropy_password(24)
            print(f"\n{Colors.CYAN}[🔑] High-Entropy Secret: {Colors.GREEN}{generated_pwd}{Colors.RESET}")
            synchronize_system_clipboard(generated_pwd)
            print(f"{Colors.GREEN}[+] Generated password synced to clipboard.{Colors.RESET}")
            
            threading.Thread(
                target=lambda: (time.sleep(15), purge_system_clipboard()),
                daemon=True
            ).start()
            print(f"{Colors.YELLOW}[*] Volatile timer activated. Clipboard will auto-wipe in 15 seconds...{Colors.RESET}")
            del generated_pwd

        elif user_choice == "3":
            resource = input(f"{Colors.CYAN}Enter resource target to retrieve: {Colors.RESET}").strip().lower()
            cryptographic_record = db.fetch_credential_record(resource)

            if not cryptographic_record:
                print(f"{Colors.RED}[-] Data query failure: No matches found for target '{resource}'.{Colors.RESET}")
                continue

            salt, nonce, ciphertext = cryptographic_record
            try:
                plaintext_decrypted = AdvancedCryptoEngine.decrypt_data(master_password, salt, nonce, ciphertext)
                synchronize_system_clipboard(plaintext_decrypted)
                print(f"{Colors.GREEN}[+] Password decrypted and synced to system clipboard.{Colors.RESET}")

                del plaintext_decrypted

                threading.Thread(
                    target=lambda: (time.sleep(15), purge_system_clipboard()),
                    daemon=True
                ).start()

                print(f"{Colors.YELLOW}[*] Volatile timer activated. Clipboard will auto-wipe in 15 seconds...{Colors.RESET}")

            except ValueError as crypto_err:
                print(f"{Colors.RED}[-] Execution Error: {crypto_err}{Colors.RESET}")

        elif user_choice == "4":
            resources = db.list_monitored_resources()
            if not resources:
                print(f"{Colors.YELLOW}[*] No monitored resources registered in database.{Colors.RESET}")
            else:
                print(f"\n{Colors.BLUE}--- Registered Vault Resources ---{Colors.RESET}")
                for index, res in enumerate(resources, 1):
                    print(f" {Colors.CYAN}{index}.{Colors.RESET} {res}")
                print()

        elif user_choice == "5":
            print(f"{Colors.YELLOW}[*] Purging session memory and terminating secure session. Goodbye!{Colors.RESET}")
            del master_password
            sys.exit(0)

        else:
            print(f"{Colors.RED}[-] Invalid command selection.{Colors.RESET}")


if __name__ == "__main__":
    main()
