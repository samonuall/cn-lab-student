import argparse
import socket
import re
import threading

SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 5389
TIMEOUT = .1
usernames = {"echobot": None} # {username: socket}
clients_lock = threading.Lock()

def receiveLogic(client):
    client_name = ""
    
    while True:
        messages = receive(client)
        
        if not messages:
            # client has closed the connection
            with clients_lock:
                del usernames[client_name]
            return
        
        with clients_lock:
            for message in messages:
                if 'HELLO-FROM' in message:
                    name = message[11:]
                    
                    if client not in usernames.values(): # socket not logged in yet

                        if len(usernames) == 17: # server is full
                            send(client, "BUSY\n")
                        
                        elif name in usernames:
                            send(client, "IN-USE\n")
                            client.close()
                            return
                        
                        elif re.search(r'[^a-zA-Z0-9]', name): #invalid username
                            send(client, 'BAD-RQST-BODY\n')
                        
                        else: #succesful login
                            usernames[name] = client
                            client_name = name
                            send(client, f"HELLO {name}\n")

                    else: # socket is already logged in
                        send(client, 'BAD-RQST-HDR\n')

                elif not client_name: # user tried to do something without being logged in
                    send(client, 'BAD-RQST-HDR\n')
                    client.close()
                    return

                elif message.startswith('LIST'):
                    str = 'LIST-OK '

                    for username in usernames.keys():
                        str +=  f"{username},"
                    str += '\n'
                    send(client, str)

                elif message.startswith('SEND'):
                    index = message.index(" ")
                    username = message[index+1: message.index(" ", index+1)]
                    mess = message[message.index(" ", index+1)+1: ]
                    
                    if username in usernames:
                        if username == "echobot":
                            rec_sock = client
                            sender_name = "echobot"
                        else:
                            rec_sock = usernames[username]
                            sender_name = client_name
                        
                        try:
                            send(rec_sock, f"DELIVERY {sender_name} {mess}\n")
                            send_success = True
                        except:
                            send_success = False
                        
                        if send_success:
                            send(client, 'SEND-OK\n')
                    
                    else:
                        send(client, 'BAD-DEST-USER\n')


def receive(sock):
    '''
    Receives data in chunks of 1024 bytes. Parses multiple messages into a list of messages
    sock: socket object
    Returns: string[], list of responses from client
    '''
    responses = []
    cut_off_message = ""
    
    while True:
        try:
            data = sock.recv(1024)
        except Exception as e:
            print("Error:", e)
            return []
        
        if not data:
            return []
        
        data = data.decode("utf-8")
        if cut_off_message:
            # message was cut off in last chunk
            if data[-1] == "\n":
                # this whole chunk is the rest of the message
                responses.append(cut_off_message + data)
                cut_off_message = ""
                return responses
            
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
            return responses
        
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
            


def main():
    # create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_ADDRESS, SERVER_PORT))

    # start listening for incoming connections
    server_socket.listen()
    print("Server is on")
    
    # start server loop
    while True:
        client_socket, _ = server_socket.accept()
        new_thread = threading.Thread(target=receiveLogic, args=(client_socket,), daemon=True)
        new_thread.start()
            
            
                    

        




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