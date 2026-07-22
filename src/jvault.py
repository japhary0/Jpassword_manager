#!/usr/bin/env python3
"""
ENTERPRISE GRADE LOCAL CRYPTOGRAPHIC VAULT (JVault Advanced - Interactive Edition)
Target Platform: Arch / Garuda Linux | Python 3.14+
Developer: Japhary Said Japhary (Cybersecurity Specialist & IT Systems Architect)
Repository: https://github.com/japhary0/Jpassword_manager.git
"""

import os
import sys
import gc
import sqlite3
import ctypes
import signal
import asyncio
import subprocess
from typing import Tuple, Optional, List
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# --- ANSI COLOR CODES & FORMATTING ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# --- HARDENING: LINUX MEMORY PROTECTION ---
def harden_process_memory():
    """Disable core dumps and memory tracing on Linux systems."""
    try:
        PR_SET_DUMPABLE = 4
        libc = ctypes.CDLL("libc.so.6")
        libc.prctl(PR_SET_DUMPABLE, 0, 0, 0, 0)
    except Exception:
        pass  # Non-Linux environments or missing libc permissions

# --- CRYPTOGRAPHIC ENGINE ---
class JVaultCrypto:
    ITERATIONS = 600_000
    CANARY_TEXT = b"JVAULT_INTEGRITY_CANARY_OK"

    @classmethod
    def derive_key(cls, master_password: str, salt: bytes) -> bytes:
        """Derive 256-bit symmetric key using PBKDF2-HMAC-SHA256."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=cls.ITERATIONS,
        )
        return kdf.derive(master_password.encode('utf-8'))

    @classmethod
    def encrypt_payload(cls, key: bytes, plaintext: bytes) -> Tuple[bytes, bytes]:
        """Encrypt payload using AES-256-GCM. Returns (IV, Ciphertext)."""
        iv = os.urandom(12)  # 96-bit nonce for GCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, plaintext, None)
        return iv, ciphertext

    @classmethod
    def decrypt_payload(cls, key: bytes, iv: bytes, ciphertext: bytes) -> Optional[bytes]:
        """Decrypt AES-256-GCM ciphertext. Returns None if tampered or wrong key."""
        try:
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(iv, ciphertext, None)
        except Exception:
            return None

# --- DATABASE MANAGEMENT & ZERO-KNOWLEDGE CANARY ---
class JVaultDatabase:
    def __init__(self, db_path: str = "encrypted_vault.db"):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    kdf_salt BLOB NOT NULL,
                    canary_iv BLOB NOT NULL,
                    canary_ciphertext BLOB NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vault_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT UNIQUE NOT NULL,
                    iv BLOB NOT NULL,
                    encrypted_data BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def is_initialized(self) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM metadata")
            return cursor.fetchone()[0] == 1

    def initialize_vault(self, master_password: str):
        salt = os.urandom(16)
        key = JVaultCrypto.derive_key(master_password, salt)
        iv, canary_cipher = JVaultCrypto.encrypt_payload(key, JVaultCrypto.CANARY_TEXT)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO metadata (id, kdf_salt, canary_iv, canary_ciphertext) VALUES (1, ?, ?, ?)",
                (salt, iv, canary_cipher)
            )
            conn.commit()

    def authenticate_master_password(self, master_password: str) -> Optional[bytes]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT kdf_salt, canary_iv, canary_ciphertext FROM metadata WHERE id = 1")
            row = cursor.fetchone()
            if not row:
                return None

            salt, canary_iv, canary_cipher = row
            derived_key = JVaultCrypto.derive_key(master_password, salt)
            decrypted_canary = JVaultCrypto.decrypt_payload(derived_key, canary_iv, canary_cipher)

            if decrypted_canary == JVaultCrypto.CANARY_TEXT:
                return derived_key
            return None

    def store_credential(self, key: bytes, service: str, secret: str):
        iv, encrypted_data = JVaultCrypto.encrypt_payload(key, secret.encode('utf-8'))
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO vault_credentials (service_name, iv, encrypted_data) VALUES (?, ?, ?)",
                (service, iv, encrypted_data)
            )
            conn.commit()

    def retrieve_credential(self, key: bytes, service: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT iv, encrypted_data FROM vault_credentials WHERE service_name = ?", (service,))
            row = cursor.fetchone()
            if not row:
                return None

            iv, encrypted_data = row
            decrypted_bytes = JVaultCrypto.decrypt_payload(key, iv, encrypted_data)
            return decrypted_bytes.decode('utf-8') if decrypted_bytes else None

    def list_services(self) -> List[Tuple[str, str]]:
        """Returns list of stored service names and their creation timestamps."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT service_name, created_at FROM vault_credentials ORDER BY service_name ASC")
            return cursor.fetchall()

    def delete_credential(self, service: str) -> bool:
        """Deletes a credential record by service name."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vault_credentials WHERE service_name = ?", (service,))
            conn.commit()
            return cursor.rowcount > 0

    def update_master_password(self, old_key: bytes, new_master_password: str) -> Optional[bytes]:
        """Re-encrypts all vault records and canary with a new master key."""
        services = self.list_services()
        decrypted_cache = []

        # Decrypt all existing items with old key
        for service, _ in services:
            secret = self.retrieve_credential(old_key, service)
            if secret is None:
                return None
            decrypted_cache.append((service, secret))

        # Generate new salt and key
        new_salt = os.urandom(16)
        new_key = JVaultCrypto.derive_key(new_master_password, new_salt)
        canary_iv, canary_cipher = JVaultCrypto.encrypt_payload(new_key, JVaultCrypto.CANARY_TEXT)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Update metadata
            cursor.execute(
                "UPDATE metadata SET kdf_salt = ?, canary_iv = ?, canary_ciphertext = ? WHERE id = 1",
                (new_salt, canary_iv, canary_cipher)
            )
            # Re-encrypt all credentials with new key
            for service, secret in decrypted_cache:
                iv, encrypted_data = JVaultCrypto.encrypt_payload(new_key, secret.encode('utf-8'))
                cursor.execute(
                    "UPDATE vault_credentials SET iv = ?, encrypted_data = ? WHERE service_name = ?",
                    (iv, encrypted_data, service)
                )
            conn.commit()

        # Wipe decrypted cache from memory
        del decrypted_cache
        gc.collect()
        return new_key

# --- ASYNC WAYLAND / X11 VOLATILE CLIPBOARD MANAGER ---
class VolatileClipboard:
    @staticmethod
    def _detect_display_server() -> str:
        """Detect whether host environment is Wayland or X11."""
        if os.environ.get("WAYLAND_DISPLAY"):
            return "wayland"
        return "x11"

    @classmethod
    async def copy_and_purge(cls, secret: str, delay_seconds: int = 15):
        """Copies secret to system clipboard and asynchronously purges it after delay."""
        display = cls._detect_display_server()
        
        # Write to clipboard
        try:
            if display == "wayland":
                proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                proc.communicate(input=secret.encode('utf-8'))
            else:
                proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                proc.communicate(input=secret.encode('utf-8'))
            print(f"\n{Colors.OKGREEN}[+] Password copied to clipboard ({display.upper()}).{Colors.ENDC} {Colors.WARNING}Auto-purging in {delay_seconds}s...{Colors.ENDC}")
        except FileNotFoundError:
            print(f"{Colors.WARNING}[!] Warning: Neither wl-copy nor xclip found. Printing suppressed for safety.{Colors.ENDC}")
            return

        # Asynchronous delay without blocking execution
        await asyncio.sleep(delay_seconds)

        # Clear clipboard
        if display == "wayland":
            subprocess.run(["wl-copy", "--clear"])
        else:
            subprocess.run(["xclip", "-selection", "clipboard", "/dev/null"])
        print(f"\n{Colors.OKCYAN}[*] Volatile memory purge executed. Clipboard cleared.{Colors.ENDC}")

# --- SECURE SHUTDOWN HANDLER ---
def safe_exit(key_ref: Optional[bytes] = None, message: str = "Safe exit completed."):
    """Safely cleans up sensitive keys, triggers garbage collection, and exits."""
    if key_ref is not None:
        del key_ref
    gc.collect()
    print(f"\n{Colors.OKCYAN}[*] {message} All volatile keys wiped from RAM.{Colors.ENDC}")
    print(f"{Colors.HEADER}====================================================={Colors.ENDC}")
    sys.exit(0)

# --- CLI INTERFACE & MAIN ROUTINE ---
async def main():
    harden_process_memory()
    db = JVaultDatabase()

    print(f"{Colors.HEADER}{Colors.BOLD}====================================================={Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}      JVAULT: LOCAL ENTERPRISE CRYPTO ENGINE         {Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}====================================================={Colors.ENDC}")

    if not db.is_initialized():
        print(f"{Colors.WARNING}[!] Uninitialized Vault Detected.{Colors.ENDC}")
        master_pw = input(f"{Colors.BOLD}Set Master Password: {Colors.ENDC}").strip()
        db.initialize_vault(master_pw)
        print(f"{Colors.OKGREEN}[+] Vault initialized successfully with 600k PBKDF2 iterations.{Colors.ENDC}\n")

    master_pw = input(f"{Colors.BOLD}Enter Master Password: {Colors.ENDC}").strip()
    key = db.authenticate_master_password(master_pw)

    if not key:
        print(f"{Colors.FAIL}[-] Authentication Failed: Invalid Master Password or Corrupted Canary.{Colors.ENDC}")
        safe_exit(None, "Authentication failed. Exiting...")

    # Wipe raw password string immediately
    del master_pw
    gc.collect()

    print(f"{Colors.OKGREEN}[+] Zero-Knowledge Canary Verified. Vault Unlocked.{Colors.ENDC}")

    # Interactive Loop
    while True:
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}--- MAIN MENU ---{Colors.ENDC}")
        print(f"[{Colors.OKCYAN}1{Colors.ENDC}] Store Credential")
        print(f"[{Colors.OKCYAN}2{Colors.ENDC}] Retrieve Credential (Copy to Clipboard)")
        print(f"[{Colors.OKCYAN}3{Colors.ENDC}] List All Stored Services")
        print(f"[{Colors.OKCYAN}4{Colors.ENDC}] Delete Credential")
        print(f"[{Colors.OKCYAN}5{Colors.ENDC}] Change Master Password")
        print(f"[{Colors.OKCYAN}6{Colors.ENDC}] Safe Exit")

        choice = input(f"\n{Colors.BOLD}Select an option (1-6): {Colors.ENDC}").strip()

        if choice == '1':
            service = input(f"{Colors.BOLD}Enter Service Name (e.g., github): {Colors.ENDC}").strip()
            secret = input(f"{Colors.BOLD}Enter Secret/Password: {Colors.ENDC}").strip()
            if service and secret:
                db.store_credential(key, service, secret)
                print(f"{Colors.OKGREEN}[+] Encrypted payload stored for '{service}'.{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}[!] Service name and secret cannot be empty.{Colors.ENDC}")

        elif choice == '2':
            service = input(f"{Colors.BOLD}Enter Service Name to retrieve: {Colors.ENDC}").strip()
            secret = db.retrieve_credential(key, service)
            if secret:
                await VolatileClipboard.copy_and_purge(secret, delay_seconds=15)
                del secret
                gc.collect()
            else:
                print(f"{Colors.FAIL}[-] Service not found or integrity check failed.{Colors.ENDC}")

        elif choice == '3':
            services = db.list_services()
            if not services:
                print(f"{Colors.WARNING}[!] No credentials currently stored in vault.{Colors.ENDC}")
            else:
                print(f"\n{Colors.BOLD}Stored Services ({len(services)} total):{Colors.ENDC}")
                print(f"{'Service Name':<25} | {'Created At'}")
                print("-" * 45)
                for svc, created in services:
                    print(f"{svc:<25} | {created}")

        elif choice == '4':
            service = input(f"{Colors.BOLD}Enter Service Name to DELETE: {Colors.ENDC}").strip()
            confirm = input(f"{Colors.FAIL}Are you sure you want to delete '{service}'? (y/N): {Colors.ENDC}").strip().lower()
            if confirm == 'y':
                if db.delete_credential(service):
                    print(f"{Colors.OKGREEN}[+] Credential for '{service}' deleted.{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}[-] Service '{service}' not found.{Colors.ENDC}")
            else:
                print(f"{Colors.OKCYAN}[*] Deletion cancelled.{Colors.ENDC}")

        elif choice == '5':
            new_pw = input(f"{Colors.BOLD}Enter NEW Master Password: {Colors.ENDC}").strip()
            confirm_pw = input(f"{Colors.BOLD}Confirm NEW Master Password: {Colors.ENDC}").strip()
            if new_pw == confirm_pw and new_pw:
                updated_key = db.update_master_password(key, new_pw)
                if updated_key:
                    del key
                    key = updated_key
                    print(f"{Colors.OKGREEN}[+] Master Password updated successfully. Vault re-encrypted.{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}[-] Failed to update master password.{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[-] Passwords do not match or are empty.{Colors.ENDC}")

        elif choice == '6':
            safe_exit(key, "User requested shutdown.")

        else:
            print(f"{Colors.WARNING}[!] Invalid option. Please enter a number between 1 and 6.{Colors.ENDC}")

if __name__ == "__main__":
    def signal_handler(sig, frame):
        safe_exit(None, "Force exit signal received.")

    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())
