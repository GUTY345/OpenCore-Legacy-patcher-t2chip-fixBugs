<div align="center">
  <img src="https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/main/docs/images/OC-Patcher.png" alt="OpenCore Legacy Patcher Logo" width="180" />

  # OpenCore Legacy Patcher — T2 Mac Edition

  **Supports Macs with Apple T2 Security Chip · macOS Tahoe / Sequoia**

  [![Latest Release](https://img.shields.io/github/v/release/GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs?label=Latest%20Release&color=blue)](https://github.com/GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs/releases/latest)
  [![Build Status](https://img.shields.io/github/actions/workflow/status/GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs/build-app-wxpython.yml?label=Build)](https://github.com/GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs/actions)
  [![License](https://img.shields.io/github/license/GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs)](LICENSE.txt)
  [![Platform](https://img.shields.io/badge/Platform-macOS%20Tahoe%20%7C%20Sequoia-purple)](https://github.com/GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs)

</div>

---

## Overview

This is a community-maintained fork of [OpenCore Legacy Patcher](https://github.com/dortania/OpenCore-Legacy-Patcher) focused exclusively on **Apple T2 Security Chip Macs**. It resolves boot failures, kernel panics, and display issues specific to T2 hardware running macOS Tahoe (macOS 26) and Sequoia.

> **Based on:** albert-mueller/OpenCore-Legacy-Patcher-T2 · Dortania/OpenCore-Legacy-Patcher

---

## Supported Models

### MacBook Pro
| Model | Marketing Name | GPU |
|---|---|---|
| MacBookPro15,1 | MacBook Pro 15-inch 2018 | Intel UHD 630 + AMD Radeon Pro |
| MacBookPro15,2 | MacBook Pro 13-inch 2018 (4 TB3) | Intel Iris Plus 655 |
| MacBookPro15,3 | MacBook Pro 15-inch 2019 | Intel UHD 630 + AMD Radeon Pro |
| MacBookPro15,4 | MacBook Pro 13-inch 2019 (2 TB3) | Intel Iris Plus 655 |
| MacBookPro16,1 | MacBook Pro 16-inch 2019 | Intel UHD 630 + AMD Radeon Pro |
| MacBookPro16,2 | MacBook Pro 13-inch 2020 (4 TB3) | Intel UHD 617 |
| MacBookPro16,3 | MacBook Pro 13-inch 2020 (2 TB3) | Intel UHD 617 |
| MacBookPro16,4 | MacBook Pro 16-inch 2019 CTO | Intel UHD 630 + AMD Radeon Pro |

### MacBook Air
| Model | Marketing Name | GPU |
|---|---|---|
| MacBookAir8,1 | MacBook Air 2018 | Intel UHD 617 ✨ |
| MacBookAir8,2 | MacBook Air 2019 | Intel UHD 617 ✨ |
| MacBookAir9,1 | MacBook Air 2020 (Intel) | Intel UHD 617 ✨ |

### Other T2 Macs
| Model | Marketing Name |
|---|---|
| Macmini8,1 | Mac mini 2018 |
| MacPro7,1 | Mac Pro 2019 |
| iMac19,1 | iMac 27-inch 2019 |
| iMac19,2 | iMac 21.5-inch 2019 |
| iMac20,1 | iMac 27-inch 2020 |
| iMac20,2 | iMac 27-inch 2020 CTO |

> ✨ = Newly added full support in v1.0.7.1

---

## What's Fixed

### 🔴 Critical Boot Fixes

**`com.apple.kec.corecrypto` Kernel Panic (macOS Tahoe)**
- Removed `-liluforce` / `-lilubetaall` from T2 Mac boot-args — Lilu injection into `corecrypto` breaks the FIPS POST self-test causing a panic at `_corecrypto_kext_start`
- Added kernel patch to bypass FIPS POST check in `com.apple.kec.corecrypto` (MinKernel 25.0.0)
- T2 Macs now use AMFIPass + `-amfipassbeta` exclusively instead of `amfi=0x80`

**Booter & Security Settings**
- `SecureBootModel` forced to `Disabled` for all T2 Macs
- `ApECID = 0` and `DmgLoading = Any` applied
- `UpdateSMBIOSMode = Custom` for correct T2 SMBIOS handling

### 🟡 Graphics Fixes

**Intel UHD 617 — MacBook Air 2018/2019 (NEW in v1.0.7.1)**
- Correct connector-less `ig-platform-id 0x3EA50009` (Amber Lake GT3e) injected
- Previously these models received wrong UHD 630 IDs (`0x3E9B0006`) causing grey screen at boot
- Added `igfxgl=1` + `igfxmetal=1` boot-args to fix grey screen on Tahoe
- `igfxnoredir=1` now scoped to UHD 630 models only

**Intel UHD 630 — MacBook Pro 15/16-inch**
- Connector-less `ig-platform-id 0x3E9B0006` to prevent APFS race condition on Tahoe
- `igfxonln=1` to force iGPU online and prevent UI stall
- `igfxnoredir=1` to fix white/frozen screen on MacBookPro15,1
- `forceRenderStandby=0` to prevent GPU power saving hang

### 🟢 Stability Fixes

| Fix | Description |
|---|---|
| AppleSEPManager patch | Converts SEP timeout panic to return — prevents unexpected reboots |
| USB handshake bypass | Bypasses T2 USB handshake to prevent boot stall |
| USB timeout increase | `AppleIntelUSBXHCI` timeout `0x0A → 0xFF` (255ms) for instant HID response |
| InternalHubPowerCheck bypass | Prevents USB hub power state hang |
| TouchBar driver patch | Fixes Touch Bar stall/hang on Tahoe |
| NVMe fix | `nvme_shutdown_timestamp=0` resolves APFS mount stall |
| ipc_control_port_options | Critical T2 communication stall fix |
| corecrypto FIPS bypass | Kernel patch allowing boot via OpenCore unsigned path |

### 🔵 Build & Code Quality

- Fixed duplicate kernel patch injection (AppleSEPManager was injected twice)
- Removed dead `run_sequence()` subprocess code in `misc.py`
- Added deduplication guards for WhateverGreen / CryptexFixup / AMFIPass
- Security chip detection (T2 / T1 / None) displayed in main menu

---

## Installation

### Option 1 — Install via PKG (Recommended)

1. Download `OpenCore-Patcher.pkg` from the [latest release](https://github.com/GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs/releases/latest)
2. Run the installer
3. Open **OpenCore Legacy Patcher** from Applications
4. Click **Build and Install OpenCore**
5. Select your target drive and install

### Option 2 — Run from Source

```bash
# Requirements: Python 3.10+, Git
git clone https://github.com/GUTY345/OpenCore-Legacy-patcher-t2chip-fixBugs.git
cd OpenCore-Legacy-patcher-t2chip-fixBugs
pip3 install -r requirements.txt

# Launch GUI
python3 OpenCore-Patcher-GUI.command
```

---

## Post-Installation (macOS Tahoe)

After installing OpenCore and booting into macOS Tahoe, run **Post-Install Root Patch** from the app to install GPU drivers and system patches.

If you encounter issues, run these commands in Recovery Mode Terminal:

```bash
csrutil disable
csrutil authenticated-root disable
```

---

## Boot Arguments Applied (T2 Macs)

| Argument | Purpose |
|---|---|
| `-amfipassbeta` | Enable AMFIPass compatibility mode |
| `-ibtcompatbeta` | Bluetooth compatibility |
| `ipc_control_port_options=0` | T2 communication stall fix |
| `igfxonln=1` | Force iGPU online |
| `igfxfw=2` | Force Apple Graphics Firmware |
| `agdpmod=vit9696` | Disable board ID checks |
| `nvme_shutdown_timestamp=0` | APFS mount fix |
| `cryptex=0` | Tahoe cryptex bypass |
| `cs_allow_invalid=1` | Allow unsigned code (Tahoe) |
| `forceRenderStandby=0` | Prevent GPU power saving hang |
| `usbmuxd=0x3` | USB multiplexer fix |
| `keepsyms=1` | Preserve kernel symbols for debugging |

---

## Kernel Patches Applied (T2 Macs, Tahoe)

| Patch | Target | Purpose |
|---|---|---|
| Bypass corecrypto FIPS POST | `com.apple.kec.corecrypto` | Allow boot via OpenCore unsigned path |
| Bypass T2 USB handshake | `AppleUSBXHCI` | Prevent USB freeze at early boot |
| Increase USB timeout | `AppleUSBXHCI` | 10ms → 255ms for HID response |
| Bypass InternalHubPowerCheck | `AppleUSBXHCI` | Prevent USB hub power state hang |
| SEP Manager panic → return | `AppleSEPManager` | Prevent SEPOS kernel panic |
| TouchBar driver fix | `AppleTouchBarHIDEventDriver` | Fix Touch Bar stall on Tahoe |
| Disable Library Validation | `kernel` | Allow unsigned kexts |

---

## Disclaimer

> This is an experimental community fork. Use at your own risk. Always back up your data before patching. This project is not affiliated with Apple Inc.

---

## Credits

- **[Dortania](https://github.com/dortania)** — Original OpenCore Legacy Patcher
- **[albert-mueller](https://github.com/albert-mueller)** — T2 Mac branch foundation
- **[Acidanthera](https://github.com/acidanthera)** — OpenCore, Lilu, WhateverGreen, AMFIPass
- **Mathachai (GUTY345)** — T2 Tahoe fixes, UHD 617 support, maintenance
