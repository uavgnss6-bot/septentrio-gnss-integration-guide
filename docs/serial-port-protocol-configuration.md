# Serial Ports, Baud Rates and Data Streams — SBF / NMEA / RTCM Configuration

> You wired TX to RX, the port is open, and the autopilot still reports no fix. In our
> support inbox that is almost never a receiver fault — it is a port/baud/protocol-direction
> mismatch. This page is the port-level companion to the parameter tables in the main README.

---

## 1. How many serial ports do you actually have?

The port count depends on the receiver, not on the interface you plug in. Counted from the
official interface maps:

| Receiver | Engine | Serial ports | Other links |
|----------|--------|--------------|-------------|
| **HB10** | AsteRx-m3 Pro+ | **3x UART** (LVTTL, 115200 bps - 4 Mbps) | USB-C, MicroSD, 1PPS out, EVENT in, NRST |
| **HB59** | AsteRx-m3 Pro+ | **3x UART** (LVTTL) | 100M Ethernet, USB-C, MicroSD, 1PPS, EVENT |
| **HB6 / HB6 Pro** | mosaic-X5 | **2x UART** | USB (4G on Pro) |
| **EV322 / HB51 / HB52** | mosaic-G5 | **2x UART** (TTL) + I2C | PPS, EVENT |
| **HB3** (machine-control box) | AsteRx-m3 Pro+ | SER M12 | CAN (PWR) M12 x2, Ethernet M12, 4G LTE, UHF, WiFi/BT |

Two things to internalise:

- **These UARTs are LVTTL (3.3 V logic) at the module.** They are **not** RS-232, RS-422 or
  RS-485. Feeding a true RS-232 source straight into the receiver — or into the flight
  controller — will not work and can damage the port. Use the matching connector/level
  shifter on the carrier board, or an external transceiver if you genuinely need RS-232.
- **Nothing here is native CAN/J1939.** CAN exists at product level on the HB3 box; on
  HB10/HB59 the CAN/J1939/RS-232 route is an external gateway/transceiver.

## 2. Port allocation — the three-stream rule

Serial links fail most often because two logical jobs were pushed onto one port. Budget one
port per job:

| Port | Job | Protocol | Typical rate |
|------|-----|----------|--------------|
| UART 1 | Autopilot position/status | NMEA 0183 out | 5-10 Hz |
| UART 2 | Corrections in (+ NMEA mirror out) | RTCM v3 / CMR in | as broadcast |
| UART 3 (HB10/HB59) | Raw logging / ROS driver / radio | SBF out | 1 Hz, up to 100 Hz bursts |

At minimum, keep **corrections in** on their own port if you can — on a single-port build you
must multiplex RTCM input and NMEA output on the same UART, and any misconfiguration there
looks exactly like a dead correction source.

### Wiring (dual-port example)

```
Septentrio receiver                 Flight controller (Pixhawk class)
-------------------                 ---------------------------------
UART1 TX  ----------------------->  GPS1 RX
UART1 RX  <-----------------------  GPS1 TX
GND       ------------------------  GND
5V        ------------------------  5V  (dedicated UART 5V pin, not the servo rail)

Septentrio receiver                 Telemetry / NTRIP link
-------------------                 ----------------------
UART2 RX  <-- RTCM v3 corrections --  radio / companion TX
UART2 TX  --- NMEA mirror (opt.) -->  radio / companion RX
```

Match `UART1` to whatever the flight controller labels `GPS1` (or `TELEM2` on some boards).
It is the same UART; what matters is that **both ends agree on baud and protocol**.

## 3. Baud rate

- **115200 bps is the safe default** for autopilot integration and is what our parameter
  tables assume (`GPS_BAUD_RATE=9` on ArduPilot, `GPS_1_BAUD=115200` on PX4).
- AsteRx-m3 Pro+ UARTs on HB10/HB59 support **up to 4 Mbps** — that headroom exists for raw
  SBF logging (full-band multi-constellation data will not fit in 115200).
- Baud must match exactly on both ends. A mismatch usually shows as garbage characters or
  framing/parity errors, not as a clean "no data" — so check the receiver's own port counters
  before blaming the cable.
- Only change baud on one side at a time and re-verify. Changing both ends blind is how two
  working ports become one broken link.

## 4. Protocol direction matrix

The silent failure in this list is direction: corrections must flow **into** the rover.

| Protocol | Direction | Carries | Goes to |
|----------|-----------|---------|---------|
| **NMEA 0183** (v3.01/v4.0) | receiver -> autopilot | GGA/RMC position + status | ArduPilot/PX4 GPS port |
| **SBF** | receiver -> logger / computer | PVTGeodetic, AttEuler, raw observables | SD card, ROS driver, post-processing |
| **RTCM v2.x / v3.x** | base -> rover (**IN**) | corrections | rover's correction port |
| **RTCM v3.x / CMR v2.0 / CMR+** | rover-base -> rover (**IN**) | corrections | rover's correction port |

