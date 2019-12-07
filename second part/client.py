import socket
import sys
import os
import logging


LISTEN_MODE = '0'
USER_MODE = '1'
BUFFER_SIZE = 1024


def CheckIP(stringIp):
    ipArray = stringIp.split(".")
    if len(ipArray) != 4:
        return False
    for seg in ipArray:
        try:  # Check seg
            segInt = int(seg)
            if segInt < 0 or segInt > 255:
                return False
        except ValueError:
            return False
    return True


def CheckInput(inputToCheck):
    # |0->python|1->0/1|2->SERVER IP|3->SERVER PORT|4->LISTEN PORT|
    # |  MODE  | 0-> LISTEN | 1-> USER |
    if len(inputToCheck) < 2:
        return False
    if inputToCheck[1] != LISTEN_MODE and inputToCheck[1] != USER_MODE:
        return False
    if inputToCheck[1] == LISTEN_MODE:
        if len(inputToCheck) != 5:
            return False
        try:  # Check listen port
            port = int(inputToCheck[4])
        except ValueError:
            return False

    if inputToCheck[1] == USER_MODE:
        if len(inputToCheck) != 4:
            return False
    try:  # Check server port
        port = int(inputToCheck[3])
    except ValueError:
        return False
    # Check server ip
    return CheckIP(inputToCheck[2])


def ReadMsgTillNewLine(client_socket):
    allMsg = ""
    while True:
        msg = client_socket.recv(1).decode()
        if msg == '\n':
            break
        allMsg += msg
    return allMsg


def HandleListen(server_ip, server_port, listen_port):

    #  Start connection with server
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.connect((server_ip, server_port))

    #  Get files list
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    stringToSend = '1 ' + str(listen_port) + ' ' + ','.join(files) + '\n'

    #  Send server files list and close connection
    logging.debug("Sending \"" + stringToSend[:-1] + "\"")
    serverSocket.send(stringToSend.encode())
    serverSocket.close()

    #  Open TCP server and wait for clients
    listeningSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listeningSocket.bind(("0.0.0.0", listen_port))
    listeningSocket.listen()
    ListenAndSend(listeningSocket, files)


def ListenAndSend(listeningSocket, files):
    while True:
        # Get a client
        clientSocket, addr = listeningSocket.accept()

        # Get desired file name
        fileName = ReadMsgTillNewLine(clientSocket)
        logging.debug("Uploading " + fileName)

        if fileName in files:  # If file in folder
            #   Open file and send data
            fileToSend = open(fileName, "rb")
            readData = fileToSend.read(BUFFER_SIZE)
            while readData:
                clientSocket.send(readData)
                readData = fileToSend.read(BUFFER_SIZE)
            logging.debug("Done Sending")
            fileToSend.close()
        clientSocket.shutdown(socket.SHUT_RDWR)
        clientSocket.close()


def HandleUser(server_ip, server_port):
    #  Get file name from user
    stringToSearch = input("Search: ")

    #  Connect to server and search
    try:
        socketToServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketToServer.connect((server_ip, server_port))
    except socket.error:
        logging.debug("Could not connect to server!")
        return
    message = "2 " + stringToSearch + '\n'
    socketToServer.send(message.encode())
    result = ReadMsgTillNewLine(socketToServer)  # "[Name] [IP] [Port],[] [] [],...\n"
    socketToServer.close()

    # If no files found stop
    if not result or result == "":
        logging.debug("No files found")
        return

    #  Parse search result in list
    filesDic = {}
    filesList = []
    resultArray = result.split(",")  # [ ([Name] [IP] [Port]) , ([] [] []) , ... ]
    for fileOption in resultArray:
        filesList.append(fileOption.split(" "))
    filesList.sort(key=lambda tup: tup[0])

    #  Print results sorted
    i = 1
    for fileOption in filesList:
        print(str(i) + " " + fileOption[0])
        i += 1

    #  Get choice from user
    fileChooseNumber = 0
    try:
        fileChooseNumber = int(input("Choose: ")) - 1
    except ValueError:
        logging.debug("Could not convert choice number to int")
        return

    if 0 <= fileChooseNumber < len(filesList):
        file_name, sender_ip, sender_port = filesList[fileChooseNumber]
        sender_port = int(sender_port)

        #  Start connection with server
        try:
            socketToSender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socketToSender.connect((sender_ip, sender_port))
        except socket.error:
            logging.debug("Could not connect to sender")
            return
        #  Send sender the file name
        socketToSender.send(file_name.encode() + "\n".encode())

        #  Write file
        fileToWrite = open(file_name, "wb")
        dataGot = socketToSender.recv(BUFFER_SIZE)
        while dataGot:
            fileToWrite.write(dataGot)
            dataGot = socketToSender.recv(BUFFER_SIZE)
        #  Close connection and file
        fileToWrite.close()
        socketToSender.close()
    else:
        logging.debug("Bad choice")
        return


if __name__ == "__main__":  # INPUT = 1:0 2:127.0.0.1 3:12345 4:12346
    if not CheckInput(sys.argv):
        exit(0)
    mainIp = sys.argv[2]
    mainPort = int(sys.argv[3])
    if sys.argv[1] == LISTEN_MODE:
        listenPort = int(sys.argv[4])
        HandleListen(mainIp, mainPort, listenPort)
    else:
        while True:
            HandleUser(mainIp, mainPort)
