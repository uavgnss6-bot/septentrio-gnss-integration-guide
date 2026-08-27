# CAN / J1939 Machine-Control Integration Guide

How to connect Septentrio-powered GNSS receivers to the CAN-based machine buses used on
construction and agricultural equipment (SAE J1939, ISOBUS, CANopen, raw CAN 2.0B).

Companion articles: [GNSS Receivers with CAN Bus Output for Machine Control](https://uav-gnss.com/gnss-receiver-can-bus-output-machine-control/)
and [J1939 for GNSS: How Receivers Talk to Construction & Agriculture Machines](https://uav-gnss.com/j1939-gnss-receivers-construction-agriculture-machines/).

## Key fact: CAN is not native to the GNSS chip

The Septentrio engines used in our receivers (AsteRx-m3 Pro+, mosaic-X5, mosaic-G5) expose
high-speed **serial (LVTTL)**, **USB** and **Ethernet**. They do **not** expose CAN/J1939 at the
chip level. Machine-bus output is a **product-level** feature — it comes from the receiver's
carrier/box design (or an external gateway), not from the silicon.

That means when you evaluate any GNSS receiver for machine control, ask three questions:

1. **Does the product expose a CAN connector?** (Not just "serial".)
2. **Which protocol?** J1939 PGNs, CANopen, or raw CAN 2.0B — and is it configurable?
3. **What serial levels?** LVTTL (3.3 V logic) vs RS-232 / RS-422 / RS-485.

## Receiver options (UAV GNSS lineup)

| Receiver | Machine-bus interfaces | Integration path |
|---|---|---|
| [HB3](https://uav-gnss.com/product/rb3-gnss-box-receiver-powered-by-septentrio-asterx-m3-pro/) (IP67 box) | **CAN (PWR) M12 x2** (CAN + power on one connector) · Serial M12 · Ethernet M12 · 4G LTE · UHF · Wi-Fi · BT 5.0 | Direct harness wiring. Onboard Linux A7 app processor; NTRIP caster/server/client. Protocol (J1939 / CANopen / raw CAN 2.0B) and serial levels (RS-232/RS-485) configured for the application — contact engineering for the PGN map. |
| [HB10](https://uav-gnss.com/product/hb10-dual-antenna-rtk-gnss-receiver-septentrio-asterx-m3-pro/) (module) | 3x UART (LVTTL, 115200-4M bps) · USB-C · 1PPS out · EVENT in · MAIN+AUX1 antennas | OEM boards: feed a J1939/CAN gateway from a UART. Add external transceiver for RS-232/RS-422/RS-485 levels. |
| [HB59](https://uav-gnss.com/product/hb59-multi-function-oem-gnss-receiver-septentrio-asterx-m3-pro/) (OEM board) | 3x UART (LVTTL) · 100M Ethernet · USB-C · Micro SD · 1PPS · EVENT | Machine-control networks and base/rover setups: Ethernet-to-J1939 gateway path, NMEA/SBF/RTCM over TCP/UDP. |

All three: dual-antenna heading (0.15 deg @ 1 m baseline, 0.03 deg @ 5 m), RTK 0.6 cm + 0.5 ppm,
AIM+ anti-jamming, OSNMA anti-spoofing. See the [receiver category](https://uav-gnss.com/product-category/gnss-receiver/).

## Serial setup (all receivers)

- Default baud: **115200** (range 115200-4,000,000 bps)
- Output: NMEA 0183 (v3.01/v4.0), Septentrio SBF, RTCM v2.x/v3.x, CMR/CMR+
- Differential input: RTCM 3.x (MSM) over UART, USB or (HB59) Ethernet
- Timing: 1PPS out (5 ns), EVENT input for time-synced machine control

## Direct-CAN wiring (HB3)

The two CAN (PWR) M12 connectors carry CAN_H/CAN_L plus power, so the box wires directly into a
vehicle harness — no extra converter. Confirm with engineering:

- Protocol and PGN set for your machine model (J1939 / ISOBUS / CANopen / raw CAN 2.0B)
- Termination (120 ohm) and bus topology per CAN 2.0B rules
- DBC file / message map for your controller

## Gateway path (HB10 / HB59 / any serial receiver)

When the receiver has no native CAN, use a serial- or Ethernet-to-CAN/J1939 gateway:

1. Configure the receiver UART (or HB59 Ethernet) for NMEA or SBF output at 115200 bps.
2. Wire the UART TX/RX (LVTTL, 3.3 V) to the gateway's serial input (level-shift to RS-232/RS-485
   if required by the gateway).
3. Configure the gateway to map position/heading/speed into J1939 PGNs for the machine ECU.
4. Validate with a CAN analyzer before production.

## Anti-jamming note

Machine environments are EMI-heavy: power lines, welders, alternators, site radios. AIM+ (up to
60 dB mitigation) keeps RTK fixed where consumer modules drop out — see
[our anti-jamming results](docs/jammertest-2025-results.md).

---

*Browse [GNSS Receivers](https://uav-gnss.com/product-category/gnss-receiver/) · [AIM+ Technology](https://uav-gnss.com/aim-resilient-gnss/) · [Request a quote](https://uav-gnss.com/request-quote/) · Maintained by [UAV GNSS](https://uav-gnss.com)*
