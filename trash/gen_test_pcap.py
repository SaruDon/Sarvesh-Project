from scapy.all import Ether, IP, TCP, UDP, wrpcap
import time

def generate_test_pcap(filename, count=100):
    pkts = []
    for i in range(count):
        # Alternate between TCP and UDP
        if i % 2 == 0:
            pkt = IP(src="192.168.10.5", dst="192.168.1.10")/TCP(sport=1234, dport=80, flags="S")
        else:
            pkt = IP(src="192.168.10.6", dst="192.168.1.11")/UDP(sport=5678, dport=53)
        
        # Add a mock arrival time
        pkt.time = time.time() + (i * 0.1)
        pkts.append(pkt)
    
    wrpcap(filename, pkts)
    print(f"Generated {count} packets in {filename}")

if __name__ == "__main__":
    generate_test_pcap("test_synthetic.pcap")
