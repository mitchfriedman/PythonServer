import time
from connection import Connection
from address import Address


def main():
    server_port = 30000
    client_port = 30001
    protocol_id = 0x99887766
    delta_time = 0.25
    send_rate = 0.25
    time_out = 10

    connection = Connection(protocol_id, time_out)
    
    if not connection.start(client_port):
        print("Could not start connection on port {}".format(client_port))
        return

    connection.connect(Address(a=127,b=0,c=0,d=1,port=server_port))
    connected = False

    while 1:
        if not connected and connection.is_connected():
            print("Client connected to server")
            connected = True

        if not connected and connection.connect_failed():
            print("Connection failed")
            break
        
        packet = [c for c in 'client to server']
        sent_bytes = connection.send_packet(packet)

        while 1:
            bytes_read, pack = connection.receive_packet(256)
            if bytes_read == 0:
                break
            print("Received packet from server")

        connection.update(delta_time)
        time.sleep(delta_time)


if __name__ == '__main__':
    main()
