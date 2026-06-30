"""TD6 and TD7 track design binary file parser."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

# Track type IDs that represent station pieces in TD6 binary data.
# Corresponds to TrackElemType: FLAT(1), STATION(2), END_STATION(3).
_STATION_TRACK_TYPES = frozenset({1, 2, 3})

# TD6 scenery type code → (bridge object type, identifier prefix)
_SCENERY_TYPE_MAP: dict[int, tuple[str, str]] = {
    1: ("small_scenery", "rct2.scenery_small"),
    2: ("large_scenery", "rct2.scenery_large"),
    3: ("wall", "rct2.wall"),
}


def decompress_rle(data: bytes) -> bytes:
    """Decompress PackBits RLE data from an RCT2 file chunk.
    
    The last 4 bytes of RCT2 RLE files are a checksum and are ignored.
    """
    compressed = data[:-4]
    decompressed = bytearray()
    
    i = 0
    while i < len(compressed):
        b = compressed[i]
        i += 1
        
        # Convert unsigned byte to signed 8-bit integer
        signed_b = b - 256 if b >= 128 else b
        
        if signed_b >= 0:
            # Literal run: copy next signed_b + 1 bytes directly
            count = signed_b + 1
            decompressed.extend(compressed[i : i + count])
            i += count
        else:
            # Repeat run: copy the next byte (1 - signed_b) times
            count = 1 - signed_b
            val = compressed[i]
            i += 1
            decompressed.extend([val] * count)
            
    return bytes(decompressed)


@dataclass(frozen=True)
class TrackPiece:
    """A single track segment parsed from a prebuilt design file."""
    track_type: int
    qualifier: int
    is_lift_hill: bool
    is_tunnel: bool
    brake_speed: int


@dataclass(frozen=True)
class DecodedScenery:
    """A decoration/scenery item parsed from a prebuilt design file."""
    scenery_type: int
    version: int
    dat_name: str
    x: int
    y: int
    z: int
    direction: int
    quadrant: int
    primary_colour: int
    secondary_colour: int


@dataclass(frozen=True)
class DecodedRideDesign:
    """Decoded metadata and track pieces from a prebuilt ride file."""
    ride_type: int
    vehicle_index: int
    vehicle_name: str
    station_length: int
    pieces: list[TrackPiece]
    decorations: list[DecodedScenery]


class TD6Parser:
    """Parser for RollerCoaster Tycoon 2 .TD6 prebuilt ride files."""

    @classmethod
    def parse_file(cls, filepath: str | Path) -> DecodedRideDesign:
        """Read and parse a .TD6 design file from a path."""
        p = Path(filepath)
        if not p.exists():
            raise FileNotFoundError(f"Track design file not found: {p}")
        return cls.parse(p.read_bytes())

    @classmethod
    def parse(cls, data: bytes) -> DecodedRideDesign:
        """Parse raw RLE-compressed TD6 bytes."""
        decompressed = decompress_rle(data)
        
        # Minimum valid uncompressed size for TD6 is 19,235 bytes
        if len(decompressed) < 19235:
            raise ValueError(
                f"Invalid decompressed TD6 file size: {len(decompressed)} bytes (expected >= 19235)"
            )
            
        # Header Offsets (0x00 - 0xA2)
        # Offset 0x00: Ride/Track Type
        ride_type = decompressed[0]
        # Offset 0x01: Vehicle Object Index / Type
        vehicle_index = decompressed[1]
        
        # Offset 0x74 (116): Vehicle Object Name (8-character ASCII, space-padded)
        vehicle_name = decompressed[0x74:0x74 + 8].decode("ascii", errors="ignore").strip()
        
        # Track Pieces Segment (Offset 0xA3 onwards)
        pieces = []
        offset = 0xA3
        
        while offset < len(decompressed):
            track_type = decompressed[offset]
            if track_type == 0xFF:
                break
                
            qualifier = decompressed[offset + 1]
            offset += 2
            
            is_lift_hill = bool(qualifier & 0x80)
            is_tunnel = bool(qualifier & 0x02)
            # Brakes speed limit is stored in bits 3-6 of the qualifier byte
            brake_speed = (qualifier >> 3) & 0x0F
            
            pieces.append(TrackPiece(
                track_type=track_type,
                qualifier=qualifier,
                is_lift_hill=is_lift_hill,
                is_tunnel=is_tunnel,
                brake_speed=brake_speed,
            ))

        # Skip the track terminator byte (0xFF)
        offset += 1

        # Parse entrance/exit structures (6 bytes each), terminated by 0xFF.
        # Mazes (ride_type == 20) use a 4-byte spacer instead.
        if ride_type == 20:
            offset += 4
        else:
            while offset < len(decompressed) and decompressed[offset] != 0xFF:
                offset += 6
            offset += 1

        # Parse scenery structures (22 bytes each), terminated by 0xFF.
        decorations = []
        while offset + 22 <= len(decompressed) and decompressed[offset] != 0xFF:
            sc_bytes = decompressed[offset : offset + 22]
            offset += 22
            flag = sc_bytes[0]
            decorations.append(DecodedScenery(
                scenery_type=flag & 0x0F,
                version=(flag >> 4) & 0x0F,
                dat_name=sc_bytes[4:12].decode("ascii", errors="ignore").strip(),
                x=sc_bytes[16],
                y=sc_bytes[17],
                z=sc_bytes[18],
                direction=sc_bytes[19] & 0x03,
                quadrant=(sc_bytes[19] >> 2) & 0x03,
                primary_colour=sc_bytes[20],
                secondary_colour=sc_bytes[21],
            ))

        # Count contiguous station pieces at the very start
        station_length = 0
        for p in pieces:
            if p.track_type in _STATION_TRACK_TYPES:
                station_length += 1
            else:
                break
            
        return DecodedRideDesign(
            ride_type=ride_type,
            vehicle_index=vehicle_index,
            vehicle_name=vehicle_name,
            station_length=station_length,
            pieces=pieces,
            decorations=decorations,
        )
