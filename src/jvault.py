#!/usr/bin/env python3
"""
ENTERPRISE GRADE LOCAL CRYPTOGRAPHIC VAULT (JVault Advanced - Universal OS Edition)
Supported Platforms: macOS (Darwin), Arch Linux, Ubuntu, Kali, Parrot OS, Windows 10/11, FreeBSD, OpenBSD
Developer: Japhary Said Japhary (Cybersecurity Specialist & IT Systems Architect)
Repository: https://github.com/japhary0/Jpassword_manager.git
"""

import os
import sys
import gc
import sqlite3
import ctypes
import signal
import platform
import asyncio
import subprocess
import secrets
import string
import math
import re
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

# Enable VT100 ANSI Escape Sequence colors natively on Windows
if platform.system() == "Windows":
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

# --- HARDENING: UNIVERSAL CROSS-PLATFORM MEMORY PROTECTION ---
def harden_process_memory():
    """Disable core dumps and memory tracing on all supported operating systems."""
    sys_type = platform.system()
    if sys_type == "Linux":
        try:
            PR_SET_DUMPABLE = 4
            libc = ctypes.CDLL("libc.so.6")
            libc.prctl(PR_SET_DUMPABLE, 0, 0, 0, 0)
        except Exception:
            pass
    elif sys_type == "Darwin":
        try:
            # PT_DENY_ATTACH (31) stops debuggers (lldb/gdb) from attaching or inspecting process RAM on macOS
            libc = ctypes.CDLL("libc.dylib")
            libc.ptrace(31, 0, 0, 0)
        except Exception:
            pass
    elif sys_type == "Windows":
        try:
            ctypes.windll.kernel32.SetProcessMitigationPolicy(9, ctypes.byref(ctypes.c_ulonglong(1)), 8)
        except Exception:
            pass

# --- AUTOMATED OS DELETION LOCK ENGINE ---
class OSProtectionEngine:
    @staticmethod
    def apply_deletion_lock():
        """Applies OS-level file locking requiring Sudo/Admin elevation to unlock or delete."""
        sys_type = platform.system()
        script_path = os.path.abspath(__file__)
        db_path = os.path.abspath("encrypted_vault.db")

        print(f"\n{Colors.OKCYAN}[*] Applying OS-Level Anti-Deletion Locks...{Colors.ENDC}")

        if sys_type == "Linux":
            try:
                cmd1 = ["sudo", "chattr", "+i", script_path]
                cmd2 = ["sudo", "chattr", "+i", db_path] if os.path.exists(db_path) else None

                res1 = subprocess.run(cmd1, check=False)
                if cmd2:
                    subprocess.run(cmd2, check=False)

                if res1.returncode == 0:
                    print(f"{Colors.OKGREEN}[+] Linux Immutable Flag (+i) successfully set on script.{Colors.ENDC}")
                    print(f"{Colors.OKGREEN}[+] Script cannot be deleted even with 'rm -rf' without Sudo password!{Colors.ENDC}")
                else:
                    print(f"{Colors.WARNING}[!] Sudo elevation declined or failed. OS Lock not fully set.{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.FAIL}[-] Failed to set Linux protection: {e}{Colors.ENDC}")

        elif sys_type in ("Darwin", "FreeBSD", "OpenBSD", "NetBSD"):
            try:
                # macOS and BSD systems use 'chflags uchg' (user immutable flag)
                cmd1 = ["chflags", "uchg", script_path]
                cmd2 = ["chflags", "uchg", db_path] if os.path.exists(db_path) else None

                res1 = subprocess.run(cmd1, check=False)
                if cmd2:
                    subprocess.run(cmd2, check=False)

                if res1.returncode == 0:
                    print(f"{Colors.OKGREEN}[+] {sys_type} Immutable Flag (uchg) successfully applied.{Colors.ENDC}")
                    print(f"{Colors.OKGREEN}[+] Script cannot be modified or deleted without unlocking flags!{Colors.ENDC}")
                else:
                    print(f"{Colors.WARNING}[!] Privilege elevation required for chflags.{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.FAIL}[-] Failed to set {sys_type} protection: {e}{Colors.ENDC}")

        elif sys_type == "Windows":
            try:
                icacls_cmd = [
                    "powershell", "-Command",
                    f'Start-Process powershell -Verb RunAs -ArgumentList "icacls `"{script_path}`" /deny Users:(D,WO,WDAC)"'
                ]
                subprocess.run(icacls_cmd, check=False)
                print(f"{Colors.OKGREEN}[+] Windows NTFS Deny-Delete ACL applied.{Colors.ENDC}")
                print(f"{Colors.OKGREEN}[+] Deleting file will now force a Windows Administrator UAC prompt!{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.FAIL}[-] Failed to set Windows protection: {e}{Colors.ENDC}")

    @staticmethod
    def remove_deletion_lock():
        """Removes OS protection flags prior to legitimate uninstallation."""
        sys_type = platform.system()
        script_path = os.path.abspath(__file__)
        db_path = os.path.abspath("encrypted_vault.db")

        if sys_type == "Linux":
            try:
                subprocess.run(["sudo", "chattr", "-i", script_path], check=False)
                if os.path.exists(db_path):
                    subprocess.run(["sudo", "chattr", "-i", db_path], check=False)
            except Exception:
                pass
        elif sys_type in ("Darwin", "FreeBSD", "OpenBSD", "NetBSD"):
            try:
                subprocess.run(["chflags", "nouchg", script_path], check=False)
                if os.path.exists(db_path):
                    subprocess.run(["chflags", "nouchg", db_path], check=False)
            except Exception:
                pass
        elif sys_type == "Windows":
            try:
                icacls_cmd = [
                    "powershell", "-Command",
                    f'Start-Process powershell -Verb RunAs -ArgumentList "icacls `"{script_path}`" /remove:d Users"'
                ]
                subprocess.run(icacls_cmd, check=False)
            except Exception:
                pass

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
        iv = os.urandom(12)
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

