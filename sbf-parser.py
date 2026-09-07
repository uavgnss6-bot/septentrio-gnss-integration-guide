#!/usr/bin/env python3
"""
Septentrio SBF (Septentrio Binary Format) Parser
Extracts position, fix quality, and (optionally) attitude from SBF log files.

Improvements over the original parser:
  * Correct PVTGeodetic field offsets (lat/lon/height at 8/16/24, mode at 6, NrSV at 62)
  * Byte-level resync: scans for the 0xFA 0xFA sync instead of skipping 8 bytes on mismatch
  * CRC-16/X25 validation (--check-crc) per the SBF reference manual
  * AttEuler (block 4031) support: roll / pitch / heading / accuracies
  * TOW + WNc -> UTC time conversion (--utc)
  * NrSV (satellite count) included in CSV output

Usage:
    python sbf-parser.py input.sbf [--check-crc] [--utc] [--analyze] [-o output.csv]

    --analyze prints an RTK drop report (fix-quality summary + drop events with
    UTC/TOW timestamps and satellite counts) instead of a CSV.
    -o writes a CSV (tow, wn, mode, nrsv, lat, lon, height[, roll, pitch, heading]).
"""

import struct
import sys
import csv
import argparse
import datetime as dt
from collections import Counter

BLOCK_ID_PVT = 4028    # PVTGeodetic
BLOCK_ID_ATT = 4031    # AttEuler

MODE_MAP = {
    0: 'No GNSS',
    1: 'Single',
    2: 'Differential',
    3: 'RTK Float',
    4: 'RTK Fixed',
}

# GPS epoch and leap seconds (UTC = GPS - leap_seconds).
GPS_EPOCH = (1980, 1, 6)
LEAP_SECONDS = 18  # 18th leap second since 2017-01-01; valid through 2026


