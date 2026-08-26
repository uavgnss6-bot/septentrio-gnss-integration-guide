# Septentrio GNSS Receivers with ROS: Official ROSaic Driver Guide

> Companion to this repository's [ArduPilot](README.md#ardupilot-parameters) and [PX4](README.md#px4-parameters) guides.
> This guide covers the **ROS route**: integrating Septentrio mosaic / AsteRx receivers (the engines inside
> [UAV GNSS receivers](https://uav-gnss.com/product-category/gnss-receiver/)) with ROS 1 and ROS 2 via the
> official open-source driver **ROSaic** (`septentrio_gnss_driver`).

---

## 1. Why ROS compatibility matters for GNSS selection

In ROS robots, self-driving platforms, and UAVs, the GNSS receiver is the primary position source in the
navigation fusion chain. Evaluation usually comes down to three things:

1. **Positioning capability** — accuracy and reliability (centimeter-level RTK)
2. **Environmental resilience** — anti-jamming and anti-spoofing (AIM+ with OSNMA, field-proven at
   [Jammertest 2025](jammertest-2025-results.md))
3. **Ecosystem compatibility** — how quickly the receiver plugs into your existing stack

Septentrio scores on all three with publicly verifiable evidence. This guide focuses on the ecosystem side:
what ROSaic does, which receivers and ROS versions it supports, how to configure GNSS/INS receivers, and how
the integration effort compares with building your own driver.

## 2. Flight controller vs ROS vs GNSS: who does what

- **Flight controller** (PX4 / ArduPilot / Pixhawk): runs on dedicated hardware, controls motors in real
  time, maintains attitude stability, executes low-level motion control.
- **ROS (Robot Operating System)**: runs on the onboard computer (Raspberry Pi, NVIDIA Jetson, NUC, …),
  handles sensor data processing, perception, path planning, and mission decisions.
- **How they cooperate**: the two communicate over protocols such as MAVLink. ROS outputs goals and
  obstacle-avoidance decisions; the flight controller executes them stably.

**Why the flight controller alone is not enough for deep GNSS work:**

- Flight-controller drivers support only basic protocols (NMEA/UBX). SBF binary parsing, fine-grained RTK
  status, AIM+ anti-jamming state, and multiple differential correction sources need a ROS driver.
- Flight controller chips have limited compute; complex fusion and avoidance need the companion computer.

In one sentence: the flight controller keeps you flying, ROS makes you smart — and Septentrio receivers
integrate into both layers.

## 3. Receiver families that speak ROSaic

| Family | Products & fit |
|--------|----------------|
| mosaic (module level) | mosaic-X5 (multi-frequency, multi-constellation RTK), mosaic-G5 (high cost-performance), mosaic-H (dual-antenna heading) — low power, small footprint |
| AsteRx (board / receiver level) | AsteRx-m3 Pro+, AsteRx-SB Pro+, AsteRx-SBi3 Pro and more, incl. GNSS/INS models with dual-antenna heading |
| Complete receivers | Ruggedized enclosed receivers (e.g. AsteRx SBi3 Pro) for vehicle and industrial scenarios |

Shared capabilities: centimeter-level RTK across GPS / Galileo / GLONASS / BeiDou / QZSS / NavIC, AIM+
interference mitigation with OSNMA signal authentication, and IMU-fused GNSS/INS output (position,
velocity, attitude). At the 2025 Jammertest, receivers held centimeter accuracy through roughly 100
interference scenarios and raised correct spoofing alarms — see [Jammertest 2025 results](jammertest-2025-results.md).

## 4. ROSaic: what the official driver does

`septentrio_gnss_driver` (brand name **ROSaic** = ROS + mosaic) is a single C++ repository maintained by
Septentrio on GitHub, covering both ROS generations — ROS 1 (Melodic, Noetic) and ROS 2 (Foxy through
Galactic, Humble, Iron, Jazzy, Kilted, Lyrical, Rolling, and later).

### 4.1 Compatibility quick reference

| Dimension | Supported |
|-----------|-----------|
| Receiver models | mosaic-X5, mosaic-H, mosaic-G5 series; AsteRx m3 Pro+, AsteRx i3 D Pro+, AsteRx SBi3 Pro(+), AsteRx RBi3 Pro(+) — GNSS+INS solutions included |
| ROS versions | ROS 1: Melodic, Noetic · ROS 2: Foxy to Rolling and beyond |
| Connections | Serial, TCP, UDP, USB (RNDIS and TCP/IP) |
| Protocols | SBF binary + ASCII messages (key NMEA included) |
| Output topics | `sensor_msgs/NavSatFix`, `gps_common/GPSFix`, `nav_msgs/Odometry` (INS models) |
| Coordinate frames | Built-in NED→ENU axis-convention conversion |
| RTK corrections | NTRIP, TCP/IP streams, and serial — configured simultaneously |
| Resilience state | AIM+ (incl. OSNMA) anti-jamming / anti-spoofing status published to ROS topics |

### 4.2 Technical highlights

- **Native SBF decoding**: PVTGeodetic, PosCovGeodetic, ChannelStatus, MeasEpoch, AttEuler, AttCovEuler,
  VelCovGeodetic, DOP and more — no lossy NMEA translation for RTK status, signal health, or attitude.
- **NED→ENU conversion**: Septentrio outputs in NED; ROS expects ENU. The driver resolves the mismatch
  internally, with an explicit convention selector for INS models.
- **Standard messages**: output plugs straight into fusion frameworks such as `robot_localization`
  (EKF/UKF).
- **Dev & debug**: launch files + parameter directories ship with the package; PCAP replay supported;
  binary install (recommended) or source build.

### 4.3 INS receivers: key YAML configuration

GNSS+INS models (AsteRx-i3 D Pro(+), AsteRx SBi3 Pro(+), AsteRx RBi3 Pro(+)) need these settings in the
driver YAML (per Septentrio's official integration guide):

```yaml
receiver_type: ins                 # enable INS receiver mode
use_ros_axis_orientation: ENU      # NED or ENU — match your robot's frame
ins_spatial_config:
  imu_orientation: [0, 0, 0]       # IMU orientation angles theta X/Y/Z
  poi_lever_arm: [0, 0, 0]         # point-of-interest lever arm
  ant_lever_arm: [0, 0, 0]         # GNSS antenna reference point -> IMU
  vsm_lever_arm: [0, 0, 0]         # velocity sensor -> IMU
ins_initial_heading: auto          # auto (from GNSS motion) or stored
ins_std_dev_mask: 1.0              # attitude/position uncertainty quality gate
ins_use_poi: true                  # must be on when publishing TF (default true)
ins_vsm:                           # velocity sensor measurement input
  source: ros                      # ros (Odometry/Twist), tcp/ip, or serial
```

These parameters define the spatial relationship between the IMU, antennas, and vehicle origin — errors
here propagate directly into fused position and attitude output.

### 4.4 INS topics and validation

INS receivers publish topics backed by the INSNavGeod, INSNavCart, ExtSensorMeas, IMUSetup, and
VelSensorSetup SBF blocks. Standard ROS workflow applies:

```bash
ros2 topic list                 # enumerate published topics
ros2 topic echo <topic_name>    # inspect data
```

The bundled PlotJuggler integration renders acceleration, trajectory, and attitude streams in real time.

## 5. Integration cost: official driver vs building your own

For a typical outdoor inspection robot on ROS 2 Humble with `robot_localization` doing GNSS/IMU fusion:

| Item | Self-developed / third-party | Septentrio + ROSaic |
|------|------------------------------|---------------------|
| Driver origin | Your team owns code + maintenance | Septentrio-maintained, open source, continuously updated |
| Onboarding effort | Protocol parsing, frame conversion, corrections by hand | Install package, configure launch parameters |
| Message output | Custom wrappers needed | NavSatFix / GPSFix / Odometry out of the box |
| Coordinate handling | NED→ENU implemented in-house | Built-in, selectable convention |
| RTK corrections | Custom NTRIP client required | NTRIP / TCP / serial simultaneously |
| Resilience visibility | Receiver internals largely opaque | AIM+ status on ROS topics, monitorable and alertable |
| Time to verified integration | Weeks to months | Typically days |

> Timelines are engineering estimates — actual results depend on team experience and project complexity.

Value summary: **time** (configuration replaces driver development), **risk** (upstream maintainer owns
compatibility), **capability** (multi-source RTK, AIM+ reporting, frame conversion in the box), and
**ecosystem fit** (standard messages drop straight into `robot_localization`).

## 6. Beyond ROS: the flight controller route

ROSaic is not the only path. mosaic-series receivers also work directly with Pixhawk, ArduPilot, and PX4
Autopilot (see the [ArduPilot](README.md#ardupilot-parameters) and [PX4](README.md#px4-parameters) sections
of this guide), and Septentrio's mosaicHAT reference design (mosaic-X5 + Raspberry Pi) plus the Robotics
Interface Board (RIB) simplify hardware bring-up. Teams can start on the flight-controller route and move
to a full ROS stack later — or run both.

## 7. FAQ

**Is the Septentrio ROS driver open source?**
Yes — `septentrio_gnss_driver` is maintained in the open on Septentrio's GitHub under the ROSaic brand,
free to use, and actively updated across ROS 1 and ROS 2 releases.

**Do I need a GNSS/INS receiver to benefit from ROSaic?**
No. GNSS-only models (mosaic-X5, mosaic-G5, AsteRx m3 Pro+) publish NavSatFix and GPSFix. INS models
additionally publish Odometry with full attitude; everything else works identically either way.

**Why does the driver convert NED to ENU?**
Septentrio receivers follow NED (North-East-Down); ROS frames use ENU (East-North-Up). Without conversion,
fused position and orientation would be subtly wrong. ROSaic handles it internally, with an explicit
convention selector for INS models.

**How do I configure lever arms for an INS receiver?**
In the driver YAML under `ins_spatial_config`: `imu_orientation` for mounting angles and the three
lever-arm offsets — `poi_lever_arm`, `ant_lever_arm` (antenna to IMU), `vsm_lever_arm` (velocity sensor to
IMU). These physical offsets directly affect fusion accuracy.

**Can I develop against ROSaic without hardware?**
Yes — the driver supports PCAP replay, so you can capture receiver data once and exercise the full pipeline
offline.

**How long does a typical integration take?**
Standard setups are usually verified within days — install, set receiver type + connection parameters,
launch. Custom INS spatial configuration adds time but rarely reaches the weeks-to-months scale of a
self-developed driver.

## 8. References

| Item | Source |
|------|--------|
| septentrio_gnss_driver repository | <https://github.com/septentrio-gnss/septentrio_gnss_driver> |
| mosaic / AsteRx product pages | <https://web.septentrio.com/GH-SSN-modules> · <https://web.septentrio.com/INS-SSN-Rx> |
| Jammertest 2025 results | <https://www.septentrio.com/en/learn-more/insights/results-jammertest-2025-withstanding-gps-jamming-and-spoofing> |
| ROS documentation | <https://wiki.ros.org/> · <https://www.ros.org/> |
| robot_localization | <https://github.com/cra-ros-pkg/robot_localization> |
| ROSaic knowledge-base article | <https://customersupport.septentrio.com/s/article/ROSaic-a-ROS-driver-to-integrate-Septentrio-receivers-in-robotics-applications> |
| GNSS/INS + ROSaic integration guide | <https://customersupport.septentrio.com/s/article/How-to-integrate-a-Septentrio-GNSS-INS-receiver-with-ROSaic> |

---

**[Browse GNSS Receivers](https://uav-gnss.com/product-category/gnss-receiver/)** | **[AIM+ Technology](https://uav-gnss.com/aim-resilient-gnss/)** | **[Robotics & Autonomous Navigation](https://uav-gnss.com/solutions/robotics-autonomous-navigation-gnss/)**

*Maintained by UAV GNSS — Septentrio-based GNSS receivers for professional UAV operations worldwide.*
