Markdown
# JVault Advanced — Universal Enterprise Cryptographic Engine

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Security Standard](https://img.shields.io/badge/NIST-SP%20800--63B-brightgreen.svg)](https://pages.nist.gov/800-63-3/sp800-63b.html)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows%20%7C%20BSD-orange.svg)]()

**JVault** is a zero-knowledge, local cryptographic vault and security suite engineered for high-assurance credential storage, password audit, and anti-forensic protection. Written natively in Python, JVault operates across Linux, macOS, Windows, and BSD environments without external cloud dependencies.

---

## 🔒 Key Security Architecture

* **AEAD Encryption Payload:** AES-256-GCM authenticated encryption with unique 96-bit Initialization Vectors (IV) generated per credential.
* **Hardened Key Derivation:** KDF via PBKDF2-HMAC-SHA256 set to **600,000 iterations**, mitigating GPU/ASIC brute-force vectors.
* **Zero-Knowledge Canary Check:** Local integrity canary prevents improper master password authentication or payload parsing without leaking secret state.
* **Process Memory Protection:**
  * **Linux:** `PR_SET_DUMPABLE` set to `0` via `libc.prctl` to prevent memory core dumps and process tracing.
  * **macOS:** Native `ptrace(PT_DENY_ATTACH)` execution via `libc.dylib` to block debuggers (`lldb`, `gdb`) from attaching to memory space.
  * **Windows:** Process Mitigation Policies enabled via `SetProcessMitigationPolicy` kernel calls.
* **OS Anti-Deletion Lock Engine:**
  * **Linux:** Applies immutable file flags (`chattr +i`).
  * **macOS / BSD:** Applies user immutable flags (`chflags uchg`).
  * **Windows:** Restricts delete/write permissions via NTFS Access Control Lists (`icacls /deny Users:(D,WO,WDAC)`).
* **Volatile Clipboard Manager:** Auto-purges secrets from RAM/clipboard after a 15-second delay utilizing OS-native mechanisms (`pbcopy`, `wl-copy`, `xclip`, `xsel`, PowerShell).
* **NIST SP 800-63B Password Engine:** Evaluates character entropy (bits), sequence repetition, positional patterns, and common dictionary blacklists.
* **Multi-Pass Cryptographic Shredder:** Overwrites database and script files with random entropy passes prior to unlinking, preventing magnetic or physical drive recovery.

---

## 🌐 Supported Operating Systems

| OS Family | Distribution / Version | Clipboard Backend | Deletion Lock Method |
| :--- | :--- | :--- | :--- |
| **Linux** | Arch, Ubuntu, Kali, Debian, Parrot OS, Fedora | `wl-copy` (Wayland) / `xclip` / `xsel` (X11) | `chattr +i` |
| **macOS** | macOS 10.15+ (Intel & Apple Silicon) | `pbcopy` | `chflags uchg` |
| **Windows** | Windows 10 / Windows 11 | PowerShell / `pyperclip` | `icacls` NTFS ACLs |
| **BSD** | FreeBSD, OpenBSD, NetBSD | `xclip` / `xsel` | `chflags uchg` |

---

## 🚀 Installation & Setup

### Requirements
* **Python 3.8+**
* `cryptography` Python package

### 1. Linux (Debian, Ubuntu, Kali, Parrot, Arch, Garuda)
```bash
# Package dependencies
# Debian/Ubuntu/Kali:
sudo apt update && sudo apt install -y python3 python3-pip python3-venv xclip wl-clipboard git

# Arch/Garuda:
sudo pacman -Syu --needed python python-pip xclip wl-clipboard git

# Repository Setup
git clone [https://github.com/japhary0/Jpassword_manager.git](https://github.com/japhary0/Jpassword_manager.git)
cd Jpassword_manager

python3 -m venv venv
source venv/bin/activate
pip install cryptography
chmod +x jvault.py
2. macOS (Darwin)
Bash
# Install Xcode Command Line Tools (if not present)
xcode-select --install

# Repository Setup
git clone [https://github.com/japhary0/Jpassword_manager.git](https://github.com/japhary0/Jpassword_manager.git)
cd Jpassword_manager

python3 -m venv venv
source venv/bin/activate
pip install cryptography
chmod +x jvault.py
3. Windows 10 / 11
Open PowerShell as Administrator:

PowerShell
# Clone Repository
git clone [https://github.com/japhary0/Jpassword_manager.git](https://github.com/japhary0/Jpassword_manager.git)
cd Jpassword_manager

# Set Up Virtual Environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Dependencies
pip install cryptography pyperclip
4. BSD (FreeBSD / OpenBSD)
Bash
# FreeBSD
sudo pkg install -y python3 git xclip

# OpenBSD
sudo pkg_add python3 git xclip

# Repository Setup
git clone [https://github.com/japhary0/Jpassword_manager.git](https://github.com/japhary0/Jpassword_manager.git)
cd Jpassword_manager

python3 -m venv venv
source venv/bin/activate
pip install cryptography
chmod +x jvault.py
💻 Quick Start & Usage
Execute the interactive CLI engine:

Bash
python3 jvault.py
Interactive Menu Overview:
=====================================================
   JVAULT: ENTERPRISE CRYPTO ENGINE (UNIVERSAL OS)   
=====================================================

--- MAIN MENU ---
[1] Store Credential
[2] Retrieve Credential (Copy to Clipboard)
[3] List All Stored Services
[4] Delete Credential
[5] Generate Strong Password (CSPRNG)
[6] Audit Password (NIST SP 800-63B Guidelines)
[7] Change Master Password
[8] ENABLE OS ANTI-DELETION LOCK (Requires Sudo/Admin)
[9] UNINSTALL & SECURELY SHRED TOOL / VAULT
[10] Safe Exit
🛠️ Security & Threat Model Considerations
Zero-Knowledge State: Master passwords are never written to disk or cached in persistent data structures. All memory references are explicitly scheduled for garbage collection (gc.collect()) upon authentication release.

Offline Local Cryptography: All operations occur purely in local memory and SQLite database files (encrypted_vault.db). No network requests are made.

Immutability Flags: Option 8 triggers OS kernel-level flags preventing rm -rf operations or non-privileged modification of the binary database.

🧑‍💻 Developer & Attribution
Developer: Japhary Said Japhary (Cybersecurity Specialist & IT Systems Architect)

Repository: https://github.com/japhary0/Jpassword_manager.git

License: MIT License
