#!/usr/bin/env python3
# https://realpython.com/python-sockets/#multi-connection-client-and-server
# https://github.com/realpython/materials/blob/master/python-sockets-tutorial/multiconn-server.py

import os, sys, types
import socket, selectors

# global objects
sel = selectors.DefaultSelector()
mode = None
done = None
cmd = ''

# register first TCP server
s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s1.bind(('', 9998))
s1.listen()
s1.setblocking(False)
s1key = sel.register(s1, selectors.EVENT_READ)
print ('TCP Server1 at {}'.format(s1key.fileobj.getsockname()))

# register second TCP server
s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s2.bind(('', 9999))
s2.listen()
s2.setblocking(False)
s2key = sel.register(s2, selectors.EVENT_READ)
print ('TCP Server2 at {}'.format(s2key.fileobj.getsockname()))

# register first UDP server
s3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s3.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s3.bind(('', 9998))
s3.setblocking(False)
s3key = sel.register(s3, selectors.EVENT_READ)
print ('UDP Server3 at {}'.format(s3key.fileobj.getsockname()))

# register second UDP server
s4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s4.bind(('', 9999))
s4.setblocking(False)
s4key = sel.register(s4, selectors.EVENT_READ)
print ('UDP Server4 at {}'.format(s4key.fileobj.getsockname()))

# register console (Linux and Mac only)
if os.name == 'nt':
    print('Console not implemented for Windows.')
else:
    print('Registering console.')
    import tty, termios
    mode = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin)
    newMode = termios.tcgetattr(sys.stdin)
    newMode[3] |= termios.ECHO
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, newMode)
    stdinKey = sel.register(sys.stdin, selectors.EVENT_READ,)
    
# define handler for TCP accept, and UDP and console messages
def accept_wrapper(key):
    global cmd, done
    # handle TCP events
    if key == s1key or key == s2key:
        conn, addr = key.fileobj.accept()
        print('opening TCP connection: {}'.format(addr))
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        sel.register(conn, events, data=data)
        
    # handle UDP events
    elif key == s3key or key == s4key:
        recv_data, recv_addr = key.fileobj.recvfrom(1024)
        text = recv_data.decode('utf-8').strip()
        print('UDP addr: {}, data: "{}"'.format(recv_addr, text))
        key.fileobj.sendto(b'You typed: ' + recv_data, recv_addr)
        
    # handle console events
    elif key == stdinKey:
        char = key.fileobj.read(1)
        if char == "\n":
            print ('You typed: "{}"'.format(cmd))
            if cmd == 'done': done = True
            if cmd == 'exit': done = True
            if cmd == 'quit': done = True
            cmd = ''
        else:
            cmd += char
        
# define handler for TCP messages
def service_connection(key, mask):
    file = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = file.recv(1024)
        if recv_data:
            data.outb += recv_data
        else:
            print('dropped TCP connection: ', data.addr)
            sel.unregister(file)
            file.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            lend = max(data.outb.find(b'\r'), data.outb.find(b'\n'))
            if -1 < lend:
                text = data.outb[:lend].decode('utf-8').strip()
                print('TCP addr: {}, data: "{}"'.format(data.addr, text))
                sent = file.send(b'You typed: ' + data.outb)
                data.outb = data.outb[sent:]
                if text == 'close':
                    print('closing TCP connection: ', data.addr)
                    sel.unregister(file)
                    file.close()

# main loop
done = False
try:
    # loop until done
    while not done:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key)
            else:
                service_connection(key, mask)
finally:
    # restore terminal settings on Linux and Mac
    if mode: termios.tcsetattr(sys.stdin, termios.TCSADRAIN, mode)
    
    # close selector
    sel.close()

