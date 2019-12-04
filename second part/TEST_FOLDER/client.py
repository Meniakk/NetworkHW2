import socket
import sys
import os

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


def HandleListen(server_ip, server_port, listen_port):
    #  Start connection with server
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.connect((server_ip, server_port))

    #  Get files list
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    stringToSend = '1 ' + str(listen_port) + ' ' + ','.join(files)

    #  Send server files list
    print("Sending " + stringToSend)
    serverSocket.send(stringToSend.encode())

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
        fileName = clientSocket.recv(BUFFER_SIZE).decode()[:-1]
        print("Uploading " + fileName)

        if fileName in files:  # If file in folder
            #   Open file and send data
            fileToSend = open(fileName, "rb")
            readData = fileToSend.read(BUFFER_SIZE)
            while readData:
                clientSocket.send(readData)
                readData = fileToSend.read(BUFFER_SIZE)
            print("Done Sending")
            fileToSend.close()
        clientSocket.shutdown(socket.SHUT_RDWR)
        clientSocket.close()


def HandleUser(server_ip, server_port):
    #  Get file name from user
    stringToSearch = input("Search: ")

    #  Connect to server and search
    socketToServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketToServer.connect((server_ip, server_port))
    message = "2 " + stringToSearch
    socketToServer.send(message.encode())
    result = socketToServer.recv(BUFFER_SIZE).decode()  # "[Name] [IP] [Port],[] [] [],...\n"
    result = result[:-1]  # Delete "\n"
    socketToServer.close()

    # If no files found stop
    if not result:
        print("No files found")
        return

    #  parse search result and print
    filesDic = {}
    filesList = []
    resultArray = result.split(",")  # [ ([Name] [IP] [Port]) , ([] [] []) , ... ]
    for fileOption in resultArray:
        filesList.append(fileOption.split(" "))
    resultArray.sort(key=lambda tup: tup[0])

    #  Get choice from user
    fileChooseNumber = input("Choose: ")
    if fileChooseNumber in filesDic:
        file_name, sender_ip, sender_port = filesDic[fileChooseNumber]
        sender_port = int(sender_port)
        #  Start connection with server
        socketToSender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketToSender.connect((sender_ip, sender_port))

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


if __name__ == "__main__":  # INPUT = 1:0 2:127.0.0.1 3:12345 4:12346
    if not CheckInput(sys.argv):
        exit(0)
    mainIp = sys.argv[2]
    mainPort = int(sys.argv[3])
    if sys.argv[1] == LISTEN_MODE:
        listenPort = int(sys.argv[4])
        HandleListen(mainIp, mainPort, listenPort)
    else:
        HandleUser(mainIp, mainPort)