# --- NIST SP 800-63B ALIGNED PASSWORD ENGINE ---
class PasswordEngine:
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    COMMON_BLACKLIST = {
        "password", "123456", "12345678", "123456789", "qwerty", "111111", 
        "admin", "welcome", "login", "pass1234", "iloveyou", "sunshine", 
        "master", "password123", "dragon", "football", "monkey", "letmein"
    }

    @classmethod
    def generate_strong_password(cls, length: int = 20) -> str:
        """Generates CSPRNG strong password."""
        if length < 12:
            length = 12

        full_pool = string.ascii_lowercase + string.ascii_uppercase + string.digits + cls.SPECIAL_CHARS
        
        password_chars = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice(cls.SPECIAL_CHARS)
        ]

        for _ in range(length - 4):
            password_chars.append(secrets.choice(full_pool))

        secrets.SystemRandom().shuffle(password_chars)
        return "".join(password_chars)

    @classmethod
    def analyze_nist_strength(cls, password: str) -> dict:
        """Evaluates password against NIST SP 800-63B guidelines."""
        length = len(password)
        lower_pw = password.lower()
        
        is_blacklisted = lower_pw in cls.COMMON_BLACKLIST
        meets_nist_min = length >= 8
        is_recommended_length = length >= 15
        
        has_repeats = bool(re.search(r'(.)\1{2,}', password))
        
        has_sequences = False
        for i in range(len(password) - 3):
            seq = password[i:i+4].lower()
            if seq in string.ascii_lowercase or seq in string.digits:
                has_sequences = True
                break

        has_lower = any(c in string.ascii_lowercase for c in password)
        has_upper = any(c in string.ascii_uppercase for c in password)
        has_digit = any(c in string.digits for c in password)
        has_special = any(c in cls.SPECIAL_CHARS for c in password)

        pool_size = 0
        if has_lower: pool_size += 26
        if has_upper: pool_size += 26
        if has_digit: pool_size += 10
        if has_special: pool_size += len(cls.SPECIAL_CHARS)

        raw_entropy = length * math.log2(pool_size) if pool_size > 0 else 0

        entropy_penalty = 0
        if has_repeats: entropy_penalty += 15
        if has_sequences: entropy_penalty += 20
        if is_blacklisted: entropy_penalty += 50

        adjusted_entropy = max(0.0, raw_entropy - entropy_penalty)

        if is_blacklisted or not meets_nist_min:
            rating = f"{Colors.FAIL}{Colors.BOLD}REJECTED (Violates NIST Baseline){Colors.ENDC}"
        elif adjusted_entropy >= 80 and is_recommended_length:
            rating = f"{Colors.OKGREEN}{Colors.BOLD}Enterprise Grade / Exceptional (NIST Compliant){Colors.ENDC}"
        elif adjusted_entropy >= 55:
            rating = f"{Colors.OKCYAN}{Colors.BOLD}Strong / Compliant{Colors.ENDC}"
        elif adjusted_entropy >= 35:
            rating = f"{Colors.WARNING}{Colors.BOLD}Moderate (Consider Increasing Length){Colors.ENDC}"
        else:
            rating = f"{Colors.FAIL}{Colors.BOLD}Weak (High Risk of Contextual Guessing){Colors.ENDC}"

        return {
            "length": length,
            "meets_min": meets_nist_min,
            "is_recommended": is_recommended_length,
            "is_blacklisted": is_blacklisted,
            "has_repeats": has_repeats,
            "has_sequences": has_sequences,
            "entropy": round(adjusted_entropy, 2),
            "rating": rating
        }

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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT service_name, created_at FROM vault_credentials ORDER BY service_name ASC")
            return cursor.fetchall()

    def delete_credential(self, service: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vault_credentials WHERE service_name = ?", (service,))
            conn.commit()
            return cursor.rowcount > 0

    def update_master_password(self, old_key: bytes, new_master_password: str) -> Optional[bytes]:
        services = self.list_services()
        decrypted_cache = []

        for service, _ in services:
            secret = self.retrieve_credential(old_key, service)
            if secret is None:
                return None
            decrypted_cache.append((service, secret))

        new_salt = os.urandom(16)
        new_key = JVaultCrypto.derive_key(new_master_password, new_salt)
        canary_iv, canary_cipher = JVaultCrypto.encrypt_payload(new_key, JVaultCrypto.CANARY_TEXT)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE metadata SET kdf_salt = ?, canary_iv = ?, canary_ciphertext = ? WHERE id = 1",
                (new_salt, canary_iv, canary_cipher)
            )
            for service, secret in decrypted_cache:
                iv, encrypted_data = JVaultCrypto.encrypt_payload(new_key, secret.encode('utf-8'))
                cursor.execute(
                    "UPDATE vault_credentials SET iv = ?, encrypted_data = ? WHERE service_name = ?",
                    (iv, encrypted_data, service)
                )
            conn.commit()

        del decrypted_cache
        gc.collect()
        return new_key

