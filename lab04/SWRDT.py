import Network
import argparse
from time import sleep, time
import hashlib


class Segment:
    ## the number of bytes used to store segment length
    seq_num_S_length = 10
    length_S_length = 10
    ## length of md5 checksum in hex
    checksum_length = 32

    def __init__(self, seq_num, msg_S):
        self.seq_num = seq_num
        self.msg_S = msg_S

    @classmethod
    def from_byte_S(self, byte_S):
        if Segment.corrupt(byte_S):
            raise RuntimeError("Cannot initialize Segment: byte_S is corrupt")
        # extract the fields
        seq_num = int(
            byte_S[
                Segment.length_S_length : Segment.length_S_length
                + Segment.seq_num_S_length
            ]
        )
        msg_S = byte_S[
            Segment.length_S_length + Segment.seq_num_S_length + Segment.checksum_length :
        ]
        return self(seq_num, msg_S)

    def get_byte_S(self):
        # convert sequence number of a byte field of seq_num_S_length bytes
        seq_num_S = str(self.seq_num).zfill(self.seq_num_S_length)
        # convert length to a byte field of length_S_length bytes
        length_S = str(
            self.length_S_length
            + len(seq_num_S)
            + self.checksum_length
            + len(self.msg_S)
        ).zfill(self.length_S_length)
        # compute the checksum
        checksum = hashlib.md5((length_S + seq_num_S + self.msg_S).encode("utf-8"))
        checksum_S = checksum.hexdigest()
        # compile into a string
        return length_S + seq_num_S + checksum_S + self.msg_S

    @staticmethod
    def corrupt(byte_S):
        # extract the fields
        length_S = byte_S[0 : Segment.length_S_length]
        seq_num_S = byte_S[
            Segment.length_S_length : Segment.seq_num_S_length + Segment.seq_num_S_length
        ]
        checksum_S = byte_S[
            Segment.seq_num_S_length
            + Segment.seq_num_S_length : Segment.seq_num_S_length
            + Segment.length_S_length
            + Segment.checksum_length
        ]
        msg_S = byte_S[
            Segment.seq_num_S_length + Segment.seq_num_S_length + Segment.checksum_length :
        ]

        # compute the checksum locally
        checksum = hashlib.md5(str(length_S + seq_num_S + msg_S).encode("utf-8"))
        computed_checksum_S = checksum.hexdigest()
        # and check if the same
        return checksum_S != computed_checksum_S


class SWRDT:
    ## latest sequence number used in a segment
    seq_num = 1
    ## buffer of bytes read from network
    byte_buffer = ""

    expected_seq_num = 1
    sender_state = 'S_A'
    current_segment = None
    timeout_duration = 2

    def __init__(self, role_S, receiver_S, port):
        self.network = Network.NetworkLayer(role_S, receiver_S, port)
        self.role = role_S

    def disconnect(self):
        self.network.disconnect()



    def swrdt_send(self, msg_S):

        if self.role == "sender": 
            if self.sender_state == 'S_A':
                # Create and send segment with current sequence number
                self.current_segment = Segment(self.seq_num, msg_S)
                segment_bytes = self.current_segment.get_byte_S()
                self.network.network_send(segment_bytes)
                print(f"\nSend message {self.seq_num}")
                
                # Change state to waiting for ACK
                self.sender_state = 'S_B'
                self.send_time = time()
                
                return True
            
            # In S_B state, cannot send new message
            else: 
                return False
            
        # is Reciever sending ACK
        else: 
            ack_segment = Segment(msg_S, "")
            self.network.network_send(ack_segment.get_byte_S())
            return True
                


    def swrdt_receive(self):
        byte_S = self.network.network_receive()
        self.byte_buffer += byte_S
        
        if self.role == "receiver":
            return self._receiver_receive()
        else:
            return self._sender_receive()


    def _receiver_receive(self):

        # Check if we have enough bytes to read segment length
        if len(self.byte_buffer) < Segment.length_S_length:
            return None
            
        # Extract length of segment
        length = int(self.byte_buffer[:Segment.length_S_length])

        # Not enough bytes to read the whole segment
        if len(self.byte_buffer) < length:
            return None  
            
        segment_bytes = self.byte_buffer[:length]
        segment_data = self.byte_buffer[Segment.length_S_length:length]
        
        # remove the Segment bytes from the buffer
        self.byte_buffer = self.byte_buffer[length:]
        
        try:
            # Try to create segment from bytes
            segment = Segment.from_byte_S(segment_bytes)
            
            # Expected segment --> deliver to application
            if segment.seq_num == self.expected_seq_num:
                print(f"Receive message {segment.seq_num}. Send ACK {segment.seq_num}")
                self.swrdt_send(str(segment.seq_num))  # Send ACK
                self.expected_seq_num += 1
                return segment.msg_S
                            
            # Unexpected sequence number --> resend previous ACK
            else:
                print(f"Receive message {segment.seq_num}. Send ACK {self.expected_seq_num - 1}")
                self.swrdt_send(str(self.expected_seq_num - 1))
                return None

        # Segment is corrupted  
        except RuntimeError:
            print(f"Corruption detected! Send ACK {self.expected_seq_num - 1}")
            self.swrdt_send(str(self.expected_seq_num - 1))
            return None


    def _sender_receive(self):

        # Not waiting for ACK
        if self.sender_state != 'S_B':
            return None  
            
        # Check for timeout
        if time() - self.send_time > self.timeout_duration:
            print(f"Timeout! Resend message {self.seq_num}")
            self.network.network_send(self.current_segment.get_byte_S())
            self.send_time = time()
            return None
            
        # Check if we have enough bytes to read segment length
        if len(self.byte_buffer) < Segment.length_S_length:
            return None
            
        # Extract length of segment
        length = int(self.byte_buffer[:Segment.length_S_length])

        
        if len(self.byte_buffer) < length:
            return None  
            
        segment_bytes = self.byte_buffer[:length]
        
        # remove the Segment bytes from the buffer
        self.byte_buffer = self.byte_buffer[length:]
        
        try:
            # Try to create segment from bytes
            segment = Segment.from_byte_S(segment_bytes)
            
            # Valid ACK  recieved --> should have empty message and sequence number matching our expected ACK
            if segment.msg_S == "" and int(segment.seq_num) == self.seq_num:
                print(f"Receive ACK {segment.seq_num}. Message successfully sent!")
                self.seq_num += 1
                self.sender_state = 'S_A'
                self.current_segment = None
                return "ACK_RECEIVED"
            
            # Unexpected ACK sequence number
            else:
                print(f"Receive ACK {segment.seq_num}. Ignored")
                return None

        # ACK is corrupted  
        except RuntimeError:
            print(f"Corruption detected in ACK. Resend message {self.seq_num}")
            self.network.network_send(self.current_segment.get_byte_S())
            self.send_time = time()
            return None




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SWRDT implementation.")
    parser.add_argument(
        "role",
        help="Role is either sender or receiver.",
        choices=["sender", "receiver"],
    )
    parser.add_argument("receiver", help="receiver.")
    parser.add_argument("port", help="Port.", type=int)
    args = parser.parse_args()

    swrdt = SWRDT(args.role, args.receiver, args.port)
    if args.role == "sender":
        swrdt.swrdt_send("MSG_FROM_SENDER")
        sleep(2)
        print(swrdt.swrdt_receive())
        swrdt.disconnect()

    else:
        sleep(1)
        print(swrdt.swrdt_receive())
        swrdt.swrdt_send("MSG_FROM_RECEIVER")
        swrdt.disconnect()
