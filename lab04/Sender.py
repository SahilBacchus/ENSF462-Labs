import argparse
import SWRDT
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Quotation sender talking to a receiver."
    )
    parser.add_argument("receiver", help="receiver.")
    parser.add_argument("port", help="Port.", type=int)
    args = parser.parse_args()

    msg_L = [
        "sending message - 1",
        "sending message - 2", 
        "sending message - 3",
        "sending message - 4",
        "sending message - 5",
        "sending message - 6",
        "sending message - 7",
        "sending message - 8",
        "sending message - 9",
        "sending message - 10",
    ]

    swrdt = SWRDT.SWRDT("sender", args.receiver, args.port)
    
    for msg_S in msg_L:
        
        # Send message (will only work if in S_A state)
        if swrdt.swrdt_send(msg_S):

            # Wait for ACK
            ack_received = False
            while not ack_received:
                result = swrdt.swrdt_receive()
                if result == "ACK_RECEIVED":
                    ack_received = True

                
                time.sleep(0.1)
        else:
            print("Cannot send message - waiting for previous ACK")

            # Wait until we can send again
            while swrdt.sender_state != 'S_A':
                swrdt.swrdt_receive()
                time.sleep(0.1)

            # Retry sending
            swrdt.swrdt_send(msg_S)

    swrdt.disconnect()
    print("\n--- End ---")