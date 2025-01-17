#!/usr/bin/env python3
# Two TCP servers, two UDP servers, and a console,
# Single process, multiple threads
# M. Williamsen, 15 January 2025
# https://docs.python.org/3/library/socketserver.html

import socket, threading, socketserver, json

# initialize connection list
# TODO consider adding the following to connection records:
# * port number and protocol
# * Start date/time (to compute how long connected)
# * log to disk file (both UDP and TCP)
# * user name if logged in

tcpList = []

class TCPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        # add new connection to list
        tcpList.append(self.client_address)
        
        # maintain connection until dropped or closed
        # TODO consider inputs and outputs which are not in lock-step
        # TODO would this imply two separate threads for read and write?
        notDone = True
        while notDone:
            # show prompt
            theThread = threading.current_thread()
            thePrompt = '{}: '.format(theThread.name)
            self.wfile.write(bytes(thePrompt, 'ascii'))

            # check for dropped connection
            self.data = self.rfile.readline()
            if not len(self.data):
                notDone = False
                print ('Connection dropped.')
                break

            # check for closed connection
            self.data = self.data.strip()
            if self.data == b'close':
                notDone = False
                print ('Connection closed.')
                break

            # handle client input
            response = '{} typed: {}'.format(self.client_address, self.data.decode('utf-8'))
            print(response)
            self.wfile.write(bytes(response + '\r\n', 'ascii'))
            
        # remove connection from list
        tcpList.remove(self.client_address)

class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class UDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # TODO consider inputs and outputs which are not in lock-step
        # TODO would this imply two separate threads for read and write?
        self.data = self.request[0].strip()
        socket = self.request[1]
        response = '{} typed: {}'.format(self.client_address, self.data.decode('utf-8'))
        print(response)
        socket.sendto(bytes(response + '\r\n', 'ascii'), self.client_address)
        
class UDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass

if __name__ == '__main__':
    # initialize TCP socket servers
    server1 = TCPServer(('', 9998), TCPHandler)
    server2 = TCPServer(('', 9999), TCPHandler)
    server1.daemon_threads = True
    server2.daemon_threads = True
    
    # initialize UDP socket servers
    server3 = UDPServer(('', 9998), UDPHandler)
    server4 = UDPServer(('', 9999), UDPHandler)
    server3.daemon_threads = True
    server4.daemon_threads = True

    # run the servers in threads
    with server1, server2, server3, server4:
        serverThread1 = threading.Thread(target=server1.serve_forever)
        serverThread1.daemon = True
        serverThread1.start()
        print('Server1:', serverThread1.name)

        serverThread2 = threading.Thread(target=server2.serve_forever)
        serverThread2.daemon = True
        serverThread2.start()
        print('Server2:', serverThread2.name)
        
        serverThread3 = threading.Thread(target=server3.serve_forever)
        serverThread3.daemon = True
        serverThread3.start()
        print('Server3:', serverThread3.name)
        
        serverThread4 = threading.Thread(target=server4.serve_forever)
        serverThread4.daemon = True
        serverThread4.start()
        print('Server4:', serverThread4.name)

        # run console in main thread
        notDone = True
        while notDone:
            theInput = input('what? ')
            print('You typed: {0}'.format(theInput))
            if theInput == 'quit' or theInput == 'exit': notDone = False
            if theInput == 'list': print(json.dumps(tcpList, indent = 2))

        # clean up when done
        server1.shutdown()
        server2.shutdown()
        server3.shutdown()
        server4.shutdown()
