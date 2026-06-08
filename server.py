import socket
import csv
import time
import os
from protocol import *

HOST = '127.0.0.1'
PORT = 8080
OUTPUT_FILE = 'received_file.dat'
LOG_FILE = 'server_log.csv'

def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    
    expected_seq_num = 0
    
    print(f"Sunucu {HOST}:{PORT} adresinde dinliyor...")
    
    with open(LOG_FILE, mode='w', newline='') as log_file, open(OUTPUT_FILE, 'wb') as out_file:
        log_writer = csv.writer(log_file)
        log_writer.writerow(['Timestamp', 'Event', 'SeqNum', 'Details'])
        
        start_time = time.time()
        received_packets_count = 0
        
        while True:
            packet_bytes, addr = sock.recvfrom(65535)
            pkt_type, seq_num, payload, is_valid = parse_packet(packet_bytes)
            
            if not is_valid:
                log_writer.writerow([time.time(), 'DROP_CORRUPT', seq_num if seq_num is not None else -1, 'Checksum failed'])
                continue
            
            if pkt_type == TYPE_DATA:
                if seq_num == expected_seq_num:
                    # In-order packet
                    out_file.write(payload)
                    log_writer.writerow([time.time(), 'RECV_DATA', seq_num, 'In-order'])
                    
                    # Send ACK for the received packet
                    ack_pkt = make_packet(TYPE_ACK, seq_num)
                    sock.sendto(ack_pkt, addr)
                    log_writer.writerow([time.time(), 'SEND_ACK', seq_num, ''])
                    
                    expected_seq_num += 1
                    received_packets_count += 1
                else:
                    # Out-of-order or duplicate packet
                    log_writer.writerow([time.time(), 'RECV_DUPLICATE_OR_OUT_OF_ORDER', seq_num, f'Expected {expected_seq_num}'])
                    # For Go-Back-N, we send an ACK for the last correctly received in-order packet (expected_seq_num - 1)
                    # If expected_seq_num is 0, we can just drop it or send an ACK with a special value like -1. 
                    # We'll just send ACK for expected_seq_num - 1.
                    last_acked = expected_seq_num - 1
                    if last_acked >= 0:
                        ack_pkt = make_packet(TYPE_ACK, last_acked)
                        sock.sendto(ack_pkt, addr)
                        log_writer.writerow([time.time(), 'SEND_ACK', last_acked, 'Duplicate/Out-of-order ACK'])
                    
            elif pkt_type == TYPE_FIN:
                log_writer.writerow([time.time(), 'RECV_FIN', seq_num, ''])
                # Send FIN_ACK
                fin_ack_pkt = make_packet(TYPE_FIN_ACK, seq_num)
                sock.sendto(fin_ack_pkt, addr)
                log_writer.writerow([time.time(), 'SEND_FIN_ACK', seq_num, ''])
                break

        total_time = time.time() - start_time
        print(f"Dosya alımı tamamlandı. Toplam {received_packets_count} paket alındı.")
        print(f"Alınan dosya: {OUTPUT_FILE}")
        
    sock.close()

if __name__ == '__main__':
    run_server()
