from socket import * 

server_name = 'localhost'
server_port = 12000

print("\n=== Server Side ====\n")
user2_name = input("Enter name for user2: ")

# Create server socket
server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind((server_name, server_port))

# Make server listen to incoming TCP requests
server_socket.listen(1)
print("\nServer is now listening to incoming TCP requests")

# Accept Connection
connection_socket, addr = server_socket.accept()
print(f"Server connected to client\n")


# Exchanging names
user1_name = connection_socket.recv(1024).decode()  # Recieve client user1 name 
print(f"Recieved user1 name ({user1_name}) from client")
connection_socket.send(user2_name.encode())         # Sending server user2 name to client 
print(f"Sent user2 name ({user2_name}) to client)\n")

print(f"user1 ({user1_name}) will send first message\n")

while True: 

    # Recieve message from Client 
    message_recieved = connection_socket.recv(1024).decode()
    print(f"({user1_name}) Message Recieved: {message_recieved}")

    if message_recieved.lower() == "bye": # Chat termination condition 
        print("Chat finished")
        connection_socket.close()
        print("Connection socket closed ")
        server_socket.close()
        print("Server socket closed ")
        break 


    # Send message to server
    message_to_send = input(f"({user2_name}) Message to Send: ")
    connection_socket.send(message_to_send.encode())
    print("Message sent \n")

    if message_to_send.lower() == "bye": # Chat termination condition 
        print("Chat finished")
        connection_socket.close()
        print("Connection socket closed ")
        server_socket.close()
        print("Server socket closed ")
        break 



