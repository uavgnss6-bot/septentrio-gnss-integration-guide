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

### Wiring diagram (ASCII)

Typical connection between a Septentrio receiver (RIB board COM2) and a Pixhawk / ArduPilot flight controller:

```
Septentrio RIB                     Pixhawk / Flight Controller
-------------                     ----------------------------
COM2 TX  ---------------------->   GPS1 RX  (TELEM2 RX)
COM2 RX  <---------------------   GPS1 TX  (TELEM2 TX)
5V (VCC) ---------------------->   5V
GND      ---------------------->   GND
```

- Use COM2 on the RIB board — it outputs 3.3 V logic that is safe for the flight controller UART.
- The port may be labeled `GPS1` on some FCs and `TELEM2` on others — it is the same UART; just match the baud rate on both ends.
- **Do not power the receiver from the FC's servo rail.** Use the dedicated 5V UART pin or a separate regulator; the receiver draws more during RTK fixes.
- If you see no fix after wiring, swap TX and RX first — it is the most common wiring mistake.

## ArduPilot Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| GPS_TYPE | 9 | Septentrio |
| GPS_BAUD_RATE | 9 | 115200 baud |
| GPS_RATE_MS | 100 | 10 Hz update |
| GPS_AUTO_CONFIG | 1 | Auto-configure receiver on boot |
| GPS_GNSS_MODE | 0 | Auto (GPS + GLONASS + Galileo + BeiDou) |
| GPS_AUTO_SWITCH | 1 | Allow automatic GPS switchover |
| GPS_POS1_X / Y / Z | 0.0 | Antenna offset from vehicle CG (set after install) |

Notes:
- `GPS_TYPE=9` selects the Septentrio driver in ArduPilot. Keep `GPS_AUTO_CONFIG=1` so the receiver is configured over UBX on every boot.
- With dual antennas (mosaic-G5 P3H), set `GPS_TYPE=9` on the primary and enable the second receiver on the secondary port (`GPS2_TYPE=9`, `GPS2_BAUD_RATE=9`) — ArduPilot uses the second antenna for heading.

## PX4 Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| GPS_1_GNSS_ID | 1 | Septentrio |
| GPS_1_CONFIG | TELEM2 | Serial port |
| GPS_1_BAUD | 115200 | Baud rate |
| GPS_1_PROTOCOL | 14 | Septentrio SBF / NMEA (autodetect usually works) |
| EKF2_AID_MASK | 1 | Enable GNSS position/velocity fusion |
| EKF2_GPS_CHECK | 245 | Standard GNSS checks (default) |

Notes:
- `GPS_1_GNSS_ID=1` is the Septentrio driver ID in PX4. `GPS_1_PROTOCOL` is usually auto-detected, but pinning it to the Septentrio value avoids boot-time negotiation.
- After changing parameters, reboot the FC, then confirm in the console that the GPS reports `RTCM`-capable SBF output and a 3D fix.

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
| Connection drops | Verify baud rate 115200 on both ends |
| Fix drops near power lines / antennas | RF interference — see AIM+ anti-jamming below |

## AIM+ Anti-Jamming

Septentrio receivers reject in-band RF interference with **AIM+** — roughly **40-60 dB** of mitigation versus ~25 dB on typical consumer GNSS modules (u-blox F9P class). Symptoms of interference-limited RTK: fix drops to float in the same physical location every pass, satellite SNR fades on specific azimuths, or the receiver loses lock near power lines, electric fences, or 4G/5G sites. AIM+ runs continuously and needs no configuration.

## SBF Parser

This repo includes `sbf-parser.py` to extract position data from Septentrio binary log files (PVTGeodetic + AttEuler blocks), with CRC validation and UTC time conversion.

Quick test without hardware — generate a synthetic log, then parse it:

    python make-sample-sbf.py sample.sbf --seconds 30 --attitude
    python sbf-parser.py sample.sbf --check-crc --utc -o sample.csv

Parser options:

| Option | Effect |
|--------|--------|
| `--check-crc` | Validate CRC-16/X25 on every block (recommended; drops corrupt blocks) |
| `--utc` | Add a UTC timestamp column (GPS week + TOW, leap-second corrected) |
| `-o FILE` | Output CSV path (default `sbf_output.csv`) |

CSV columns: `tow, wnc, mode, nrsv, lat, lon, height` plus `roll, pitch, heading` when the log contains AttEuler blocks (dual-antenna heading receivers).

The sample generator writes a synthetic straight-line path at 1 Hz (mostly RTK Fixed, a few RTK Float epochs) so you can exercise the parser without a receiver. The data is clearly synthetic — it is for testing, not analysis.

## Documentation

- [Septentrio GNSS Receivers with ROS: Official ROSaic Driver Guide](docs/ros-integration-guide.md) - ROS 1/ROS 2 integration, INS YAML config, NED/ENU frames, integration comparison
- [Jammertest 2025 Results: AIM+ Keeps UAVs on Mission](docs/jammertest-2025-results.md) - field evidence for AIM+ anti-jamming / anti-spoofing
- [CAN/J1939 Machine-Control Integration](docs/machine-control-can-j1939.md)

---

---

**[Browse GNSS Receivers](https://uav-gnss.com/product-category/gnss-receiver/)** | **[AIM+ Technology](https://uav-gnss.com/aim-resilient-gnss/)** | **[Integration Guide Blog](https://uav-gnss.com/blog/)**

*Maintained by UAV GNSS — Septentrio-based GNSS receivers for professional UAV operations worldwide.*
