import argparse
import socket
import threading

SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 5378
TIMEOUT = .1
current_users = []



def receive(sock):
    '''
    Receives data in chunks of 1024 bytes. Parses multiple messages into a list of messages
    sock: socket object
    Returns: string[], list of responses from client
    '''
    responses = []
    sock.settimeout(TIMEOUT)
    cut_off_message = ""
    
    while True:
        try:
            data = sock.recv(1024)
        except socket.timeout:
            return responses
        
        if not data:
            break
        
        data = data.decode("utf-8")
        if cut_off_message:
            # message was cut off in last chunk
            if data[-1] == "\n":
                # this whole chunk is the rest of the message
                responses.append(cut_off_message + data)
                cut_off_message = ""
                continue
            
            elif "\n" in data:
                # end of the message is in this chunk, along with another message
                cut_off_message += data[: data.index("\n")]
                responses.append(cut_off_message)
                
                # make data not include the cut off message part
                data = data[data.index("\n")+1: ]
                cut_off_message = ""
            
            else:
                # full message has not been received yet
                cut_off_message += data
                continue
        
        if data[-1] == "\n":
            # this means no cut off messages
            responses.extend(data.split("\n")[: -1])
        
        elif "\n" in data:
            # this means a message was cut off after a message
            messages = data.split("\n")
            responses.extend(messages[:-1])
            cut_off_message = messages[-1]
        
        else:
            # no newline characters at all means message is cut off
            cut_off_message = data


    return responses



# Taken from threading tutorial in lab manual
def send(sock, string):
    '''
    sock: socket object
    string: message to be sent
    Send message string to server using socket "sock"
    '''
    string_bytes = string.encode("utf-8")
    
    # send string to server
    bytes_len = len(string_bytes)
    num_bytes_to_send = bytes_len
    while num_bytes_to_send > 0:
        # Sometimes, the operating system cannot send everything immediately.
        # For example, the sending buffer may be full.
        # send returns the number of bytes that were sent.
        num_bytes_to_send -= sock.send(string_bytes[bytes_len-num_bytes_to_send:])


# for deliveries, we need to either just send to other client from the current thread (will have to store client sockets in global var), or
# let threads communicate with each other and send a command to other thread to send message to the desired user. Problem with first is if two threads send to user at same time maybe.
# need a way to confirm that message was sent to confirm with sender.
# always check that the current client is logged in first
def handle_client(sock, address):
    logged_in = False

    while True:
        # blocks until response from client heard
        responses = []
        while not responses:
            try:
                responses = receive(sock)
            except:
                pass

        for response in responses:
            



def main():
    # create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_ADDRESS, SERVER_PORT))

    # start listening for incoming connections
    server_socket.listen()
    print("Server is on")

    # start server loop
    while True:
        # Accept incoming connection
        client_socket, client_address = server_socket.accept()

        # Create a new thread to handle the client connection
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()



if __name__ == "__main__":
    
    # Add optional arguments
    parser = argparse.ArgumentParser(description="Run server using sockets")
    parser.add_argument('--address', type=str, help='Address of server', nargs='?')
    parser.add_argument('--port', type=int, help='Listening port', nargs='?')

    # Assign arguments to global vars
    args = parser.parse_args()
    if args.address:
        SERVER_ADDRESS = args.address
    if args.port:
        SERVER_PORT = args.port
    
    main()