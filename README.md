1. **Cross-Platform Support**: Updated to reflect complete compatibility with both **Linux** (Arch, Garuda, Kali, Ubuntu, Debian, Parrot OS) and **Windows 10/11**.
2. **NIST SP 800-63B Compliance Engine**: Added documentation for options 5 & 6 (CSPRNG strong password generation and standard-aligned security auditing).
3. **Automated OS Anti-Deletion Locking**: Included details on option 8 (`chattr +i` on Linux & NTFS ACL Deny rules on Windows) to prevent unauthorized file removal without system Administrator/Sudo elevation.
4. **Master-Authenticated Cryptographic Shredding**: Added details on option 9 (multi-pass secure file shredding for complete self-destruction).
5. **Cross-Platform Volatile Clipboard Engine**: Documented auto-flushing support for Windows CMD/PowerShell alongside Linux Wayland and X11.

---

```markdown
# 🛡️ Jpassword_manager | Advanced CLI Cryptographic Vault (Cross-Platform)

A high-security, zero-knowledge local password management utility built in Python. Engineered for **Linux environments** (Arch, Garuda, Kali, Debian, Ubuntu, Parrot OS) and **Windows 10/11**, JVault isolates credential assets inside an authenticated cryptographic store while enforcing OS-level process memory protection, anti-deletion locks, and volatile memory lifecycle controls.

---

## 🔥 Key Features

* **Authenticated Encryption**: All vault assets are secured using AES-256-GCM, providing both confidentiality and integrity verification against offline payload tampering.
* **PBKDF2 Key Stretching**: Derived master keys use 600,000 iterations of PBKDF2-HMAC-SHA256 to heavily mitigate GPU-accelerated brute-force attacks.
* **OS-Level Anti-Deletion Locking (Option 8)**: Prevents unauthorized users or attackers with local access from deleting or tampering with the tool/database. Enforces system-level password prompts via Linux `chattr +i` (Immutable attribute) or Windows NTFS ACL Deny rules (`icacls`).
* **Authenticated Cryptographic Self-Destruct (Option 9)**: Requires Master Password authentication to unlock system flags and execute a multi-pass random byte overwrite (shredding) of both the database and script files.
* **NIST SP 800-63B Password Engine (Options 5 & 6)**: Features a CSPRNG password generator and an interactive audit engine evaluating length thresholds, dictionary blacklists, repetitive character sequences, and adjusted entropy calculations.
* **Process Memory Hardening**: Invokes native platform bindings (`prctl / PR_SET_DUMPABLE` on Linux, `SetProcessMitigationPolicy` on Windows) to prevent memory dumps and local process tracing (`ptrace`).
* **Zero-Knowledge Auth Canary**: Validates master password authenticity via an encrypted internal canary block without storing raw keys or static hashes on disk.
* **Cross-Platform Volatile Clipboard Engine**: Asynchronously pipes decrypted secrets to `wl-clipboard` (Wayland), `xclip` (X11), or the native Windows Clipboard API, executing an automated zero-out purge cycle after 15 seconds.
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
| **Clipboard Systems** | `wl-clipboard` (Wayland), `xclip` (X11), Windows Native API / `pyperclip` |

---

## 🔒 Security Architecture Lifecycle

```text
             ┌───────────────────────────┐
             │   Master Password Input   │
             └─────────────┬─────────────┘
                           │
                           ▼
      ┌───────────────────────────────────────────┐
      │   PBKDF2-HMAC-SHA256 (600k Iterations)    │
      └─────────────┬─────────────────────────────┘
                           │
                           ▼
      ┌───────────────────────────────────────────┐
      │   AES-256-GCM Key (Locked in RAM)         │
      └─────────────┬─────────────────────────────┘
                    │
    ┌───────────────┴───────────────┐
    │                               │
    ▼                               ▼
┌─────────────────────────┐   ┌───────────────────────────┐
│ Zero-Knowledge Canary   │   │ Encrypted SQLite Payload  │
│ (Authenticity Verified) │   │ (AES-256-GCM + Nonce Tag) │
└─────────────────────────┘   └─────────────┬─────────────┘
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │ Cross-Platform Volatile   │
                              │ Clipboard Sync (15s Purge)│
                              └─────────────┬─────────────┘
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │ Safe Exit / SIGINT        │
                              │ (del key + gc.collect)    │
                              └───────────────────────────┘

```

---

## 💻 Quickstart & Setup

### 1. Install System Clipboard Dependencies

#### 🦅 Arch Linux & Garuda Linux

```bash
# Wayland (Garuda / Arch default)
sudo pacman -S wl-clipboard

# X11 / Xorg
sudo pacman -S xclip

```

#### 🐉 Kali Linux, Debian, Parrot OS & Ubuntu

```bash
sudo apt update

# Wayland
sudo apt install wl-clipboard

# X11 / Xorg (Kali / Debian default)
sudo apt install xclip

```

#### 🎩 Fedora Linux

```bash
# Wayland (Fedora default)
sudo dnf install wl-clipboard

# X11 / Xorg
sudo dnf install xclip

```

#### 🪟 Windows 10/11

No external system packages required. Clipboard support utilizes native PowerShell execution or optional `pyperclip`:

```powershell
pip install pyperclip

```

---

### 2. Installation & Execution

```bash
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

```

---

## ⚙️ Operating Instructions

Upon execution, `jvault.py` provides an interactive command menu:

1. **Store Credential**: Encrypts and saves secrets associated with a service name.
2. **Retrieve Credential**: Decrypts secret and copies it to clipboard with a 15-second auto-purge timer.
3. **List All Stored Services**: Displays index of stored services and creation timestamps.
4. **Delete Credential**: Removes selected target credential from the database.
5. **Generate Strong Password**: Creates a CSPRNG password compliant with high-entropy standards.
6. **Audit Password**: Analyzes any input password against NIST SP 800-63B guidelines.
7. **Change Master Password**: Re-encrypts all database records under a new master key derivation.
8. **Enable OS Anti-Deletion Lock**: Prompts for system administrator privileges to set file immutability flags.
9. **Uninstall & Shred Tool**: Authenticates Master Password and executes a multi-pass secure wipe of all files.
10. **Safe Exit**: Wipes volatile keys from memory and exits cleanly.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information
