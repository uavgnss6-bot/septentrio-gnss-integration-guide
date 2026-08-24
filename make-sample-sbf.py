#!/usr/bin/env python3
"""
Generate a synthetic Septentrio SBF log file for testing sbf-parser.py
without real GNSS hardware.

Produces 1 Hz PVTGeodetic (block 4028) blocks along a straight-line path,
plus optional AttEuler (block 4031) heading blocks (--attitude).

The data is SYNTHETIC - generated for parser testing/demo purposes,
not recorded from a receiver.

Usage:
    python make-sample-sbf.py output.sbf [--seconds 30] [--attitude]
"""

import struct
import sys
import argparse


def crc16_x25(data):
    """CRC-16/X25 - the SBF CRC (same implementation as sbf-parser.py)."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc % 2 == 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return crc ^ 0xFFFF


def sbf_block(block_id, payload):
    """Wrap a payload into an SBF block: sync, CRC, block id, length, data."""
    length = 8 + len(payload)
    crc = crc16_x25(struct.pack('<HH', block_id, length) + payload)
    return struct.pack('<HHHH', 0xFAFA, crc, block_id, length) + payload


def pvt_block(tow_ms, wnc, lat0, lon0, h0, dlat, dlon, mode, nrsv):
    """PVTGeodetic (4028) block for a point on a straight-line path."""
    t = tow_ms / 1000.0
    lat = lat0 + dlat * t
    lon = lon0 + dlon * t
    h = h0 + 0.05 * t
    payload = struct.pack('<IhBB', tow_ms, wnc, mode, 0)
    payload += struct.pack('<ddd', lat, lon, h)
    payload += struct.pack('<fffffff', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)  # undulation + vel + cog + clocks
    payload += struct.pack('<BBBB', 0, 0, nrsv, 0)  # time system, datum, NrSV, WACorr
    return sbf_block(4028, payload)


def att_block(tow_ms, wnc, heading0):
    """AttEuler (4031) block with slowly changing heading."""
    h = (heading0 + 0.1 * (tow_ms / 1000.0)) % 360.0
    payload = struct.pack('<IhBB', tow_ms, wnc, 4, 0)
    payload += struct.pack('<ffffff', 0.5, 1.0, h, 0.05, 0.05, 0.2)  # roll, pitch, heading + accuracies
    return sbf_block(4031, payload)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Generate a synthetic SBF test log.')
    ap.add_argument('output', help='output .sbf path')
    ap.add_argument('--seconds', type=int, default=30, help='duration in seconds (default 30)')
    ap.add_argument('--attitude', action='store_true', help='include AttEuler heading blocks')
    ap.add_argument('--wnc', type=int, default=2400, help='continuous GPS week (default 2400 ~ 2026)')
    args = ap.parse_args()

    lat0, lon0, h0 = 40.7128, -74.0060, 15.0   # NYC as a recognizable start point
    dlat, dlon = 0.00001, 0.00002              # ~1-2 m per second drift
    out = bytearray()
    n_pvt = 0
    for sec in range(args.seconds):
        tow = sec * 1000
        # mostly RTK Fixed (4), a few RTK Float (3) to exercise the mode map
        mode = 3 if sec in (10, 11) else 4
        nrsv = 12 + (sec % 9)
        out += pvt_block(tow, args.wnc, lat0, lon0, h0, dlat, dlon, mode, nrsv)
        n_pvt += 1
        if args.attitude:
            out += att_block(tow, args.wnc, 90.0)
    with open(args.output, 'wb') as f:
        f.write(bytes(out))
    print('Wrote %s: %d PVT blocks (%d s), attitude=%s'
          % (args.output, n_pvt, args.seconds, 'yes' if args.attitude else 'no'))
