from socket import * 

server_name = 'localhost'
server_port = 12000

print("\n=== Client Side ====\n")
user1_name = input("Enter name for user1: ")

# Create cleint socket
client_socket = socket(AF_INET, SOCK_STREAM)

# Connect to server 
print(f"\nAttempting to conenct to server... ")
client_socket.connect((server_name, server_port))
print(f"Connected to server ({server_name}:{server_port})\n")


# Exchanging names
client_socket.send(user1_name.encode())         # Sending client user1 name to server 
print(f"Sent user1 name ({user1_name}) to server")
user2_name = client_socket.recv(1024).decode()  # Recieve server user2 name 
print(f"Recieved user2 name ({user2_name}) from server)\n")

print(f"user1 ({user1_name}) will send first message\n")

while True: 

    # Send message to server
    message_to_send = input(f"({user1_name}) Message to Send: ")
    client_socket.send(message_to_send.encode())
    print("Message sent \n")

    if message_to_send.lower() == "bye": # Chat termination condition 
        print("Chat finished")
        client_socket.close()
        print("Client socket closed ")
        break 


    # Recieve message from server 
    message_recieved = client_socket.recv(1024).decode()
    print(f"({user2_name}) Message Recieved: {message_recieved}")

    if message_recieved.lower() == "bye": # Chat termination condition 
        print("Chat finished")
        client_socket.close()
        print("Client socket closed ")
        break 

