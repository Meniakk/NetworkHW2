import socket
import sys
import logging  #

# A dictionary of clients (ip,port) to files list
clientsDictionary = {}


def CheckMsgValid(msg):
    if msg[0] != '1' and msg[0] != '2':
        return False

    if msg[0] == '1':
        if len(msg.strip()) < 3:
            return False
        args = msg.split(" ")
        if len(args) < 3:
            return False
    else:
        if len(msg.strip()) < 2:
            return False
        args = msg.split(" ")
        if len(args) < 2:
            return False
    if msg[1] != ' ':
        return False

    return True


def ReadMsgTillNewLine(client_socket):
    allMsg = ""
    while True:
        msg = client_socket.recv(1).decode()
        if msg == '\n':
            break
        allMsg += msg
    return allMsg


def HandleConnection(client_socket, client_address):
    # Connection was made, read msg
    msg = ReadMsgTillNewLine(client_socket)
    logging.debug("Rec: " + msg)
    if CheckMsgValid(msg):
        # msg is valid, do work
        if msg[0] == '1':
            HandleJoin(msg, client_address)
        if msg[0] == '2':
            HandleSearch(msg, client_socket)
    else:
        if msg[0] == '2' and msg == '2 ':
            HandleSearch(msg, client_socket)
        else:
            logging.debug("Bad msg")


def HandleJoin(msg, client_address):
    args = msg.split(" ")  # |0->1|1->port|2->files|
    ip, _ = client_address
    files = args[2].split(",")
    logging.debug("Got this files: " + str(files))
    clientsDictionary[(ip, args[1])] = files


def HandleSearch(msg, client_socket):
    args = msg.split(" ")  # |0->2|1->string|
    strToFind = args[1]

    if not strToFind or strToFind == '':
        client_socket.send("\n".encode())
        return

    logging.debug("Searching for " + strToFind)
    filesFound = []
    # Search in dic for a client with a file
    for currentClientAddr in clientsDictionary:
        currentClientIp, currentClientPort = currentClientAddr
        currentFiles = clientsDictionary[currentClientAddr]
        # Search in list for a file
        for currentFile in currentFiles:
            if currentFile.find(strToFind, 0, len(currentFile)) != -1:
                filesFound.append((currentFile, currentClientIp, currentClientPort))

    # send client files
    currentFilesFound = ""
    for currentFile, currentIp, currentPort in filesFound:
        currentFilesFound += currentFile + " " + currentIp + " " + currentPort + ","
    # If files found parse
    if filesFound:
        currentFilesFound = currentFilesFound[:-1]
        logging.debug("Found: " + currentFilesFound)
        currentFilesFound += "\n"

    # If no files found, send only new line
    else:
        logging.debug("Found nothing")
        currentFilesFound = "\n"
    client_socket.send(currentFilesFound.encode())


if __name__ == "__main__":  # |argv: 0->python|1->port|
    # Make sure we have our arguments
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if len(sys.argv) > 1:
        # Make sure argument is valid
        server_ip = '0.0.0.0'
        server_port = int(sys.argv[1])
        server.bind((server_ip, server_port))
        server.listen()
        while True:
            c_socket, c_address = server.accept()
            logging.debug("Got client")
            HandleConnection(c_socket, c_address)
            c_socket.close()
            logging.debug("Finished with client\n")
    server.close()
