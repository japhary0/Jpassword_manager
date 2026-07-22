Markdown
# 🛡️ Jpassword_manager | Advanced CLI Cryptographic Vault

A high-security, zero-knowledge local password management utility built in Python. Engineered specifically for Linux environments (Arch, Garuda, Kali, Debian, Fedora), **JVault** isolates credential assets inside an authenticated cryptographic store while enforcing OS-level memory protection and volatile memory lifecycle controls.

---

## 🔥 Key Features

* **Authenticated Encryption:** All vault assets are secured using **AES-256-GCM**, providing both confidentiality and integrity verification against offline payload tampering.
* **PBKDF2 Key Stretching:** Derived master keys use **600,000 iterations of PBKDF2-HMAC-SHA256** to heavily mitigate GPU-accelerated brute-force attempts.
* **Linux Process Memory Hardening:** Invokes `ctypes` bindings (`prctl / PR_SET_DUMPABLE`) to prevent memory dumps and local process tracing (`ptrace`).
* **Interactive Menu & Management:** Full-featured CLI loop allowing credential storage, service listing, selective deletion, interactive retrieval, and master key rotation.
* **Dynamic ANSI Color UI:** Distinct visual indicators for system headers, successful operations, warnings, and cryptographic failure states.
* **Zero-Knowledge Auth Canary:** Validates master password authenticity via an encrypted internal canary block without storing raw keys or static hashes on disk.
* **Volatile Memory Defense (`Safe Exit`):** Explicit variable de-allocation and forced garbage collection (`gc.collect()`) purge master keys from RAM upon exit or signal interrupt (`SIGINT`).
* **Auto-Flushing Clipboard Sync:** Asynchronously pipes decrypted secrets to `wl-clipboard` (Wayland) or `xclip` (X11) and executes an automated purge cycle after **15 seconds**.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Language** | Python 3.10+ / 3.14 |
| **Crypto Primitive Engine** | `python-cryptography` (OpenSSL Backend) |
| **Database Engine** | Embedded SQLite3 (`encrypted_vault.db`) |
| **OS Security Interfaces** | Linux C-bindings (`libc.so.6` via `ctypes`) |
| **Clipboard Systems** | `wl-clipboard` (Wayland) / `xclip` (X11) |

---

## 🔒 Security Architecture Lifecycle

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
          │   AES-256-GCM Key (Locked in RAM)     │
          └─────────────┬─────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌─────────────────────────┐   ┌───────────────────────────┐
│ Zero-Knowledge Canary   │   │  Encrypted SQLite Payload │
│ (Authenticity Verified) │   │ (AES-256-GCM + Nonce Tag) │
└─────────────────────────┘   └─────────────┬─────────────┘
│
▼
┌───────────────────────────┐
│  Async Clipboard Sync     │
│ (15s Memory Purge Timer)  │
└─────────────┬─────────────┘
│
▼
┌───────────────────────────┐
│ Safe Exit / SIGINT Cleanup│
│ (del key + gc.collect)│
└───────────────────────────┘


---

## 💻 Quickstart & Multi-Distro Setup

### 1. Install System Clipboard Dependencies

`Jpassword_manager` utilizes `wl-clipboard` (Wayland) or `xclip` (X11) to sync decrypted credentials and execute volatile memory purges. Install the appropriate package for your Linux distribution:

#### 🦅 Arch Linux & Garuda Linux
```bash
# Wayland (Garuda / Arch default)
sudo pacman -S wl-clipboard

# X11 / Xorg
sudo pacman -S xclip
🐉 Kali Linux, Debian & Ubuntu
Bash
# Update repository index
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
2. Installation & Execution
Bash
# Clone repository
git clone [https://github.com/japhary0/Jpassword_manager.git](https://github.com/japhary0/Jpassword_manager.git)
cd Jpassword_manager

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install cryptographic dependencies
pip install -r requirements.txt

# Run the vault engine
python3 src/jvault.py
