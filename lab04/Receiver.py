import argparse
import SWRDT
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uppercase conversion receiver.")
    parser.add_argument("port", help="Port.", type=int)
    args = parser.parse_args()

    timeout = 10
    time_of_last_data = time.time()

    swrdt = SWRDT.SWRDT("receiver", None, args.port)
    
    
    while True:

        # try to receive message before timeout
        msg_S = swrdt.swrdt_receive()
        if msg_S is not None:
            time_of_last_data = time.time()
            print(f"Received and delivered to application: '{msg_S}'\n")

        if time_of_last_data + timeout < time.time():
            print("\nReceiver timeout - no data received for too long")
            break

    swrdt.disconnect()
    print("\n--- End ---")