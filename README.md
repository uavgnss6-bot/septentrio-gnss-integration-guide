# Septentrio GNSS Receiver Integration Guide

> A practical, step-by-step guide for integrating Septentrio GNSS receivers with ArduPilot and PX4 flight controllers.

---

## Supported Receivers

| Model | Form Factor | Key Features | Best For |
|-------|------------|--------------|----------|
| **mosaic-X5** | 31x31x4 mm / 7g | 448 channels, L1/L2/L5, 100 Hz | UAVs, drones, robotics |
| **mosaic-G5 P3H** | 22.8x16.4 mm | Dual-antenna heading, pitch/roll | Survey, agri, precision nav |
| **AsteRx-m3 Pro+** | OEM or Box | Military AIM+ anti-jamming/spoofing | Defense, tactical UAVs |
| **mosaic-T** | Timing module | <1 ns accuracy, AIM+ protection | Infrastructure, swarms |

## Quick Start

1. Connect Septentrio COM2 to flight controller UART
2. Set baud rate to 115200 (both sides)
3. Configure flight controller parameters (see guides below)
4. Verify 3D Fix with >16 satellites

## Wiring

| Pixhawk Port | Septentrio RIB Board |
|-------------|---------------------|
| GPS1 RX | COM2 TX |
| GPS1 TX | COM2 RX |
| 5V | Power |
| GND | GND |

> **Important:** Always use COM2 on the RIB board for correct voltage levels.

## ArduPilot Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| GPS_TYPE | 9 | Septentrio |
| GPS_BAUD_RATE | 9 | 115200 baud |
| GPS_RATE_MS | 100 | 10 Hz update |

## PX4 Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| GPS_1_GNSS_ID | 1 | Septentrio |
| GPS_1_CONFIG | TELEM2 | Serial port |
| GPS_1_BAUD | 115200 | Baud rate |

## RTK NTRIP Configuration

1. Open Septentrio Web Interface
2. Go to Navigation -> RTK Settings
3. Enable NTRIP Client
4. Enter: Server, Port (2101), Mount Point, Username, Password

| Status | Meaning | Accuracy |
|--------|---------|----------|
| RTK Fixed | Full RTK solution | < 2.5 cm |
| RTK Float | Partial solution | ~20-40 cm |
| Single | No corrections | 1-3 m |

## Troubleshooting

| Symptom | Solution |
|---------|----------|
| No GPS fix | Swap TX/RX wires |
| Low satellites (<8) | Relocate antenna to clear sky view |
| RTK Float (not Fixed) | Reduce baseline distance (<30 km) |
| No heading data | Enable AttEulerCov in COM2 SBF output |
| Connection drops | Verify baud rate 115200 on both sides |

## SBF Parser

This repo includes `sbf-parser.py` to extract position data from Septentrio binary log files.

---

**[Browse GNSS Receivers](https://uav-gnss.com/product-category/gnss-receiver/)** | **[AIM+ Technology](https://uav-gnss.com/aim-resilient-gnss/)**

*Maintained by UAV GNSS — Septentrio-based GNSS receivers for professional UAV operations worldwide.*