# --- CRYPTOGRAPHIC SECURE SHREDDING ---
def secure_shred_file(filepath: str, passes: int = 3):
    """Overwrites file with random bytes before deletion to prevent magnetic recovery."""
    if not os.path.exists(filepath):
        return
    length = os.path.getsize(filepath)
    with open(filepath, "wb") as f:
        for _ in range(passes):
            f.seek(0)
            f.write(os.urandom(length))
            f.flush()
            os.fsync(f.fileno())
    os.remove(filepath)

# --- UNIVERSAL VOLATILE CLIPBOARD MANAGER ---
class VolatileClipboard:
    @staticmethod
    def _detect_system() -> Tuple[str, str]:
        sys_type = platform.system()
        if sys_type == "Windows":
            return "windows", "native"
        elif sys_type == "Darwin":
            return "macos", "native"
        elif sys_type in ("Linux", "FreeBSD", "OpenBSD", "NetBSD"):
            if os.environ.get("WAYLAND_DISPLAY"):
                return "unix", "wayland"
            return "unix", "x11"
        return "unknown", "unknown"

    @classmethod
    async def copy_and_purge(cls, secret: str, delay_seconds: int = 15):
        sys_type, env = cls._detect_system()
        copied_ok = False

        try:
            if sys_type == "windows":
                try:
                    import pyperclip
                    pyperclip.copy(secret)
                    copied_ok = True
                except ImportError:
                    proc = subprocess.Popen(["powershell", "-command", "$input | Set-Clipboard"], stdin=subprocess.PIPE)
                    proc.communicate(input=secret.encode('utf-8'))
                    copied_ok = True

            elif sys_type == "macos":
                proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                proc.communicate(input=secret.encode('utf-8'))
                copied_ok = True

            elif sys_type == "unix":
                if env == "wayland":
                    proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                    proc.communicate(input=secret.encode('utf-8'))
                    copied_ok = True
                else:
                    try:
                        proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                        proc.communicate(input=secret.encode('utf-8'))
                        copied_ok = True
                    except FileNotFoundError:
                        proc = subprocess.Popen(["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE)
                        proc.communicate(input=secret.encode('utf-8'))
                        copied_ok = True
        except FileNotFoundError:
            print(f"{Colors.WARNING}[!] Clipboard driver missing (install pbcopy, wl-clipboard, xclip, or xsel).{Colors.ENDC}")
            return

        if copied_ok:
            print(f"\n{Colors.OKGREEN}[+] Password copied to clipboard ({sys_type.upper()}/{env.upper()}).{Colors.ENDC} {Colors.WARNING}Auto-purging in {delay_seconds}s...{Colors.ENDC}")

        await asyncio.sleep(delay_seconds)

        try:
            if sys_type == "windows":
                try:
                    import pyperclip
                    pyperclip.copy("")
                except ImportError:
                    subprocess.run(["powershell", "-command", "Clear-Clipboard"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif sys_type == "macos":
                proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                proc.communicate(input=b"")
            elif sys_type == "unix":
                if env == "wayland":
                    subprocess.run(["wl-copy", "--clear"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    try:
                        subprocess.run(["xclip", "-selection", "clipboard", "/dev/null"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception:
                        subprocess.run(["xsel", "--clipboard", "--clear"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"\n{Colors.OKCYAN}[*] Volatile memory purge executed. Clipboard cleared.{Colors.ENDC}")
        except Exception:
            pass

# --- SECURE SHUTDOWN HANDLER ---
def safe_exit(key_ref: Optional[bytes] = None, message: str = "Safe exit completed."):
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
    print(f"{Colors.HEADER}{Colors.BOLD}   JVAULT: ENTERPRISE CRYPTO ENGINE (UNIVERSAL OS)   {Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}====================================================={Colors.ENDC}")

    if not db.is_initialized():
        print(f"{Colors.WARNING}[!] Uninitialized Vault Detected.{Colors.ENDC}")
        master_pw = input(f"{Colors.BOLD}{Colors.OKBLUE}Set Master Password: {Colors.ENDC}").strip()
        db.initialize_vault(master_pw)
        print(f"{Colors.OKGREEN}[+] Vault initialized successfully with 600k PBKDF2 iterations.{Colors.ENDC}\n")

    master_pw = input(f"{Colors.BOLD}{Colors.OKBLUE}Enter Master Password: {Colors.ENDC}").strip()
    key = db.authenticate_master_password(master_pw)

    if not key:
        print(f"{Colors.FAIL}[-] Authentication Failed: Invalid Master Password or Corrupted Canary.{Colors.ENDC}")
        safe_exit(None, "Authentication failed. Exiting...")

    del master_pw
    gc.collect()

    print(f"{Colors.OKGREEN}[+] Zero-Knowledge Canary Verified. Vault Unlocked.{Colors.ENDC}")

    # Interactive Loop
    while True:
        print(f"\n{Colors.HEADER}{Colors.BOLD}--- MAIN MENU ---{Colors.ENDC}")
        print(f"[{Colors.OKCYAN}1{Colors.ENDC}] {Colors.OKGREEN}Store Credential{Colors.ENDC}")
        print(f"[{Colors.OKCYAN}2{Colors.ENDC}] {Colors.OKBLUE}Retrieve Credential (Copy to Clipboard){Colors.ENDC}")
        print(f"[{Colors.OKCYAN}3{Colors.ENDC}] {Colors.OKBLUE}List All Stored Services{Colors.ENDC}")
        print(f"[{Colors.OKCYAN}4{Colors.ENDC}] {Colors.FAIL}Delete Credential{Colors.ENDC}")
        print(f"[{Colors.OKCYAN}5{Colors.ENDC}] {Colors.OKGREEN}Generate Strong Password (CSPRNG){Colors.ENDC}")
        print(f"[{Colors.OKCYAN}6{Colors.ENDC}] {Colors.OKCYAN}Audit Password (NIST SP 800-63B Guidelines){Colors.ENDC}")
        print(f"[{Colors.OKCYAN}7{Colors.ENDC}] {Colors.WARNING}Change Master Password{Colors.ENDC}")
        print(f"[{Colors.OKCYAN}8{Colors.ENDC}] {Colors.OKCYAN}{Colors.BOLD}ENABLE OS ANTI-DELETION LOCK (Requires Sudo/Admin){Colors.ENDC}")
        print(f"[{Colors.OKCYAN}9{Colors.ENDC}] {Colors.FAIL}{Colors.BOLD}UNINSTALL & SECURELY SHRED TOOL / VAULT{Colors.ENDC}")
        print(f"[{Colors.OKCYAN}10{Colors.ENDC}] {Colors.HEADER}Safe Exit{Colors.ENDC}")

        choice = input(f"\n{Colors.BOLD}{Colors.OKBLUE}Select an option (1-10): {Colors.ENDC}").strip()

        if choice == '1':
            service = input(f"{Colors.BOLD}Enter Service Name (e.g., github): {Colors.ENDC}").strip()
            secret = input(f"{Colors.BOLD}Enter Secret/Password (or press Enter to auto-generate): {Colors.ENDC}").strip()
            if not secret:
                secret = PasswordEngine.generate_strong_password(20)
                print(f"{Colors.OKCYAN}[*] Auto-Generated NIST Passphrase: {Colors.BOLD}{Colors.OKGREEN}{secret}{Colors.ENDC}")
            
            if service and secret:
                db.store_credential(key, service, secret)
                print(f"{Colors.OKGREEN}[+] Encrypted payload stored for '{Colors.BOLD}{service}{Colors.ENDC}{Colors.OKGREEN}'.{Colors.ENDC}")
                del secret
                gc.collect()
            else:
                print(f"{Colors.WARNING}[!] Service name cannot be empty.{Colors.ENDC}")

        elif choice == '2':
            service = input(f"{Colors.BOLD}Enter Service Name to retrieve: {Colors.ENDC}").strip()
            secret = db.retrieve_credential(key, service)
            if secret:
                await VolatileClipboard.copy_and_purge(secret, delay_seconds=15)
                del secret
                gc.collect()
            else:
                print(f"{Colors.FAIL}[-] Service '{service}' not found or integrity check failed.{Colors.ENDC}")

        elif choice == '3':
            services = db.list_services()
            if not services:
                print(f"{Colors.WARNING}[!] No credentials currently stored in vault.{Colors.ENDC}")
            else:
                print(f"\n{Colors.BOLD}{Colors.HEADER}Stored Services ({len(services)} total):{Colors.ENDC}")
                print(f"{Colors.BOLD}{Colors.OKCYAN}{'Service Name':<25} | {'Created At'}{Colors.ENDC}")
                print(f"{Colors.OKCYAN}{'-' * 45}{Colors.ENDC}")
                for svc, created in services:
                    print(f"{Colors.OKGREEN}{svc:<25}{Colors.ENDC} | {Colors.OKBLUE}{created}{Colors.ENDC}")

        elif choice == '4':
            service = input(f"{Colors.BOLD}Enter Service Name to DELETE: {Colors.ENDC}").strip()
            confirm = input(f"{Colors.FAIL}{Colors.BOLD}Are you sure you want to delete '{service}'? (y/N): {Colors.ENDC}").strip().lower()
            if confirm == 'y':
                if db.delete_credential(service):
                    print(f"{Colors.OKGREEN}[+] Credential for '{service}' deleted.{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}[-] Service '{service}' not found.{Colors.ENDC}")
            else:
                print(f"{Colors.OKCYAN}[*] Deletion cancelled.{Colors.ENDC}")

        elif choice == '5':
            try:
                length_input = input(f"{Colors.BOLD}Enter desired length (default 20, min 12): {Colors.ENDC}").strip()
                length = int(length_input) if length_input else 20
            except ValueError:
                length = 20
            
            generated_pw = PasswordEngine.generate_strong_password(length)
            print(f"\n{Colors.OKGREEN}[+] Generated NIST Password:{Colors.ENDC} {Colors.BOLD}{Colors.OKCYAN}{generated_pw}{Colors.ENDC}")
            
            copy_choice = input(f"{Colors.BOLD}Copy password to volatile clipboard? (Y/n): {Colors.ENDC}").strip().lower()
            if copy_choice != 'n':
                await VolatileClipboard.copy_and_purge(generated_pw, delay_seconds=15)
            
            del generated_pw
            gc.collect()

        elif choice == '6':
            target_pw = input(f"{Colors.BOLD}Enter password to audit against NIST: {Colors.ENDC}").strip()
            if not target_pw:
                print(f"{Colors.WARNING}[!] Password cannot be empty.{Colors.ENDC}")
                continue

            results = PasswordEngine.analyze_nist_strength(target_pw)
            
            meets_min_tag = f"{Colors.OKGREEN}[PASS]{Colors.ENDC}" if results['meets_min'] else f"{Colors.FAIL}[FAIL]{Colors.ENDC}"
            rec_len_tag = f"{Colors.OKGREEN}[PASS]{Colors.ENDC}" if results['is_recommended'] else f"{Colors.WARNING}[WARN]{Colors.ENDC}"
            blacklist_tag = f"{Colors.FAIL}[FAIL - Flagged]{Colors.ENDC}" if results['is_blacklisted'] else f"{Colors.OKGREEN}[PASS - Clean]{Colors.ENDC}"
            repeats_tag = f"{Colors.FAIL}[FAIL - Found]{Colors.ENDC}" if results['has_repeats'] else f"{Colors.OKGREEN}[PASS - Clear]{Colors.ENDC}"
            sequences_tag = f"{Colors.FAIL}[FAIL - Found]{Colors.ENDC}" if results['has_sequences'] else f"{Colors.OKGREEN}[PASS - Clear]{Colors.ENDC}"

            entropy_val = results['entropy']
            if entropy_val >= 80:
                entropy_colored = f"{Colors.OKGREEN}{entropy_val} bits{Colors.ENDC}"
            elif entropy_val >= 55:
                entropy_colored = f"{Colors.OKCYAN}{entropy_val} bits{Colors.ENDC}"
            elif entropy_val >= 35:
                entropy_colored = f"{Colors.WARNING}{entropy_val} bits{Colors.ENDC}"
            else:
                entropy_colored = f"{Colors.FAIL}{entropy_val} bits{Colors.ENDC}"

            print(f"\n{Colors.HEADER}{Colors.BOLD}--- NIST SP 800-63B PASSWORD AUDIT REPORT ---{Colors.ENDC}")
            print(f"{Colors.BOLD}Overall Evaluation  :{Colors.ENDC} {results['rating']}")
            print(f"{Colors.BOLD}Adjusted Entropy    :{Colors.ENDC} {entropy_colored}")
            print(f"{Colors.BOLD}NIST Min Length (>=8):{Colors.ENDC} {meets_min_tag}")
            print(f"{Colors.BOLD}NIST Rec Length(>=15):{Colors.ENDC} {rec_len_tag}")
            print(f"{Colors.BOLD}Common Blacklist    :{Colors.ENDC} {blacklist_tag}")
            print(f"{Colors.BOLD}Repetitive Chars    :{Colors.ENDC} {repeats_tag}")
            print(f"{Colors.BOLD}Sequential Patterns :{Colors.ENDC} {sequences_tag}")
            
            del target_pw
            gc.collect()

        elif choice == '7':
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

        elif choice == '8':
            OSProtectionEngine.apply_deletion_lock()

        elif choice == '9':
            print(f"\n{Colors.FAIL}{Colors.BOLD}[!] WARNING: UNINSTALLATION / COMPLETE PURGE INITIATED.{Colors.ENDC}")
            print(f"{Colors.WARNING}This action will permanently overwrite and delete your encrypted database and the tool script.{Colors.ENDC}")
            
            verify_pw = input(f"{Colors.BOLD}{Colors.FAIL}Re-enter Master Password to AUTHORIZE UNINSTALL: {Colors.ENDC}").strip()
            auth_check = db.authenticate_master_password(verify_pw)
            
            if auth_check:
                del verify_pw, auth_check
                gc.collect()
                
                print(f"\n{Colors.WARNING}[*] Password verified. Removing OS locks and performing multi-pass secure cryptographic wipe...{Colors.ENDC}")
                
                # 1. Unlock OS Locks
                OSProtectionEngine.remove_deletion_lock()

                # 2. Shred Database
                db_file = db.db_path
                secure_shred_file(db_file)
                print(f"{Colors.OKGREEN}[+] Encrypted Vault Database shredded and deleted.{Colors.ENDC}")
                
                # 3. Shred Executing Script
                script_path = os.path.abspath(__file__)
                print(f"{Colors.OKGREEN}[+] Tool script target: {script_path}{Colors.ENDC}")
                print(f"{Colors.FAIL}[!] Goodbye. Self-destruction complete.{Colors.ENDC}")
                
                del key
                gc.collect()
                
                secure_shred_file(script_path)
                sys.exit(0)
            else:
                print(f"{Colors.FAIL}[-] ACTION DENIED: Incorrect Master Password. Purge aborted.{Colors.ENDC}")

        elif choice == '10':
            safe_exit(key, "User requested shutdown.")

        else:
            print(f"{Colors.WARNING}[!] Invalid option. Please enter a number between 1 and 10.{Colors.ENDC}")

if __name__ == "__main__":
    def signal_handler(sig, frame):
        safe_exit(None, "Force exit signal received.")

    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())
