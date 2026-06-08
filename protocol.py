import struct
import hashlib

# Packet Types
TYPE_DATA = 0
TYPE_ACK = 1
TYPE_FIN = 2
TYPE_FIN_ACK = 3

# Header Format:
# Type (1 byte) + SeqNum (4 bytes) + PayloadLen (2 bytes) + Checksum (16 bytes)
# Total: 23 bytes
HEADER_FORMAT = '!B I H 16s'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

def compute_checksum(payload: bytes) -> bytes:
    """Computes MD5 hash of the payload."""
    return hashlib.md5(payload).digest()

def make_packet(pkt_type: int, seq_num: int, payload: bytes = b'') -> bytes:
    """
    Creates a packet with header and payload.
    """
    payload_len = len(payload)
    checksum = compute_checksum(payload)
    header = struct.pack(HEADER_FORMAT, pkt_type, seq_num, payload_len, checksum)
    return header + payload

def parse_packet(packet_bytes: bytes):
    """
    Parses a packet, verifies checksum.
    Returns (pkt_type, seq_num, payload, is_valid)
    """
    if len(packet_bytes) < HEADER_SIZE:
        return None, None, None, False
    
    header = packet_bytes[:HEADER_SIZE]
    payload = packet_bytes[HEADER_SIZE:]
    
    pkt_type, seq_num, payload_len, checksum = struct.unpack(HEADER_FORMAT, header)
    
    # Extract exact payload according to length (useful if there's padding, though UDP handles boundaries)
    payload = payload[:payload_len]
    
    expected_checksum = compute_checksum(payload)
    is_valid = (checksum == expected_checksum)
    
    return pkt_type, seq_num, payload, is_valid
