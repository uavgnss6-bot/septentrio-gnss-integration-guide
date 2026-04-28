#!/usr/bin/env python3
"""
Septentrio SBF (Septentrio Binary Format) Parser
Extracts position, velocity, and fix quality from SBF log files.

Usage:
    python sbf-parser.py input.sbf

Output:
    CSV file with timestamp, lat, lon, height, and fix mode
"""

import struct, sys, csv

BLOCK_ID_PVT = 4028  # PVTGeodetic block

def parse_sbf(filename):
    """Parse SBF file and extract PVT data."""
    results = []
    with open(filename, 'rb') as f:
        while True:
            header = f.read(8)
            if len(header) < 8:
                break
            sync, crc, block_id, block_len = struct.unpack('<HHIH', header[:8])
            if sync != 0xFAFA:
                continue
            data = f.read(block_len - 8)
            if len(data) < block_len - 8:
                break
            if block_id == BLOCK_ID_PVT:
                tow = struct.unpack('<I', data[0:4])[0]
                mode = struct.unpack('<B', data[8:9])[0]
                lat = struct.unpack('<d', data[40:48])[0]
                lon = struct.unpack('<d', data[48:56])[0]
                height = struct.unpack('<d', data[64:72])[0]
                mode_map = {0: 'No GNSS', 1: 'Single', 2: 'Differential',
                           3: 'RTK Float', 4: 'RTK Fixed'}
                results.append({
                    'tow': tow,
                    'mode': mode_map.get(mode, f'Unknown({mode})'),
                    'lat': lat,
                    'lon': lon,
                    'height': height
                })
    return results

def export_csv(results, output='sbf_output.csv'):
    if not results:
        print('No data found!')
        return
    with open(output, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['tow', 'mode', 'lat', 'lon', 'height'])
        writer.writeheader()
        writer.writerows(results)
    print(f'Exported {len(results)} records to {output}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python sbf-parser.py <sbf_file>')
        sys.exit(1)
    data = parse_sbf(sys.argv[1])
    if data:
        print(f'Parsed {len(data)} records')
        print(f'First: Mode={data[0]["mode"]}, Lat={data[0]["lat"]:.6f}, Lon={data[0]["lon"]:.6f}')
        export_csv(data)
    else:
        print('No valid SBF data found')
