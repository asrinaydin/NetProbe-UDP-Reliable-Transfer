import pandas as pd
import sys
import os

def analyze(client_log_file, server_log_file, packet_size=1024, header_size=23):
    if not os.path.exists(client_log_file):
        print(f"Hata: {client_log_file} bulunamadı.")
        return None
        
    try:
        df_client = pd.read_csv(client_log_file)
        
        # Calculate times
        start_time = df_client['Timestamp'].min()
        end_time = df_client['Timestamp'].max()
        total_time = end_time - start_time
        
        if total_time == 0:
            total_time = 0.0001 # prevent div by zero
            
        # Count events
        sends = df_client[df_client['Event'] == 'SEND_DATA']
        retransmits = df_client[df_client['Event'] == 'RETRANSMIT_WINDOW'] # this event marks the timeout, but actual sends are logged as SEND_DATA. Wait, if it's sent again, it's just SEND_DATA.
        # Actually, if we just count all SEND_DATA, that's total_sent.
        # Unique seq numbers sent is the number of actual packets.
        total_sent = len(sends)
        unique_packets = sends['SeqNum'].nunique()
        retransmissions = total_sent - unique_packets
        
        # In client.py, drops are logged as DROP_SIMULATED but we also incremented total_sent in the script, though it didn't hit the socket. Let's count SEND_DATA + DROP_SIMULATED.
        drops = len(df_client[df_client['Event'] == 'DROP_SIMULATED'])
        total_attempts = total_sent + drops
        retransmissions = total_attempts - unique_packets
        
        # Calculate sizes
        total_bytes_sent = total_attempts * (packet_size + header_size)
        good_bytes_sent = unique_packets * packet_size
        
        throughput = total_bytes_sent / total_time # Bytes/sec
        goodput = good_bytes_sent / total_time     # Bytes/sec
        retransmission_rate = retransmissions / total_attempts if total_attempts > 0 else 0
        
        metrics = {
            'CompletionTime': total_time,
            'Throughput': throughput,
            'Goodput': goodput,
            'RetransmissionRate': retransmission_rate,
            'TotalAttempts': total_attempts,
            'UniquePackets': unique_packets
        }
        
        return metrics
        
    except Exception as e:
        print(f"Analiz sırasında hata oluştu: {e}")
        return None

if __name__ == '__main__':
    metrics = analyze('client_log.csv', 'server_log.csv')
    if metrics:
        print("--- PERFORMANS METRİKLERİ ---")
        print(f"Tamamlanma Süresi: {metrics['CompletionTime']:.3f} saniye")
        print(f"Throughput: {metrics['Throughput']/1024:.2f} KB/s")
        print(f"Goodput: {metrics['Goodput']/1024:.2f} KB/s")
        print(f"Retransmission Oranı: {metrics['RetransmissionRate']*100:.2f}%")
        print(f"Toplam Deneme: {metrics['TotalAttempts']}, Eşsiz Paket: {metrics['UniquePackets']}")
