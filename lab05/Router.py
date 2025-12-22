import sys
import socket
import threading
import time
import json

# Global Constants
INFINITY = 999
UPDATE_INTERVAL = 1.0           # Time in seconds to send link states 
ROUTE_UPDATE_INTERVAL = 10.0    # Time in seconds to send paths
HOST = 'localhost'  

class Router:
    def __init__(self, router_id, port, config_file):
        self.id = int(router_id)
        self.port = int(port)
        self.config_file = config_file
        
        # State variables
        self.neighbors = {} # {neighbor_id: {'cost', 'port', 'label'}}
        self.total_nodes = 0
        self.link_state = {} # {node_id: [cost_vector]} 
        self.labels = {}
        self.ids = {}  
        
        # Socket setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((HOST, self.port))
        
        # Intialize 
        self.load_config()        
        self.update_own_link_state()

    def load_config(self):
        """
        Reads the configuration file to setup neighbors and total nodes.
        """
        try:
            with open(self.config_file, 'r') as f:
                lines = f.readlines()
                
                # <Total number of nodes> (first line)
                self.total_nodes = int(lines[0].strip())
                
                # Initialize label mappings (A=0, B=1, etc.)
                for i in range(self.total_nodes):
                    label = chr(ord('A') + i)
                    self.labels[i] = label
                    self.ids[label] = i
                
                # Parse neighbors
                for line in lines[1:]:
                    parts = line.strip().split()
                    if not parts: continue
                    # <neighbor node label> <space> <neighbor node id> <space> <link cost> <space> <neighbor node port number> (a line per neighbor)
                    n_label, n_id, n_cost, n_port = parts[0], int(parts[1]), int(parts[2]), int(parts[3])
                    self.neighbors[n_id] = {
                        'cost': n_cost,
                        'port': n_port,
                        'label': n_label
                    }
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)


    def update_own_link_state(self):
        """
        Constructs the link state vector for this router.
        """
        vector = []
        for i in range(self.total_nodes):
            if i == self.id:
                vector.append(0) # Cost to self is 0
            elif i in self.neighbors:
                vector.append(self.neighbors[i]['cost'])
            else:
                vector.append(INFINITY) # Non-neighbors are ininite cost
        self.link_state[self.id] = vector


    def send_link_state(self):
        """
        Thread 1: Broadcasts own Link State to direct neighbors every second.
        """
        while True:
            # Create packet
            packet = {
                'type': 'LSP',
                'sender_id': self.id,      
                'origin_id': self.id,     
                'link_vector': self.link_state[self.id],
                'ttl': self.total_nodes    # Use Counter for broadcast limiting 
            }
            
            data = json.dumps(packet).encode('utf-8')
            
            # Send to all direct neighbors
            for n_id, info in self.neighbors.items():
                try:
                    self.sock.sendto(data, (HOST, info['port']))
                except Exception as e:
                    print(f"Error sending link state: {e}")
            
            time.sleep(UPDATE_INTERVAL)

    def receive_link_state(self):
        """
        Thread 2: Receives UDP packets, updates link_states, and forwards valid packets.
        """
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                packet = json.loads(data.decode('utf-8'))
                
                origin = packet['origin_id']
                vector = packet['link_vector']
                ttl = packet['ttl']
                
                current_vector = self.link_state.get(origin)
                self.link_state[origin] = vector
                
                # Decrement TTL (counter)
                packet['ttl'] -= 1
                
                if packet['ttl'] > 0 and self.id != origin:
                    packet['sender_id'] = self.id # Update sender to self for next hop
                    forward_data = json.dumps(packet).encode('utf-8')
                    
                    for n_id, info in self.neighbors.items():
                        self.sock.sendto(forward_data, (HOST, info['port']))
                        
            except Exception as e:
                print(f"Receive error: {e}")

    def compute_routing(self):
        """
        Thread 3: Runs Dijkstra and builds Forwarding Table every 10 seconds.
        """
        while True:
            time.sleep(ROUTE_UPDATE_INTERVAL)
            
            # Check if we have the whole network topology 
            if len(self.link_state) < self.total_nodes:
                continue

            # Run dijkstra
            dist, prev = self.dijkstra_algorithm()
            
            # print dijkstra results
            print("================================================")
            print(f"Router {self.labels[self.id]}")
            print("------------------------------------------------")
            print(f"Dijkstra results: ")
            print(f"{'Destination Routerid':<20} | {'Distance':<10} | {'Previous node id':<15}")
            print("------------------------------------------------")
            
            for i in range(self.total_nodes):
                d = dist[i]
                p = prev[i] if prev[i] is not None else -1
                if i == self.id:
                    p = self.id 
                print(f"{i:<20} | {d:<10} | {p:<15}")

            # Build and print forwarding tablel
            print("------------------------------------------------")
            print(f"The forwarding table in {self.labels[self.id]} is printed as follows:")
            print(f"{'Destination Routerid':<20} | {'Next hop routerlabel':<20}")
            print("------------------------------------------------")
            
            for dest_id in range(self.total_nodes):
                if dest_id == self.id: # Skip self
                    continue 
                
                next_hop_label = self.get_next_hop(dest_id, prev)
                print(f"{dest_id:<20} | {next_hop_label:<20}")
            print("================================================")
            print("\n\n") 

    def dijkstra_algorithm(self):
            """
            implement  Dijkstra's link-state routing algorithm.
            """
            # u: Source node
            u = self.id
            
            # N' (visited set)
            visited = set()
            visited.add(u)
            
            # Initialization
            dist = {}  # D(v) --> current estimate of cost of least-cost-path from u to v
            prev = {} # p(v) --> predecessor node along path from u to v
            
            # Initialize D(v) = c(u,v) or infinity
            source_vector = self.link_state[u]
            for v in range(self.total_nodes):
                dist[v] = source_vector[v]
                if v != u and dist[v] != INFINITY:
                    prev[v] = u # If v is a direct neighbor, p(v) is u
                else:
                    prev[v] = None
            
            prev[u] = u # Self points to self
            
            # Loop until all nodes are in N' (visited)
            while len(visited) < self.total_nodes:
                # Find w not in N' such that D(w) is min
                min_dist = INFINITY + 1
                w = -1 # Node chosen for addition to N'
                
                for node in range(self.total_nodes):
                    if node not in visited:
                        if dist[node] < min_dist:
                            min_dist = dist[node]
                            w = node
                
                if w == -1 or min_dist == INFINITY:
                    break 
                    
                visited.add(w) # Add w to N'
                
                # Update D(v) for all v not in N' 
                if w in self.link_state:
                    w_vector = self.link_state[w]
                    for v in range(self.total_nodes):
                        if v not in visited:
                            # c(w,v) --> Cost from w to v
                            cost_w_v = w_vector[v]
                            
                            # D(v) = min(D(v), D(w) + c(w,v))
                            new_cost = dist[w] + cost_w_v
                            if new_cost < dist[v]:
                                dist[v] = new_cost
                                prev[v] = w
                                
            return dist, prev

    def get_next_hop(self, dest_id, prev):
        """
        Determines the first hop neighbor on the least cost path.
        """
        if prev[dest_id] is None:
            return "None"
        
        # backtrack from destination until we find the node whose previous is src
        curr = dest_id
        
        # If the destination is a direct neighbor and the previous node is us --> it is the next hop
        if prev[curr] == self.id:
            return self.labels[curr]
            
        # otherwise backtrack
        count = 0 
        while prev[curr] != self.id and count < self.total_nodes:
            curr = prev[curr]
            count += 1
            
        return self.labels[curr]

    def run(self):
        """
        Initializes and starts all threads. 
        """
        t1 = threading.Thread(target=self.send_link_state, daemon=True)
        t2 = threading.Thread(target=self.receive_link_state, daemon=True)
        t3 = threading.Thread(target=self.compute_routing, daemon=True)
        
        t1.start()
        t2.start()
        t3.start()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Router stopping...")




def main(): 
    if len(sys.argv) != 4:
        print("Usage: python Router.py <routerid> <routerport> <configfile>")
        sys.exit(1)
        
    r_id = sys.argv[1]
    r_port = sys.argv[2]
    config = sys.argv[3]
    
    router = Router(r_id, r_port, config)
    router.run()


if __name__ == "__main__":
    main()
