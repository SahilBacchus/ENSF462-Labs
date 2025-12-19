from socket import *
import time
import datetime



print("\n=== UDP Pinger Client ===\n")

server_name = '192.168.1.86'   # ip of device running UDPPingerServer --> another laptop on same local network
# server_name = 'iocalhost'  
server_port = 12000

# Create client socket
client_socket = socket(AF_INET, SOCK_DGRAM)
client_socket.settimeout(1.0) # Sets timeout to be 1.0 seconds --> assumes packet was lost if not recieved in this time
print(f"Pinging server ({server_name}:{server_port})\n")


rtt_times = []
packets_lost = 0
packets_sent = 10

for sequence_number in range(1, packets_sent + 1):
    
    # Create ping message
    send_time = datetime.datetime.now() # Get current time
    ping_message = f"Ping {sequence_number} {send_time}"
    
    try:
        # Send message to server
        client_socket.sendto(ping_message.encode(), (server_name, server_port))
        print(f"Sent ping #{sequence_number} to server")
        
        # Receive response from server
        response, server_address = client_socket.recvfrom(1024)
        receive_time = datetime.datetime.now()
        
        # Calculate RTT
        rtt = (receive_time - send_time).total_seconds()
        rtt_times.append(rtt)
        
        print(f"Received response from server: {response.decode()}")
        print(f"RTT: {rtt} s\n")
        


    except timeout: # Handle timeout case
        packets_lost += 1
        print("Request timed out\n")
    

    # Wait 1 second before next ping
    time.sleep(1)



# Close client socket
client_socket.close()
print("Client socket closed\n")



# Print statistics
print("=== Ping Statistics ===")

min_rtt = min(rtt_times)
max_rtt = max(rtt_times)
avg_rtt = sum(rtt_times) / len(rtt_times)

print(f"Minimum RTT: {min_rtt} s")
print(f"Maximum RTT: {max_rtt} s")
print(f"Average RTT: {avg_rtt} s\n")

pkt_loss_rate = (packets_lost / packets_sent) * 100

print(f"Packet loss rate: {pkt_loss_rate}%")



