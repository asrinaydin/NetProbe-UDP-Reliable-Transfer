import subprocess
import time
import os
import matplotlib.pyplot as plt
from analyzer import analyze

def create_random_file(filename, size_bytes):
    print(f"[{filename}] {size_bytes} byte boyutunda test dosyasi olusturuluyor...")
    with open(filename, 'wb') as f:
        f.write(os.urandom(size_bytes))


def run_experiment(name, client_args):
    print(f"\n--- DENEY BAŞLIYOR: {name} ---")
    
    # 1. Start Server
    server_process = subprocess.Popen(['python', 'server.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1) # wait for server to bind
    
    # 2. Start Client
    client_cmd = ['python', 'client.py'] + client_args
    print(f"İstemci çalıştırılıyor: {' '.join(client_cmd)}")
    subprocess.run(client_cmd)
    
    # 3. Wait for logs to be flushed
    time.sleep(1)
    
    # 4. Run Analysis
    metrics = analyze('client_log.csv', 'server_log.csv')
    
    # 5. Stop Server (if not already stopped by FIN)
    server_process.terminate()
    server_process.wait()
    
    return metrics

def plot_results(results_dict, metric_name, title, ylabel, filename):
    names = list(results_dict.keys())
    values = [results_dict[n][metric_name] for n in names]
    
    plt.figure(figsize=(10, 6))
    plt.bar(names, values, color='skyblue')
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename)
    print(f"Grafik kaydedildi: {filename}")

if __name__ == '__main__':
    # Prepare files
    create_random_file('test_100k.txt', 100 * 1024)
    create_random_file('test_1m.txt', 1024 * 1024)
    
    results_scenario_1 = {}
    results_scenario_2 = {}
    results_scenario_3 = {}
    
    # Senaryo 1: Paket Boyutunun Etkisi
    for size in [512, 1024, 2048, 4096]:
        metrics = run_experiment(f"Paket Boyutu {size} B", ['--file', 'test_1m.txt', '--chunk', str(size)])
        if metrics:
            results_scenario_1[f"{size} B"] = metrics
            
    # Senaryo 2: Timeout Etkisi
    for to in [0.05, 0.1, 0.5, 1.0]:
        metrics = run_experiment(f"Timeout {to} s", ['--file', 'test_1m.txt', '--timeout', str(to), '--drop', '0.05'])
        if metrics:
            results_scenario_2[f"{to} s"] = metrics
            
    # Senaryo 3: Kayıp Oranı Etkisi
    for drop in [0.0, 0.05, 0.1, 0.2]:
        metrics = run_experiment(f"Kayıp %{int(drop*100)}", ['--file', 'test_100k.txt', '--drop', str(drop)])
        if metrics:
            results_scenario_3[f"%{int(drop*100)}"] = metrics

    # Grafikleri Çiz
    if results_scenario_1:
        plot_results(results_scenario_1, 'Throughput', 'Senaryo 1: Paket Boyutunun Throughput Etkisi', 'Throughput (Bytes/s)', 'grafik_senaryo1.png')
    if results_scenario_2:
        plot_results(results_scenario_2, 'CompletionTime', 'Senaryo 2: Timeout Değerinin Tamamlanma Süresine Etkisi', 'Süre (s)', 'grafik_senaryo2.png')
    if results_scenario_3:
        plot_results(results_scenario_3, 'RetransmissionRate', 'Senaryo 3: Kayıp Oranının Retransmission Oranına Etkisi', 'Retransmission Rate', 'grafik_senaryo3.png')

    print("\nTüm deneyler tamamlandı. Grafikler oluşturuldu.")
