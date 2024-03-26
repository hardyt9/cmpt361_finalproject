# Server.py
import socket, sys, os, glob, datetime, json
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

def server():
    serverPort = 13000

    # retrieve the servers private keys
    with open('server_private.pem', 'rb') as file:
        server_private_key = RSA.import_key(file.read())

    while True:
        try:
            serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serverSocket.bind(('', serverPort))
            serverSocket.listen(1)
        except socket.error as e:
            print('Error in server socket binding:', e)
            sys.exit(1)

        while True:
            try:
                connectionSocket, addr = serverSocket.accept()
                child_pid = os.fork()
                if child_pid == 0:  
                    # Send Username message to server
                    usernameMessage = ("Enter your username: ")
                    connectionSocket.send(usernameMessage.encode('ascii'))
                    # Receive Username
                    encrypted_username = connectionSocket.recv(2048)
                    username = rsa_decrypt(encrypted_username, server_private_key).decode()
                    # Send Password message to server 
                    passwordMessage = ("Enter your password: ")
                    connectionSocket.send(passwordMessage.encode('ascii'))
                    # Receive password
                    encrypted_password = connectionSocket.recv(2048)
                    password = rsa_decrypt(encrypted_password, server_private_key).decode()

                    # get directory of user_pass.json
                    dir = os.path.dirname(os.path.abspath(__file__))
                    user_pass = os.path.join(dir,"user_pass.json")
                    # Open user_pass file and read dictonary
                    with open(user_pass, 'rb') as users:
                        data = json.load(users)
                  
                    # check if username & password is valid
                    authorization = 0
                    sym_key = None
                    for db_username in data.keys():
                        if db_username == username:
                            db_password = data[db_username]
                            if password == db_password:
                                authorization = 1
                                # retrieve the clients public keys
                                with open('%s_public.pem' % username, 'rb') as file:
                                    client_public_key = RSA.import_key(file.read())
                                # create the sym_key, encode it, and send it
                                sym_key = generate_key()
                                symkey_encrypted = rsa_encrypt(sym_key, client_public_key)
                                # send length of encrypted key
                                connectionSocket.send(len(symkey_encrypted).to_bytes(4, 'big'))
                                connectionSocket.send(symkey_encrypted)
                                print("Connection Accepted and Symmetric Key Generated for client: " + username)
                                break
                            else:
                                break

                    # receive the "OK"
                    connectionSocket.recv(2048)
                    if authorization == 1: # TODO accept only certain users
                        # Create menu prompts and sent to the client
                        menuMessage = ("\nSelect the operation:\n\t1) Create and send an email\n\t2) Display the inbox list\n\t3) Display the email contents\n\t4) Terminate the connection\nChoice: ")
                        connectionSocket.send(menuMessage.encode('ascii'))

                        while (1):
                            # Receive user chice from client 
                            clientChoice = connectionSocket.recv(2048)
                            decodedChoice = clientChoice.decode('ascii')

                            if decodedChoice == "1":
                                # Send destination prompt to the client 
                                destination = "Enter destinations (seperated by;): "
                                connectionSocket.send(destination.encode('ascii'))
                                # Receive the destinations from the client 
                                destination = connectionSocket.recv(2048).decode('ascii')
                                print(destination)
                    
                                # Send title prompt to the user 
                                title = "Enter title: "
                                connectionSocket.send(title.encode('ascii'))
                                # receive title from the client
                                title = connectionSocket.recv(2048).decode('ascii')
                                print(title)

                                # Send loadFile prompt to the user
                                loadFile= "Would you like to load contents from a file?(Y/N)"
                                connectionSocket.send(loadFile.encode('ascii'))
                                # Receive response from user
                                loadFile = connectionSocket.recv(2048).decode('ascii')
                                print(loadFile)

                                # Send content prompt to the user
                                contents = "Enter message contents: "
                                connectionSocket.send(contents.encode('ascii'))
                                # Receive content from the client 
                                content = connectionSocket.recv(2048).decode('ascii')
                                print(content)

                            elif decodedChoice == "2":
                                # Get inbox list and send to server
                                inboxlist = "Inbox List Info Displayed"
                                connectionSocket.send(inboxlist.encode('ascii'))

                            elif decodedChoice == "3":
                                # Send prompt to server
                                response = "Enter the email index you wish to view: "
                                connectionSocket.send(response.encode('ascii'))
                                # Receive index from user
                                index = connectionSocket.recv(2048).decode('ascii')
                                print(index)

                            elif decodedChoice == "4":
                                # terminate connection
                                connectionSocket.close()
                                sys.exit(1)

                            else:
                                print("Invalid choice.")

                    else:
                        print("The received client information: " + username + " is invalid (Connection Terminated).")
                        terminationMessage = "Invalid username or password.\nTerminating."
            
                        connectionSocket.send(terminationMessage.encode('ascii'))
                        connectionSocket.close()
                        

            except socket.error as e:
                print('An error occurred:', e)
                serverSocket.close()
                sys.exit(1)
            except Exception as e:
                print('An unexpected error occurred:', e)
                serverSocket.close()
                sys.exit(1)

# RSA decrypt method for initial handshake between client and server
def rsa_decrypt(encrypted_message, private_key):
    cipher = PKCS1_OAEP.new(private_key)
    decrypted_message = cipher.decrypt(encrypted_message)
    return decrypted_message

# RSA encrypt method for initial handshake between client and server
def rsa_encrypt(message, public_key):
    cipher = PKCS1_OAEP.new(public_key)
    encrypted_message = cipher.encrypt(message)
    return encrypted_message

# encrypts messages sent by server using AES (symmetric keys)
def encrypt(message, key, socket):
    cipher = AES.new(key, AES.MODE_ECB)
    cipher_bytes = cipher.encrypt(pad(message.encode(), AES.block_size))
    socket.send(cipher_bytes)
# decrypts messages sent by client using AES (symmetric keys)
def decrypt(ciphertext, key):
    cipher = AES.new(key, AES.MODE_ECB)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode()

# generates a 256 AES key ( 256 = 32 bytes) that will exchanged with client
def generate_key(key_size=32):
    return get_random_bytes(key_size)

# call the server function below
if __name__ == "__main__":
    server()

