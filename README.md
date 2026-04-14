# Nordic Semiconductor KiCad Library

[![GitHub stars](https://img.shields.io/github/stars/hlord2000/nordic-lib-kicad)](https://github.com/hlord2000/nordic-lib-kicad/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/hlord2000/nordic-lib-kicad)](https://github.com/hlord2000/nordic-lib-kicad/network)
[![GitHub issues](https://img.shields.io/github/issues/hlord2000/nordic-lib-kicad)](https://github.com/hlord2000/nordic-lib-kicad/issues)
---
# A KiCad 9 library for all modern Nordic Semiconductor parts.
<p align="center">
  <img src="img/img.png" alt="centered image" />
</p>

KLC compliance is established using KiCad's official scripts within the "kicad-library-utils" folder and the "lib_check.sh" script

Compliance for the purposes of this library is defined as zero errors for footprints and symbols. Reasonable warnings about pin position or names may be accepted.

Current generated-footprint status:
- Repo-local Nordic footprints and STEP models are generated from spec through the `kicad-footprint-generator` submodule.
- The current footprint KLC sweep covers 29 generated footprints.
- 26 pass cleanly; 3 still emit warnings:
  - `QFN-52-1EP_6x6mm_P0.4mm_EP4.7x4.7mm_ThermalVias` (`F6.3`, same thermal-via checker issue seen on KiCad's official QFN thermal-via footprints)
  - `LGA_9160_16.0x10.5mm` (`F9.2`, non-default `solder_paste_ratio`)
  - `LGA_9161_16.0x10.5mm` (`F9.2`, non-default `solder_paste_ratio`)

## Installation instructions

Open the KiCad Plugin and Content Manager (PCM), click "Manage..." in the top right, and add the following URL to your list of repositories:
```
https://raw.githubusercontent.com/hlord2000/hlord2000-kicad-repository/main/repository.json
```
Then, using the dropdown in the PCM, switch to "hlord2000's KiCad Repository" and click on the "Libraries" tab.

## Seeking pull-requests for any footprint/symbol/reference design block/3D model marked 🚧

 # nRF9 series - Cellular

|             | Symbol | Footprint | Reference Design Block | 3D Model | KLC Compliant |
|-------------|--------|-----------|------------------------|----------|---------------|
| [nRF9151](https://www.nordicsemi.com/products/nrf9151) LGA |✅|✅|🚧|✅|🚧|
| [nRF9161](https://www.nordicsemi.com/products/nrf9161) LGA |✅|✅|🚧|✅|🚧|
| [nRF9160](https://www.nordicsemi.com/products/nrf9160) LGA |✅|✅|🚧|✅|🚧|

 # nRF7 series - Wi-Fi

|             | Symbol | Footprint | Reference Design Block | 3D Model | KLC Compliant |
|-------------|--------|-----------|------------------------|----------|---------------|
| [nRF7002](https://www.nordicsemi.com/products/nrf7002) QFN |✅|✅|🚧|✅|🚧| 
| [nRF7002](https://www.nordicsemi.com/products/nrf7002) WLCSP |✅|✅|🚧|✅|🚧| 
| [nRF7001](https://www.nordicsemi.com/products/nrf7001) QFN |✅|✅|🚧|✅|🚧| 
| [nRF7000](https://www.nordicsemi.com/products/nrf7000) QFN |✅|✅|🚧|✅|🚧| 

# nRF54L series - Bluetooth Low Energy

|             | Symbol | Footprint | Reference Design Block | 3D Model | KLC Compliant |
|-------------|--------|-----------|------------------------|----------|---------------|
| [nRF54LM20A](https://www.nordicsemi.com/Products/nRF54LM20A) QFN-52 |✅|✅|✅|✅|🚧| 
| [nRF54LM20A](https://www.nordicsemi.com/Products/nRF54LM20A) FCCSP |✅|✅|✅|✅|🚧| 
| [nRF54L15](https://www.nordicsemi.com/products/nrf54l15) QFN-52 |✅|✅|✅|✅|🚧| 
| [nRF54L15](https://www.nordicsemi.com/products/nrf54l15) QFN-48 |✅|✅|✅|✅|🚧| 
| [nRF54L15](https://www.nordicsemi.com/products/nrf54l15) QFN-40 |✅|✅|✅|✅|🚧| 
| [nRF54L15](https://www.nordicsemi.com/products/nrf54l15) WLCSP |✅|✅|✅|✅|🚧| 
| [nRF54L10](https://www.nordicsemi.com/products/nrf54l10) QFN-52 |✅|✅|✅|✅|🚧| 
| [nRF54L10](https://www.nordicsemi.com/products/nrf54l10) QFN-48 |✅|✅|✅|✅|🚧| 
| [nRF54L10](https://www.nordicsemi.com/products/nrf54l10) QFN-40 |✅|✅|✅|✅|🚧| 
| [nRF54LV10A](https://www.nordicsemi.com/products/nrf54lv10) CSP-29 |✅|✅|🚧|✅|🚧| 
| [nRF54LV10A](https://www.nordicsemi.com/products/nrf54lv10) QFN-48 |✅|✅|🚧|✅|🚧| 
| [nRF54L05](https://www.nordicsemi.com/products/nrf54l05) QFN-52 |✅|✅|✅|✅|🚧| 
| [nRF54L05](https://www.nordicsemi.com/products/nrf54l05) QFN-48 |✅|✅|✅|✅|🚧| 
| [nRF54L05](https://www.nordicsemi.com/products/nrf54l05) QFN-40 |✅|✅|✅|✅|🚧| 

 # nRF53 series - Bluetooth Low Energy

|             | Symbol | Footprint | Reference Design Block | 3D Model | KLC Compliant |
|-------------|--------|-----------|------------------------|----------|---------------|
| [nRF5340](https://www.nordicsemi.com/products/nrf5340) aQFN |✅|✅|🚧|🚧|🚧| 
| [nRF5340](https://www.nordicsemi.com/products/nrf5340) WLCSP |✅|✅|🚧|🚧|🚧| 

 # nRF52 series - Bluetooth Low Energy

|             | Symbol | Footprint | Reference Design Block | 3D Model | KLC Compliant |
|-------------|--------|-----------|------------------------|----------|---------------|
| [nRF52840](https://www.nordicsemi.com/products/nrf52840) aQFN |✅|✅|🚧|✅|🚧| 
| [nRF52840](https://www.nordicsemi.com/products/nrf52840) WLCSP |✅|✅|🚧|🚧|🚧| 
| [nRF52840](https://www.nordicsemi.com/products/nrf52840) QFN |✅|✅|🚧|✅|🚧| 
| [nRF52833](https://www.nordicsemi.com/products/nrf52833) aQFN |✅|✅|🚧|🚧|🚧| 
| [nRF52833](https://www.nordicsemi.com/products/nrf52833) WLCSP |✅|✅|🚧|🚧|🚧| 
| [nRF52833](https://www.nordicsemi.com/products/nrf52833) QFN |✅|✅|🚧|✅|🚧| 
| [nRF52832](https://www.nordicsemi.com/products/nrf52832) WLCSP |✅|✅|🚧|🚧|🚧| 
| [nRF52832](https://www.nordicsemi.com/products/nrf52832) QFN |✅|✅|🚧|✅|🚧| 
| [nRF52820](https://www.nordicsemi.com/products/nrf52820) WLCSP |✅|✅|🚧|🚧|🚧| 
| [nRF52820](https://www.nordicsemi.com/products/nrf52820) QFN |✅|✅|🚧|✅|🚧| 
| [nRF52811](https://www.nordicsemi.com/products/nrf52811) WLCSP |✅|✅|🚧|✅|🚧| 
| [nRF52811](https://www.nordicsemi.com/products/nrf52811) QFN-32 |✅|✅|🚧|✅|🚧| 
| [nRF52811](https://www.nordicsemi.com/products/nrf52811) QFN-48 |✅|✅|🚧|✅|🚧| 
| [nRF52810](https://www.nordicsemi.com/products/nrf52810) WLCSP |✅|✅|🚧|✅|🚧| 
| [nRF52810](https://www.nordicsemi.com/products/nrf52810) QFN-32 |✅|✅|🚧|✅|🚧| 
| [nRF52810](https://www.nordicsemi.com/products/nrf52810) QFN-48 |✅|✅|🚧|✅|🚧| 
| [nRF52805](https://www.nordicsemi.com/products/nrf52805) WLCSP |✅|✅|🚧|✅|🚧| 

 # nRF52 series - Modules

|             | Symbol | Footprint | Reference Design Block | 3D Model | KLC Compliant |
|-------------|--------|-----------|------------------------|----------|---------------|
| [E73-2G4M08S1C](https://www.ebyte.com/product-view-news.html?id=787) LGA module |✅|✅|🚧|✅|🚧|
| [ISP1907-LL](https://www.insightsip.com/products/bluetooth-low-energy/isp1907) LGA module |✅|✅|🚧|✅|🚧|

 # nRF21 series - PA + LNA ICs

|             | Symbol | Footprint | Reference Design Block | 3D Model | KLC Compliant |
|-------------|--------|-----------|------------------------|----------|---------------|
| [nRF21540](https://www.nordicsemi.com/products/nrf21540) QFN |✅|✅|🚧|✅|✅| 

 # nRF53 series - Modules

|             | Symbol | Footprint | Reference Design Block | 3D Model | KLC Compliant |
|-------------|--------|-----------|------------------------|----------|---------------|
| [E83-2G4M03S](https://www.ebyte.com/product-view-news.html?id=1307) LGA module |✅|✅|🚧|✅|🚧|
| [ISP2053-AX](https://www.insightsip.com/products/bluetooth-low-energy-and-802-15-4/isp2053) LGA module |✅|✅|🚧|✅|🚧|

 # nRF54 series - Modules

|             | Symbol | Footprint | Reference Design Block | 3D Model | KLC Compliant |
|-------------|--------|-----------|------------------------|----------|---------------|
| BC15C LGA module |✅|✅|🚧|✅|🚧|
| BC15M LGA module |✅|✅|🚧|✅|🚧|
| BL54L15-453-000xxx LGA module |✅|✅|🚧|✅|🚧|
| BL54L10-453-000xxx LGA module |✅|✅|🚧|✅|🚧|
| BM15x LGA module |✅|✅|🚧|✅|🚧|
| BM20x LGA module |✅|✅|🚧|✅|🚧|

 # nPM Power Management ICs

|             | Symbol | Footprint | Reference Design Block | 3D Model | KLC Compliant |
|-------------|--------|-----------|------------------------|----------|---------------|
| [nPM6001](https://www.nordicsemi.com/products/nPM6001) WLCSP |✅|✅|🚧|🚧|✅| 
| [nPM2100](https://www.nordicsemi.com/products/nPM2100) WLCSP |✅|✅|🚧|✅|✅| 
| [nPM2100](https://www.nordicsemi.com/products/nPM2100) QFN |✅|✅|🚧|✅|✅| 
| [nPM1300](https://www.nordicsemi.com/products/nPM1300) WLCSP |✅|✅|🚧|🚧|✅| 
| [nPM1300](https://www.nordicsemi.com/products/nPM1300) QFN |✅|✅|🚧|✅|✅| 
| [nPM1100](https://www.nordicsemi.com/products/nPM1100) WLCSP |✅|✅|🚧|🚧|✅| 
| [nPM1100](https://www.nordicsemi.com/products/nPM1100) QFN |✅|✅|🚧|✅|✅| 
