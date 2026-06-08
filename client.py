import socket
import csv
import time
import os
import random
import select
from protocol import *

HOST = '127.0.0.1'
PORT = 8080
import argparse

def run_client():
    parser = argparse.ArgumentParser(description="UDP RDT Client")
    parser.add_argument('--file', type=str, default='test_file.txt', help='Input file to send')
    parser.add_argument('--chunk', type=int, default=1024, help='Chunk size in bytes')
    parser.add_argument('--window', type=int, default=4, help='Window size')
    parser.add_argument('--timeout', type=float, default=0.5, help='Timeout in seconds')
    parser.add_argument('--retries', type=int, default=5, help='Max retries')
    parser.add_argument('--drop', type=float, default=0.0, help='Drop probability')
    args = parser.parse_args()

    INPUT_FILE = args.file
    CHUNK_SIZE = args.chunk
    WINDOW_SIZE = args.window
    TIMEOUT = args.timeout
    MAX_RETRIES = args.retries
    DROP_PROBABILITY = args.drop
    LOG_FILE = 'client_log.csv'


    if not os.path.exists(INPUT_FILE):
        print(f"Hata: {INPUT_FILE} bulunamadı.")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    
    # Read file and chunk it
    chunks = []
    with open(INPUT_FILE, 'rb') as f:
        while True:
            data = f.read(CHUNK_SIZE)
            if not data:
                break
            chunks.append(data)
            
    total_packets = len(chunks)
    print(f"Dosya okunuyor... Toplam {total_packets} paket gönderilecek.")
    
    base = 0
    next_seq_num = 0
    
    packet_info = {}
    
    start_time = time.time()
    total_sent = 0
    total_retransmissions = 0
    total_timeouts = 0
    
    with open(LOG_FILE, mode='w', newline='') as log_file:
        log_writer = csv.writer(log_file)
        log_writer.writerow(['Timestamp', 'Event', 'SeqNum', 'Details'])
        
        def send_pkt(seq):
            nonlocal total_sent
            pkt = make_packet(TYPE_DATA, seq, chunks[seq])
            
            # Simulate packet loss
            if random.random() < DROP_PROBABILITY:
                log_writer.writerow([time.time(), 'DROP_SIMULATED', seq, 'Simulated network drop'])
                total_sent += 1
                return
                
            try:
                sock.sendto(pkt, (HOST, PORT))
                log_writer.writerow([time.time(), 'SEND_DATA', seq, ''])
                total_sent += 1
            except Exception as e:
                pass
                
        while base < total_packets:
            # 1. Send packets if there is space in the window
            while next_seq_num < base + WINDOW_SIZE and next_seq_num < total_packets:
                send_pkt(next_seq_num)
                if next_seq_num not in packet_info:
                    packet_info[next_seq_num] = {'retries': 0}
                packet_info[next_seq_num]['time'] = time.time()
                next_seq_num += 1
                
            # 2. Check for incoming ACKs
            readable, _, _ = select.select([sock], [], [], 0.01)
            if readable:
                try:
                    packet_bytes, _ = sock.recvfrom(65535)
                    pkt_type, ack_num, _, is_valid = parse_packet(packet_bytes)
                    if is_valid and pkt_type == TYPE_ACK:
                        log_writer.writerow([time.time(), 'RECV_ACK', ack_num, ''])
                        # In GBN, ACK n acknowledges all packets up to and including n
                        if ack_num >= base:
                            base = ack_num + 1
                except BlockingIOError:
                    pass
                    
            # 3. Check for timeouts (GBN uses a single timer for the oldest unacked packet)
            if base < next_seq_num:
                if time.time() - packet_info[base]['time'] > TIMEOUT:
                    log_writer.writerow([time.time(), 'TIMEOUT', base, ''])
                    total_timeouts += 1
                    packet_info[base]['retries'] += 1
                    
                    if packet_info[base]['retries'] > MAX_RETRIES:
                        print(f"HATA: Paket {base} için maksimum retransmission limitine ({MAX_RETRIES}) ulaşıldı.")
                        log_writer.writerow([time.time(), 'ERROR_MAX_RETRIES', base, 'Aktarım iptal edildi'])
                        sock.close()
                        return
                    
                    # Retransmit ALL unacked packets in window
                    log_writer.writerow([time.time(), 'RETRANSMIT_WINDOW', base, f'Retransmitting {base} to {next_seq_num-1}'])
                    for seq in range(base, next_seq_num):
                        send_pkt(seq)
                        total_retransmissions += 1
                        packet_info[seq]['time'] = time.time()
        
        # 4. Teardown - Send FIN
        fin_pkt = make_packet(TYPE_FIN, next_seq_num)
        fin_retries = 0
        sock.setblocking(True)
        sock.settimeout(TIMEOUT)
        
        while fin_retries <= MAX_RETRIES:
            sock.sendto(fin_pkt, (HOST, PORT))
            log_writer.writerow([time.time(), 'SEND_FIN', next_seq_num, ''])
            try:
                packet_bytes, _ = sock.recvfrom(65535)
                pkt_type, ack_num, _, is_valid = parse_packet(packet_bytes)
                if is_valid and pkt_type == TYPE_FIN_ACK:
                    log_writer.writerow([time.time(), 'RECV_FIN_ACK', ack_num, ''])
                    break
            except socket.timeout:
                fin_retries += 1
                
        if fin_retries > MAX_RETRIES:
            print("FIN_ACK alınamadı, ancak aktarım tamamlandı kabul ediliyor.")
            
        end_time = time.time()
        print(f"Aktarım tamamlandı!")
        print(f"Toplam süre: {end_time - start_time:.2f} saniye")
        print(f"Toplam gönderilen paket (retransmission dahil): {total_sent}")
        print(f"Toplam timeout: {total_timeouts}, Toplam retransmission: {total_retransmissions}")

    sock.close()

if __name__ == '__main__':
    run_client()
