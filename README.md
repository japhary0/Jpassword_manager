```markdown
# 🛡️ Jpassword_manager | CLI Cryptographic Vault

A high-security, zero-knowledge local password management utility built in Python. Designed for Linux environments (Wayland & X11), it isolates credential assets inside an authenticated cryptographic store while enforcing strict volatile memory lifecycle controls.

---

## 🔥 Key Features

* **Authenticated Encryption:** All vault assets are secured using **AES-256-GCM**, providing both confidentiality and integrity verification against database tampering.
* **PBKDF2 Key Stretching:** Derived master keys use **600,000 iterations of PBKDF2-HMAC-SHA256** to heavily mitigate GPU-accelerated offline brute-force attempts.
* **Zero-Knowledge Auth:** Uses a database canary record to validate your master password without ever saving raw passwords or static hashes to disk.
* **Volatile Memory Defense:** Active variable de-allocation (`del` tracking) purges plaintexts from RAM immediately after use, backed by non-blocking daemon thread controls.
* **Auto-Flushing Clipboard Sync:** Temporarily pipes decrypted passwords to `wl-clipboard` or `xclip` and triggers an automated flush cycle after **15 seconds**.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Language** | Python 3.13 / 3.14+ |
| **Crypto Primitive Engine** | `python-cryptography` (OpenSSL Backend) |
| **Database** | Embedded SQLite3 (`encrypted_vault.db`) |
| **Clipboard Integration** | `wl-clipboard` (Wayland) / `xclip` (X11) |

---

## 💻 Quickstart & Multi-Distro Setup

### 1. Install System Clipboard Dependencies

`Jpassword_manager` utilizes `wl-clipboard` (Wayland) or `xclip` (X11) to sync decrypted credentials and execute volatile memory purges. Install the appropriate package for your distribution and display server:

#### 🦅 Arch Linux & Garuda Linux
```bash
# Wayland (Garuda / Arch default)
sudo pacman -S wl-clipboard

# X11 / Xorg
sudo pacman -S xclip

```

#### 🐉 Kali Linux, Debian & Ubuntu

```bash
# Update repository index
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

---

### 2. Installation & Execution

```bash
# Clone the repository
git clone [https://github.com/japhary0/Jpassword_manager.git](https://github.com/japhary0/Jpassword_manager.git)
cd Jpassword_manager

# Set up and activate isolated virtual environment
python3 -m venv venv
source venv/bin/activate

# Install cryptographic dependencies
pip install -r requirements.txt

# Launch the secure vault engine
python3 src/jvault.py

```

---

## 🔒 Security Lifecycle Overview

```
 [ Master Password Input ]
           │
           ▼
[ PBKDF2-HMAC-SHA256 (600,000 Iterations) ]
           │
           ▼
[ AES-256-GCM Symmetric Key ]
           │
           ├──► Validate Canary Block (Zero-Knowledge Check)
           │
           └──► Decrypt Secret ──► Clipboard Sync (15s Threaded Timer) ──► Clipboard & Memory Purge
