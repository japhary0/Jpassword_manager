Markdown
# 🛡️ Jpassword_manager | Advanced CLI Cryptographic Vault (Cross-Platform)

A high-security, zero-knowledge local password management utility built in Python. Engineered for full cross-platform compatibility across **Linux distributions** (Arch, Garuda, Kali, Debian, Ubuntu, Parrot OS) and **Windows 10/11**, JVault isolates credential assets inside an authenticated cryptographic store while enforcing OS-level process memory protection, anti-deletion locks, and volatile memory lifecycle controls.

---

## 🔥 Key Features

* **Complete Cross-Platform Compatibility**: Native operational support engineered for Linux environments (Arch, Garuda, Kali, Ubuntu, Debian, Parrot OS) as well as Windows 10 and 11 environments.
* **Authenticated Encryption**: All vault assets are secured using AES-256-GCM, providing both confidentiality and integrity verification against offline payload tampering.
* **PBKDF2 Key Stretching**: Derived master keys use 600,000 iterations of PBKDF2-HMAC-SHA256 to heavily mitigate GPU-accelerated brute-force attacks.
* **NIST SP 800-63B Compliance Engine (Options 5 & 6)**: Features a CSPRNG strong password generator and an interactive audit engine evaluating length thresholds, dictionary blacklists, repetitive character sequences, and adjusted entropy calculations aligned with NIST SP 800-63B security standards.
* **Automated OS Anti-Deletion Locking (Option 8)**: Prevents unauthorized users or attackers with local access from deleting or tampering with the tool or database. Enforces elevated permission requirements via Linux `chattr +i` (Immutable attribute) or Windows NTFS ACL Deny rules (`icacls`) to restrict file removal without Administrator/Sudo elevation.
* **Master-Authenticated Cryptographic Shredding (Option 9)**: Requires Master Password authentication to unlock system flags and execute a multi-pass secure random byte overwrite (shredding) of both the database and script files for complete self-destruction.
* **Cross-Platform Volatile Clipboard Engine**: Asynchronously pipes decrypted secrets to `wl-clipboard` (Wayland), `xclip` (X11), or Windows CMD/PowerShell native clipboard APIs, executing an automated zero-out purge cycle after 15 seconds.
* **Process Memory Hardening**: Invokes native platform bindings (`prctl / PR_SET_DUMPABLE` on Linux, `SetProcessMitigationPolicy` on Windows) to prevent memory dumps and local process tracing (`ptrace`).
* **Zero-Knowledge Auth Canary**: Validates master password authenticity via an encrypted internal canary block without storing raw keys or static hashes on disk.
* **Dynamic ANSI Color UI**: Cross-platform VT100-enabled terminal interface with distinct visual indicators for headers, successful operations, warnings, and cryptographic failures.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Language** | Python 3.10+ / Python 3.14 |
| **Crypto Engine** | `python-cryptography` (OpenSSL Backend) |
| **Database Engine** | Embedded SQLite3 (`encrypted_vault.db`) |
| **OS Security Interfaces** | Linux C-bindings (`libc.so.6` via `ctypes`) / Windows API (`kernel32`) |
| **OS Access Control** | Linux `chattr` (Ext4/Btrfs) / Windows NTFS `icacls` |
| **Clipboard Systems** | `wl-clipboard` (Wayland), `xclip` (X11), Windows CMD / PowerShell Native API / `pyperclip` |

---

## 🔒 Security Architecture Lifecycle

```text
             ┌───────────────────────────┐
             │   Master Password Input   │
             └─────────────┬─────────────┘
                           │
                           ▼
             ┌───────────────────────────┐
             │ PBKDF2-HMAC-SHA256 (600k) │
             └─────────────┬─────────────┘
                           │
                           ▼
             ┌───────────────────────────┐
             │ AES-256-GCM Key (in RAM)  │
             └─────────────┬─────────────┘
                           │
    ┌──────────────────────┴──────────────────────┐
    │                                             │
    ▼                                             ▼
┌─────────────────────────┐           ┌───────────────────────────┐
│ Zero-Knowledge Canary   │           │ Encrypted SQLite Payload  │
│ (Authenticity Verified) │           │ (AES-256-GCM + Nonce Tag) │
└─────────────────────────┘           └─────────────┬─────────────┘
                                                    │
                                                    ▼
                                      ┌───────────────────────────┐
                                      │ Cross-Platform Volatile   │
                                      │ Clipboard Sync (15s Purge)│
                                      │ (Wayland / X11 / Win CMD) │
                                      └─────────────┬─────────────┘
                                                    │
                                                    ▼
                                      ┌───────────────────────────┐
                                      │ Safe Exit / SIGINT        │
                                      │ (del key + gc.collect)    │
                                      └───────────────────────────┘
💻 Quickstart & Setup
1. Install System Clipboard Dependencies
🦅 Arch Linux & Garuda Linux
Bash
# Wayland (Garuda / Arch default)
sudo pacman -S wl-clipboard

# X11 / Xorg
sudo pacman -S xclip
🐉 Kali Linux, Debian, Parrot OS & Ubuntu
Bash
sudo apt update

# Wayland
sudo apt install wl-clipboard

# X11 / Xorg (Kali / Debian default)
sudo apt install xclip
🎩 Fedora Linux
Bash
# Wayland (Fedora default)
sudo dnf install wl-clipboard

# X11 / Xorg
sudo dnf install xclip
🪟 Windows 10/11
No external system packages are required. Clipboard management uses native Windows CMD/PowerShell integration or pyperclip:

PowerShell
pip install pyperclip
2. Installation & Execution
Bash
# Clone repository
git clone [https://github.com/japhary0/Jpassword_manager.git](https://github.com/japhary0/Jpassword_manager.git)
cd Jpassword_manager

# Create and activate virtual environment
# Linux/macOS:
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install cryptographic dependencies
pip install cryptography

# Run the vault engine
python3 jvault.py
⚙️ Operating Instructions
Upon execution, jvault.py provides an interactive command menu:

Store Credential: Encrypts and saves secrets associated with a service name.

Retrieve Credential: Decrypts secret and copies it to clipboard with a 15-second auto-purge timer across Linux (Wayland/X11) and Windows (CMD/PowerShell).

List All Stored Services: Displays index of stored services and creation timestamps.

Delete Credential: Removes selected target credential from the database.

Generate Strong Password: Creates a CSPRNG password compliant with NIST SP 800-63B standards.

Audit Password: Analyzes input passwords against NIST SP 800-63B guidelines (length thresholds, entropy calculations, dictionary checks).

Change Master Password: Re-encrypts all database records under a new master key derivation.

Enable OS Anti-Deletion Lock: Sets file immutability flags via Linux chattr +i or Windows NTFS ACL Deny rules to prevent unauthorized removal.

Uninstall & Shred Tool: Authenticates Master Password and executes a multi-pass cryptographic wipe (shredding) of all script and database files.

Safe Exit: Wipes volatile keys from RAM memory and exits cleanly.

📄 License
Distributed under the MIT License. See LICENSE for more information.