So: NMEA and SBF are *outputs* you enable; RTCM/CMR is an *input* the rover must be told to
accept. A receiver streaming perfect NMEA to the autopilot while ignoring its RTCM input will
sit in Single forever, with a healthy-looking data link.

## 5. Configure the receiver (web interface)

1. Open the Septentrio web interface and go to the **communication / port settings** page for
   the port you are using (COM1/COM2/COM3 mapping varies by carrier — check the pinout).
2. Set **baud rate** and **input/output streams** per port: NMEA output on the autopilot port,
   SBF blocks on the logging port, RTCM/CMR input on the correction port.
3. On the logging port, enable the SBF blocks you actually need —
   `PVTGeodetic` for position/fix mode, `AttEuler` for dual-antenna heading/roll/pitch.
   Logging every block at high rate fills an SD card fast; pick blocks first, then rate.
4. For RTK, configure the correction source under **RTK settings**: NTRIP client (caster
   host/port 2101/mount point/credentials), a local base over radio, or the receiver acting as
   base/caster itself. Then watch **correction age** — it is the single most useful RTK metric
   you have.
5. Save the configuration and, on boxed receivers, store it as the boot configuration so a
   power cycle does not drop you back to defaults.

## 6. Configure the autopilot

ArduPilot:

| Parameter | Value | Notes |
|-----------|-------|-------|
| `GPS_TYPE` | 9 | Septentrio |
| `GPS_BAUD_RATE` | 9 | 115200 |
| `GPS_RATE_MS` | 100 | 10 Hz |
| `GPS_AUTO_CONFIG` | 1 | Receiver configured on every boot |
| `GPS2_TYPE` / `GPS2_BAUD_RATE` | 9 / 9 | Second receiver or dual-antenna heading |

PX4:

| Parameter | Value | Notes |
|-----------|-------|-------|
| `GPS_1_GNSS_ID` | 1 | Septentrio |
| `GPS_1_CONFIG` | TELEM2 | Serial port |
| `GPS_1_BAUD` | 115200 | Must match receiver |
| `GPS_1_PROTOCOL` | 14 | Septentrio SBF/NMEA (autodetect usually works) |

Rule: **one driver per port.** Do not point two autopilot drivers (or an autopilot plus a
companion log script) at the same UART — they will fight over the stream and both will look
intermittent.

## 7. Verify before you fly or drive

1. The autopilot reports a 3D fix and a satellite count (16+ is a healthy open-sky figure).
2. Fix type reaches **RTK Fixed** — not merely "3D".
3. **Correction age** is low and steady. Spiking age = link problem, not receiver problem.
4. Satellite C/N0 is stable across the sky, without a block of satellites dying on one azimuth.
5. Then prove it from the log: capture SBF, and summarise fix quality plus every RTK drop
   event with the parser in this repo:

```
python make-sample-sbf.py sample.sbf --seconds 30 --drops 10,20
python sbf-parser.py sample.sbf --check-crc --utc --analyze
```

`--analyze` prints time spent in each fix mode and each RTK Fixed -> degraded transition with
its start time, duration, and satellite count at onset vs. minimum during the drop. That
distinguishes a wiring/baud fault from a multipath or interference fault without guessing.

## 8. Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| No data at all | TX/RX swapped; wrong port; baud mismatch |
| Garbage / framing errors | Baud or protocol mismatch on that port |
| 3D fix but never RTK Fixed | Corrections not arriving, or RTCM wired/directed OUT instead of IN |
| RTK Fixed drops to float, then recovers when you move | Multipath (canopy, buildings, vehicle body) — antenna placement |
| Fix lost near power lines, fences, 4G sites | RF interference — see AIM+ below |
| Data dies at high output rate | Baud too low for the configured stream set; reduce blocks or raise baud |
| Two receivers conflict / intermittent position | Both drivers on one UART, or mismatched `GPS2_*` configuration |
| Receiver resets to defaults after power cycle | Configuration not stored as boot config |

## 9. Why interference immunity shows up here

A port can be perfectly configured and still lose its fix: AIM+ on Septentrio receivers
rejects in-band RF interference with roughly **40-60 dB** of mitigation versus ~25 dB on
typical consumer GNSS modules (u-blox F9P class). If your fix drops to float in the *same
physical location* every pass while C/N0 sags across many satellites at once, the link is
fine — the RF environment is not. AIM+ runs continuously and needs no configuration.

---

**[GNSS Receivers](https://uav-gnss.com/product-category/gnss-receiver/)** |
**[AIM+ Resilient GNSS](https://uav-gnss.com/aim-resilient-gnss/)** |
**[Integration Guides](https://uav-gnss.com/blog/)**

*Maintained by UAV GNSS — Septentrio-based GNSS receivers for professional UAV operations worldwide.*
