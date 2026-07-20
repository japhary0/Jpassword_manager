# Hardened Local Cryptographic Vault (CLI Password Manager)

A local-first, zero-knowledge password management system engineered with strict secure-coding standards and defensive memory management. This utility eliminates remote cloud exposure vectors entirely, keeping credential assets isolated inside a cryptographically hardened local environment.

## ⚙️ Core Security Architecture (07 Methodology)

This project implements a defense-in-depth model to protect sensitive data at rest, in transit across local systems, and inside volatile memory (RAM):

*   **Authenticated Encryption at Rest:** Utilizes **AES-256-GCM** to ensure absolute data confidentiality and cryptographic tamper-detection for all database records.
*   **Key Stretching Defenses:** Implements **PBKDF2-HMAC-SHA256 with 600,000 iterations** to derive robust master keys from user passwords, heavily mitigating the threat of offline hardware-accelerated brute-force attacks.
*   **Zero-Knowledge Master Authentication:** Employs an isolated database "Canary Block" encrypted with the derived master key. The system authenticates user identity by testing its ability to successfully decrypt this single canary record, ensuring raw passwords or static hashes are never stored on disk.
*   **Volatile Memory Lifecycle Isolation:** Enforces active garbage collection and explicit variable de-allocation (`del` tracking) on keys and text variables immediately after use. It intercepts OS signals (such as `Ctrl+C`) to cleanly purge memory spaces upon unexpected session terminations.
*   **Clipboard Exposure Mitigation:** Spawns decoupled Linux subprocesses via `wl-copy` (Wayland) or `xclip` (X11) to temporarily host decrypted credentials, tracking them with an asynchronous background loop that executes an absolute clipboard wipe after exactly 15 seconds.

## 🛠️ Technical Stack & Dependencies
*   **Language Runtime:** Python (Validated on interpreter v3.13 / v3.14 branches)
*   **Cryptographic Primitives Engine:** Native `python-cryptography` module (OpenSSL backend)
*   **Storage Framework:** Embedded `sqlite3` isolated relational pipeline
*   **Linux Clipboard Drivers:** `wl-clipboard` / `xclip` core binaries

---

## 📈 Timeline & Milestones (08 Timeline & Milestones)

The development lifecycle spanned a targeted 4-week implementation window:

*   **Week 1: Core Cryptographic Architecture & Design**
    *   *Action:* Built out the PBKDF2 key-stretching functions and the AES-256-GCM encryption/decryption pipeline.
    *   *Milestone 1:* Cryptographic backend engine fully validated with no memory leaks.
*   **Week 2: Database Layer & Canary Validation Mappings**
    *   *Action:* Constructed the relational database schema in SQLite and coded the secure zero-knowledge canary check.
    *   *Milestone 2:* Database layer initialization and secure authentication flow functional.
*   **Week 3: Display Subsystem Integration & Clipboard Timing Loops**
    *   *Action:* Implemented Linux subprocess pipelines for system clipboard interactions along with the 15-second tracking and wiping loop.
    *   *Milestone 3:* Successful automated copy-and-wipe test execution on Wayland/X11.
*   **Week 4: Integrity Testing, Code Optimization, & Portfolio Release**
    *   *Action:* Conducted database tampering simulation attacks, verified memory purging routines, and formatted documentation for version control tracking.
    *   *Milestone 4:* Project complete and repository published openly.

---

## 🚀 Getting Started

### Prerequisites
Install the required system clipboard handlers based on your current Linux desktop environment:
```bash
# For Wayland (Garuda, Fedora, etc.)
sudo pacman -S wl-clipboard

# For X11 Legacy Engine
sudo pacman -S xclip
# Jpassword_manager
# Jpassword_manager
# Jpassword_manager