def crc16_x25(data):
    """CRC-16/X25 (poly 0x1021 reflected, init 0xFFFF, xorout 0xFFFF) - the SBF CRC."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc % 2 == 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return crc ^ 0xFFFF


def gps_week_to_utc(wnc, tow_ms):
    """Convert continuous GPS week + TOW (ms) to an ISO UTC string."""
    epoch = dt.datetime(*GPS_EPOCH, tzinfo=dt.timezone.utc)
    t = epoch + dt.timedelta(weeks=wnc, milliseconds=tow_ms) - dt.timedelta(seconds=LEAP_SECONDS)
    return t.isoformat()


def parse_sbf(filename, check_crc=False):
    """Parse SBF file, returning (pvt_records, attitude_records)."""
    results = []
    att = []
    with open(filename, 'rb') as f:
        data = f.read()
    i = 0
    n = len(data)
    while i < n - 7:
        # byte-level resync: find the 0xFA 0xFA sync marker
        if data[i] != 0xFA or data[i + 1] != 0xFA:
            i += 1
            continue
        block_id, block_len = struct.unpack_from('<HH', data, i + 4)
        if block_len < 8 or i + block_len > n:
            i += 2
            continue
        block = data[i:i + block_len]
        crc_stored = struct.unpack_from('<H', data, i + 2)[0]
        if check_crc:
            crc_calc = crc16_x25(block[4:])
            if crc_calc != crc_stored:
                i += 2
                continue
        payload = block[8:]
        if block_id == BLOCK_ID_PVT and len(payload) >= 32:
            tow = struct.unpack_from('<I', payload, 0)[0]
            wnc = struct.unpack_from('<h', payload, 4)[0]
            mode = payload[6]
            error = payload[7]
            lat = struct.unpack_from('<d', payload, 8)[0]
            lon = struct.unpack_from('<d', payload, 16)[0]
            height = struct.unpack_from('<d', payload, 24)[0]
            nrsv = payload[62] if len(payload) >= 63 else 0
            results.append({
                'tow': tow, 'wnc': wnc,
                'mode': MODE_MAP.get(mode, 'Unknown(%d)' % mode),
                'mode_id': mode,
                'error': error,
                'lat': lat, 'lon': lon, 'height': height,
                'nrsv': nrsv,
            })
        elif block_id == BLOCK_ID_ATT and len(payload) >= 20:
            tow = struct.unpack_from('<I', payload, 0)[0]
            wnc = struct.unpack_from('<h', payload, 4)[0]
            roll = struct.unpack_from('<f', payload, 8)[0]
            pitch = struct.unpack_from('<f', payload, 12)[0]
            heading = struct.unpack_from('<f', payload, 16)[0]
            att.append({'tow': tow, 'wnc': wnc,
                        'roll': roll, 'pitch': pitch, 'heading': heading})
        i += block_len
    return results, att


def analyze(results, utc=False):
    """Print a fix-quality summary and RTK drop events (fixed -> degraded)."""
    if not results:
        print('No PVT data to analyze')
        return
    total = len(results)
    counts = Counter(r['mode'] for r in results)
    order = ['RTK Fixed', 'RTK Float', 'Differential', 'Single', 'No GNSS']
    print('\nFix-quality summary (%d epochs):' % total)
    for m in order:
        c = counts.get(m, 0)
        if c:
            print('  %-12s %5d  (%5.1f%%)' % (m, c, 100.0 * c / total))
    other = sum(c for m, c in counts.items() if m not in order)
    if other:
        print('  %-12s %5d  (%5.1f%%)' % ('Other', other, 100.0 * other / total))

    def stamp(r):
        if utc:
            return gps_week_to_utc(r['wnc'], r['tow'])
        return 'tow=%d ms' % r['tow']

    # Drop event = a contiguous degraded run (mode != RTK Fixed) that follows a
    # fixed epoch. Track satellite counts at onset and the minimum during the run.
    events = []
    saw_fixed = False
    last_fixed_nrsv = None
    cur = None
    for r in results:
        if r['mode_id'] == 4:
            saw_fixed = True
            last_fixed_nrsv = r['nrsv']
            if cur is not None:
                cur['end_tow'] = r['tow']
                cur['end_stamp'] = stamp(r)
                cur['duration_s'] = (r['tow'] - cur['start_tow']) / 1000.0
                cur['recovered'] = True
                events.append(cur)
                cur = None
        else:
            if cur is None:
                if saw_fixed:
                    cur = {'start_tow': r['tow'], 'start_stamp': stamp(r),
                           'start_mode': r['mode'],
                           'onset_nrsv': last_fixed_nrsv,
                           'min_nrsv': r['nrsv'],
                           'duration_s': None, 'recovered': False}
            else:
                cur['min_nrsv'] = min(cur['min_nrsv'], r['nrsv'])
    if cur is not None:  # still degraded at end of log
        cur['duration_s'] = (results[-1]['tow'] - cur['start_tow']) / 1000.0
        events.append(cur)

    print('\nDrop events (RTK Fixed -> degraded):')
    if not events:
        if not saw_fixed:
            print('  (log never reached RTK Fixed)')
        else:
            print('  (none - held RTK Fixed for the whole log)')
        return
    for i, e in enumerate(events, 1):
        line = ('  #%d  %s: RTK Fixed -> %s for %.1f s'
                % (i, e['start_stamp'], e['start_mode'], e['duration_s']))
        if e['onset_nrsv'] is not None:
            line += '   (NrSV %s -> %d)' % (e['onset_nrsv'], e['min_nrsv'])
        if e['recovered']:
            line += ', recovered at %s' % e['end_stamp']
        else:
            line += ', STILL DEGRADED at end of log'
        print(line)


def export_csv(results, att, output, utc=False):
    if not results:
        print('No PVT data found!')
        return
    att_by_key = {(a['wnc'], a['tow']): a for a in att}
    fields = ['tow', 'wnc', 'mode', 'nrsv', 'lat', 'lon', 'height']
    if utc:
        fields.insert(1, 'utc')
    has_att = any((r['wnc'], r['tow']) in att_by_key for r in results)
    if has_att:
        fields += ['roll', 'pitch', 'heading']
    with open(output, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for r in results:
            row = dict(r)
            if utc:
                row['utc'] = gps_week_to_utc(r['wnc'], r['tow'])
            a = att_by_key.get((r['wnc'], r['tow']))
            if a:
                row.update(roll=a['roll'], pitch=a['pitch'], heading=a['heading'])
            writer.writerow(row)
    print('Exported %d records to %s' % (len(results), output))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Parse Septentrio SBF log files.')
    ap.add_argument('input', help='.sbf file to parse')
    ap.add_argument('--check-crc', action='store_true',
                    help='validate CRC-16/X25 on every block (recommended)')
    ap.add_argument('--utc', action='store_true',
                    help='add UTC timestamp column (GPS week + TOW, leap-second corrected)')
    ap.add_argument('--analyze', action='store_true',
                    help='print RTK drop report (fix-quality summary + drop events)')
    ap.add_argument('-o', '--output', default=None,
                    help='output CSV path (omit for console-only summary / analysis)')
    args = ap.parse_args()
    results, att = parse_sbf(args.input, check_crc=args.check_crc)
    if results:
        first = results[0]
        print('Parsed %d PVT records, %d attitude records' % (len(results), len(att)))
        print('First: Mode=%s, NrSV=%d, Lat=%.6f, Lon=%.6f, H=%.2f m'
              % (first['mode'], first['nrsv'], first['lat'], first['lon'], first['height']))
        if att:
            a0 = att[0]
            print('Attitude: Heading=%.2f deg, Roll=%.2f, Pitch=%.2f'
                  % (a0['heading'], a0['roll'], a0['pitch']))
        if args.analyze:
            analyze(results, utc=args.utc)
        if args.output:
            export_csv(results, att, args.output, utc=args.utc)
    else:
        print('No valid SBF data found')
        sys.exit(1)
