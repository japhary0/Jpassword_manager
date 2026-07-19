import os
import sys
import time
import sqlite3
import getpass
import secrets
import string
import subprocess
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Define the local SQLite database file name
DB_FILE = "encrypted_vault.db"

class AdvancedCryptoEngine:
    """
    Handles all mathematical cryptographic mechanics including key derivation,
    authenticated encryption, and integrity verification.
    """
    
    @staticmethod
    def derive_cryptographic_key(master_password: str, salt: bytes) -> bytes:
        """
        Uses PBKDF2-HMAC-SHA256 with 600,000 iterations to stretch the master password.
        This hardens the password against GPU-accelerated brute-force attacks.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes output = 256 bits (Perfect for AES-256)
            salt=salt,
            iterations=600000,
        )
        return kdf.derive(master_password.encode())

    @staticmethod
    def encrypt_data(master_password: str, plaintext_string: str) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypts a string using AES-256-GCM (Authenticated Encryption).
        Generates a unique 16-byte salt and a 12-byte initialization vector (nonce).
        """
        # Cryptographically secure random generation for salt and nonce
        salt = os.urandom(16)
        nonce = os.urandom(12)
        
        # Derive the ephemeral key
        key = AdvancedCryptoEngine.derive_cryptographic_key(master_password, salt)
        
        # Execute symmetric authenticated encryption
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext_string.encode(), None)
        
        # Secure Practice: Explicitly delete key reference from RAM allocation
        del key
        return salt, nonce, ciphertext

    @staticmethod
    def decrypt_data(master_password: str, salt: bytes, nonce: bytes, ciphertext: bytes) -> str:
        """
        Decrypts AES-256-GCM ciphertext. If the data has been altered/tampered with,
        or if the master password is wrong, it raises a strict ValueError.
        """
        key = AdvancedCryptoEngine.derive_cryptographic_key(master_password, salt)
        aesgcm = AESGCM(key)
        try:
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            plaintext = decrypted_bytes.decode()
            del key  # Wipe key reference immediately upon success
            return plaintext
        except Exception as e:
            del key  # Wipe key reference on failure to maintain RAM safety
            raise ValueError("Decryption integrity verification failed! (Wrong Master Password or Tampered Data)") from e


