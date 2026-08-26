# Jammertest 2025 Results: AIM+ Keeps UAVs on Mission Through 100+ Interference Scenarios

> Field evidence for the AIM+ anti-jamming claims referenced throughout this repository.
> Source: Septentrio's report of the annual Norwegian government anti-jamming/anti-spoofing test.

---

Interference is the silent failure mode of drone operations. A jammed or spoofed GNSS receiver does not
always announce itself — the aircraft simply ends up somewhere it should not be. At **Jammertest 2025**, the
annual Norwegian government test of anti-jamming and anti-spoofing hardware, Septentrio receivers with
**AIM+** technology held centimeter-level positioning through roughly 100 jamming and spoofing scenarios,
while rival receivers drifted meters — sometimes more than ten — off their true position.

Here is what those results mean for UAV and robotics teams, and which receivers bring that protection to
your airframe.

## What Jammertest actually is

Jammertest is a real-world, government-run exercise held in Andøya, Norway: signal generators on the ground
emit jamming and spoofing against receivers mounted in vehicles and aircraft, and the hardware under test
has to keep producing trustworthy positions. It is not a lab simulation — antennas are mounted on real
aircraft, and the interference is broadcast over real distances. A receiver that survives Jammertest has
survived the closest thing the industry has to a combat RF environment.

## What AIM+ held through the 2025 scenarios

Septentrio's AIM+ (Advanced Interference Mitigation and Monitoring) technology combines:

- **Advanced interference mitigation** — in-band jamming suppression, roughly **40–60 dB** of mitigation
  versus ~25 dB on typical consumer GNSS modules (u-blox F9P class).
- **OSNMA authentication** — Galileo's Open Service Navigation Message Authentication, which detects
  spoofed signals rather than merely reporting a good fix.
- **Continuous monitoring** — interference state is reported to the host system (in ROS via
  `septentrio_gnss_driver`; in ArduPilot/PX4 via the standard receiver status), so you can log, alarm, and
  react.

At Jammertest 2025 the summary result: **centimeter-level accuracy sustained through ~100 interference
scenarios**, and in spoofing tests the receivers raised **correct alarms**. Competing receivers drifted
meters off position under the same signal conditions.

## What this means for your UAV

1. **RTK fixed ≠ interference-free.** If a receiver without AIM+ holds "RTK Fixed" until the jammer turns
   on, then silently degrades to float or worse, the mission is already compromised. AIM+ keeps the fix.
2. **Spoofing is the harder threat.** Jamming is noise; spoofing is a counterfeit signal. OSNMA
   authentication is what turns a "looks fine" spoofed fix into a detectable anomaly.
3. **Interference state belongs in your logs.** Because AIM+ status is exposed to the flight stack, you
   can correlate "fix dropped" events with interference events in post-mission analysis — instead of
   guessing between multipath, corrections, and RF.

## Receivers that bring AIM+ to your platform

| Receiver | Form factor | Notes |
|----------|-------------|-------|
| [EV322](https://uav-gnss.com/product/ev322-gnss-receiver-powered-by-septentrio-mosaic-g5/) | Enclosed box (mosaic-G5) | Drop-in for Pixhawk/ArduPilot/PX4 and ROS stacks |
| HB6 / HB6 Pro | Enclosed box (mosaic-X5, 4G) | RTK + network corrections in one unit |
| HB51 / HB52 | Heading modules (mosaic-X5 P3H) | Dual-antenna heading + AIM+ |
| HB10 | Dual-antenna (AsteRx-m3 Pro) | Survey-grade, AIM+ |

All are powered by Septentrio mosaic / AsteRx engines, so they inherit the exact AIM+ behavior tested at
Jammertest. See the full [receiver lineup](https://uav-gnss.com/product-category/gnss-receiver/) for specs.

## How to verify AIM+ state on your stack

- **ROS**: ROSaic (`septentrio_gnss_driver`) publishes AIM+/OSNMA status to topics — see the
  [ROS integration guide](ros-integration-guide.md).
- **ArduPilot**: `GPS_TYPE=9` — receiver status is visible in the ground station; watch the satellite
  status page during interference.
- **PX4**: `GPS_1_GNSS_ID=1` — monitor receiver status / satellite info; AIM+ mitigation state is
  reported in the receiver's SBF output.

## FAQ

**Can jamming crash a drone?**
Yes. A jammed receiver loses position; depending on the flight mode the autopilot may fail safe, loiter,
or drift. In GNSS-denied environments with no other positioning source, that is a real safety event.

**Is AIM+ automatic, or do I need to configure it?**
Automatic. AIM+ mitigation runs continuously and needs no configuration. OSNMA authentication is enabled
via the receiver's web interface / RxTools.

**Does AIM+ work with Pixhawk / ArduPilot / PX4?**
Yes. AIM+ is receiver-side; any autopilot that accepts NMEA or SBF over UART works. See the
[ArduPilot](README.md#ardupilot-parameters) and [PX4](README.md#px4-parameters) sections of this repo.

**Where can I read the full Jammertest 2025 report?**
Septentrio's public write-up:
<https://www.septentrio.com/en/learn-more/insights/results-jammertest-2025-withstanding-gps-jamming-and-spoofing>

---

**[Browse GNSS Receivers](https://uav-gnss.com/product-category/gnss-receiver/)** | **[AIM+ Technology](https://uav-gnss.com/aim-resilient-gnss/)** | **[Integration Guide Blog](https://uav-gnss.com/blog/)**

*Maintained by UAV GNSS — Septentrio-based GNSS receivers for professional UAV operations worldwide.*
