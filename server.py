import time
from connection import Connection


def main():
    server_port = 30000
    client_port = 30001
    protocol_id= 0x99887766
    delta_time = 0.25
    send_rate = 0.25
    time_out = 10

    connection = Connection(protocol_id, time_out)

    if not connection.start(server_port):
        print("Could not start connection on port {}".format(server_port))
        return 1

    connection.listen()

    while 1:
        if connection.is_connected():
            print('server sending packet')
            packet = [c for c in "server to client"]
            connection.send_packet(packet)

        while 1:
            bytes_read, pack = connection.receive_packet(256)
            if bytes_read == 0:
                break
            print("Received packet from client")

        connection.update(delta_time)
        time.sleep(delta_time)


if __name__ == "__main__":
    main()