class DatabaseManager:
    """
    Controls relational database connectivity, initialization schemas,
    and structured data storage pipelines.
    """
    def __init__(self, database_path: str):
        self.db_path = database_path
        self._initialize_database_tables()

    def _initialize_database_tables(self):
        """Creates the relational framework with strict structural abstraction constraints."""
        with sqlite3.connect(self.db_path) as conn:
            # Table 1: Stores metadata validation signature to safely verify the user's master password
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vault_canary (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    salt BLOB NOT NULL,
                    nonce BLOB NOT NULL,
                    canary_ciphertext BLOB NOT NULL
                )
            """)
            # Table 2: Stores the actual encrypted login credentials
            conn.execute("""
                CREATE TABLE IF NOT EXISTS safe_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_target TEXT UNIQUE NOT NULL,
                    salt BLOB NOT NULL,
                    nonce BLOB NOT NULL,
                    ciphertext BLOB NOT NULL
                )
            """)
            conn.commit()

    def initialize_or_verify_master(self, master_password: str) -> bool:
        """
        Checks if a master password exists. If not, it creates a dynamic verification canary.
        If it exists, it tries to decrypt it to grant or deny system access.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT salt, nonce, canary_ciphertext FROM vault_canary WHERE id = 1")
            record = cursor.fetchone()
            
            if not record:
                print("\033[1;33m[*] Creating a new secure local vault database...\033[0m")
                # Encrypt a static test string (Canary) using the master password
                salt, nonce, ciphertext = AdvancedCryptoEngine.encrypt_data(master_password, "VAULT_ACCESS_GRANTED")
                conn.execute(
                    "INSERT INTO vault_canary (id, salt, nonce, canary_ciphertext) VALUES (1, ?, ?, ?)",
                    (salt, nonce, ciphertext)
                )
                conn.commit()
                return True
            else:
                salt, nonce, ciphertext = record
                try:
                    # Attempt to decrypt the canary string to verify password validity
                    AdvancedCryptoEngine.decrypt_data(master_password, salt, nonce, ciphertext)
                    return True
                except ValueError:
                    return False

    def store_credential_record(self, resource: str, salt: bytes, nonce: bytes, ciphertext: bytes):
        """Commits the secure cryptographic outputs cleanly into the system database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO safe_credentials (resource_target, salt, nonce, ciphertext) VALUES (?, ?, ?, ?)",
                (resource.lower(), salt, nonce, ciphertext)
            )
            conn.commit()

    def fetch_credential_record(self, resource: str) -> Optional[Tuple[bytes, bytes, bytes]]:
        """Queries database for cryptographic blocks matching a specific application/website."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT salt, nonce, ciphertext FROM safe_credentials WHERE resource_target = ?", (resource.lower(),))
            return cursor.fetchone()

    def retrieve_all_resource_names(self):
        """Lists targeted application profiles without leaking cryptographic payloads."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT resource_target FROM safe_credentials")
            return [row[0] for row in cursor.fetchall()]


def generate_high_entropy_password(length: int = 20) -> str:
    """
    Generates a secure password using Python's `secrets` engine.
    Ensures at least one uppercase letter, one lowercase letter, one digit, and one special character.
    """
    if length < 14:
        length = 14  # Enforce minimum industry-standard length threshold
        
    character_universe = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    while True:
        proposed_password = ''.join(secrets.choice(character_universe) for _ in range(length))
        # Ensure password complies with modern, strict security profiling policies
        if (any(c.islower() for c in proposed_password)
                and any(c.isupper() for c in proposed_password)
                and any(c.isdigit() for c in proposed_password)
                and any(c in "!@#$%^&*()-_=+" for c in proposed_password)):
            return proposed_password


def synchronize_system_clipboard(decrypted_text: str):
    """
    Interfaces natively with display architectures.
    Automatically detects Wayland or X11 to securely inject text into the system clipboard.
    """
    try:
        if os.environ.get("WAYLAND_DISPLAY"):
            # Execute native Wayland copy protocol
            process = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=decrypted_text)
        else:
            # Fallback to legacy X11 clipboard pipeline architecture
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=decrypted_text)
        print("\033[1;32m[+] Password successfully synced to system clipboard.\033[0m")
    except Exception:
        print("\033[1;31m[-] Clipboard system error: Install xclip or wl-clipboard via pacman.\033[0m")


def purge_system_clipboard():
    """Wipes the clipboard buffer to mitigate memory sniffing exposures."""
    try:
        if os.environ.get("WAYLAND_DISPLAY"):
            subprocess.run(['wl-copy', '--clear'], check=True)
        else:
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, text=True)
            process.communicate(input="")
        print("\033[1;36m[⚡] System clipboard successfully flushed for memory optimization.\033[0m")
    except Exception:
        pass


def display_secure_banner():
    """Prints a high-visibility, colored ASCII Lock Banner tracking developer state."""
    # We removed the 'r'. Now we double the backslashes (\\) 
    # only where they are part of the ASCII art drawing.
    banner = """\033[1;35m
                               .--------.
                              / .------. \\
                             / /        \\ \\
                             | |        | |
                           __| |________| |_
                         \033[1;32m [=================]
                          |     \033[1;36mMR_J.FO     \033[1;32m|
                          |       \033[1;33m[  ]      \033[1;32m|
                          |       \033[1;33m/  \\      \033[1;32m|
                          |      \033[1;33m'----'     \033[1;32m|
                          |                 |
                          [=================]\033[0m
    \033[1;32m=================================================================
         🛡️  ADVANCED PRIVACY VAULT CORE — HIGH SECURITY ENGINE      
    =================================================================\033[0m"""
    print(banner)

def main():
    # Instantiate the database management layer
    db = DatabaseManager(DB_FILE)
    
    # Render the custom security logo sequence
    display_secure_banner()
    
    # Hide terminal input during Master Password query authentication
    master_password = getpass.getpass("Provide Vault Master Password: ")
    if not master_password:
        print("\033[1;31m[-] Error: Master Password parameters cannot evaluate to empty.\033[0m")
        sys.exit(1)

    # Perform structural cryptographic canary matching verification
    if not db.initialize_or_verify_master(master_password):
        print("\033[1;31m[-] CRITICAL ACCESS ALARM: Master Password signature validation failure.\033[0m")
        sys.exit(1)
        
    print("\033[1;32m[+] Cryptographic verification clear. Vault access unlocked.\033[0m")

    while True:
        print("\n" + "\033[1;34m-\033[0m" * 65)
        print("\033[1;36m[1]\033[0m Securely Encrypt and Store New Password")
        print("\033[1;36m[2]\033[0m Generate a Random High-Entropy Password")
        print("\033[1;36m[3]\033[0m Decrypt and Sync Password to Clipboard (Auto-Wipes)")
        print("\033[1;36m[4]\033[0m List Monitored Resources")
        print("\033[1;36m[5]\033[0m Terminate Secure Session")
        print("\033[1;34m-\033[0m" * 65)
        
        user_choice = input("\033[1;32mCommand >> \033[0m").strip()

        if user_choice == "1":
            resource = input("Enter unique resource target identifier (e.g. protonmail): ").strip()
            secret_string = getpass.getpass("Enter targeted password to hide: ")
            
            if not resource or not secret_string:
                print("\033[1;31m[-] Error: Fields cannot evaluate to null.\033[0m")
                continue
                
            salt, nonce, ciphertext = AdvancedCryptoEngine.encrypt_data(master_password, secret_string)
            db.store_credential_record(resource, salt, nonce, ciphertext)
            print(f"\033[1;32m[+] Credentials for '{resource}' safely committed into database storage.\033[0m")
            del secret_string  # Destroy plaintext memory instantiation

        elif user_choice == "2":
            try:
                length_input = input("Enter length requirements (Default 20): ").strip()
                selected_length = int(length_input) if length_input else 20
            except ValueError:
                selected_length = 20
            
            generated_secret = generate_high_entropy_password(selected_length)
            print(f"\n\033[1;33m[!] Secure Gen String: {generated_secret}\033[0m")
            print("[*] Notice: You can manually copy and save this asset using option [1].")
            del generated_secret

        elif user_choice == "3":
            resource = input("Enter resource target to retrieve: ").strip()
            cryptographic_record = db.fetch_credential_record(resource)
            
            if not cryptographic_record:
                print(f"\033[1;31m[-] Data query failure: No matches found for target '{resource}'.\033[0m")
                continue
                
            salt, nonce, ciphertext = cryptographic_record
            try:
                plaintext_decrypted = AdvancedCryptoEngine.decrypt_data(master_password, salt, nonce, ciphertext)
                synchronize_system_clipboard(plaintext_decrypted)
                
                # Sleep sequence mimicking hardware volatile timer protections
                print("\033[1;33m[*] Volatile timer activated. Clipboard will auto-wipe in 15 seconds...\033[0m")
                time.sleep(15)
                purge_system_clipboard()
                
                del plaintext_decrypted
            except ValueError as crypto_err:
                print(f"\033[1;31m[-] Execution Error: {crypto_err}\033[0m")

        elif user_choice == "4":
            all_assets = db.retrieve_all_resource_names()
            if not all_assets:
                print("\033[1;33m[*] Database registers zero elements.\033[0m")
            else:
                print("\n\033[1;34m--- Currently Protected Identifiers ---\033[0m")
                for index, item in enumerate(all_assets, 1):
                    print(f"  [\033[1;36m{index}\033[0m] -> {item}")

        elif user_choice == "5":
            print("\033[1;33m[*] De-allocating cryptographic session variables. Vault closing safely.\033[0m")
            del master_password
            break
        else:
            print("\033[1;31m[-] Error: Unrecognized interaction sequence.\033[0m")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Emergency exit clipboard flush sequence if user issues a Ctrl+C break signature
        purge_system_clipboard()
        print("\n\033[1;31m[-] Emergency abort signal intercepted. Session terminated safely.\033[0m")
        sys.exit(0)
