from address import Address
from reliability import ReliableConnection
import sys
import time


def main():
    server_port = 30000
    client_port = 30001
    protocol_id = 0x11223344
    delta_time = 1.0 / 30.0
    send_rate = 1.0 / 30.0
    time_out = 10.0
    packet_size = 256

    show_acks = False

    Mode = {
        'Server': 0,
        'Client': 1,
    }

    mode = Mode['Server']
    address = Address()

    if len(sys.argv) >= 2:
        ip = sys.argv[1]
        a,b,c,d = ip.split('.')
        mode = Mode['Client']
        address = Address(a=int(a),b=int(b),c=int(c),d=int(d),port=server_port)

    connection = ReliableConnection(protocol_id, time_out)
    port = server_port if mode == Mode['Server'] else client_port

    if not connection.start(port):
        print("Could not start connection")
        return

    if mode == Mode['Client']:
        connection.connect(address)
    else:
        connection.listen()

    connected = False
    send_accumulator = 0
    stats_accumulator = 0

    flow_control = FlowControl()

    while 1:
        if connection.is_connected():
            flow_control.update(delta_time, connection.reliability_system.rtt * 1000.0)

        send_rate = flow_control.get_send_rate()

        if mode == Mode['Server'] and connected and not connection.is_connected():
            flow_control.reset()
            print("resetting flow control")
            connected = False

        if not connected and connection.is_connected():
            print("Client connected to server")
            connected = True

        if not connected and connection.connect_failed():
            print("Connection failed")
            break

        send_accumulator += delta_time
        while send_accumulator > 1.0 / send_rate:
            packet = [0] * packet_size
            connection.send_packet(packet)
            send_accumulator -= 1.0 / send_rate

        while 1:
            bytes_read = connection.receive_packet(1024)
            if not bytes_read:
                break

        if show_acks:
            acks = connection.reliability_system.acks
            if len(acks) > 0:
                print("acks: ", end='')
                for ack in acks:
                    print(" {}".format(ack))

        connection.update(delta_time)
        stats_accumulator += delta_time

        while stats_accumulator >= 0.25 and connection.is_connected():
            rtt = connection.reliability_system.rtt
            sent_packets = connection.reliability_system.sent_packets
            acked_packets = connection.reliability_system.acked_packets
            lost_packets = connection.reliability_system.lost_packets

            sent_bandwidth = connection.reliability_system.sent_bandwidth
            acked_bandwidth = connection.reliability_system.acked_bandwidth

            print("rtt: {}, sent: {}, acked: {}, lost: {}, sent bandwidth: {}, acked bandwidth: {}"
                .format(rtt, sent_packets, acked_packets, lost_packets, sent_bandwidth, acked_bandwidth))

            stats_accumulator -= 0.25

        time.sleep(delta_time)


class FlowControl(object):

    Mode = {
        "Bad": 0,
        "Good": 1,
    }

    def __init__(self):
        print("Flow control created")
        self.mode = None
        self.penalty_time = 4.0
        self.good_conditions_time = 0.0
        self.penalty_reduction_accumulator = 0.0
        self.reset()

    def reset(self):
        self.mode = self.Mode['Bad']
        self.penalty_time = 4.0
        self.good_conditions_time = 0.0
        self.penalty_reduction_accumulator = 0.0

    def update(self, delta_time, rtt):
        rtt_threshold = 250.0
        if self.mode == self.Mode['Good']:
            if rtt > rtt_threshold:
                print("Dropping into bad mode")
                self.mode = self.Mode['Bad']

                if self.good_conditions_time < 10.0 and self.penalty_time < 60.0:
                    self.penalty_time *= 2.0
                    if self.penalty_time > 60.0:
                        self.penalty_time = 60.0
                    print("Penalty time increased to {}".format(self.penalty_time))

                self.good_conditions_time = 0.0
                self.penalty_reduction_accumulator = 0.0
                return

            self.good_conditions_time += delta_time
            self.penalty_reduction_accumulator += delta_time

            if self.penalty_reduction_accumulator > 10.0 and self.penalty_time > 1.0:
                self.penalty_time /= 1.0
                if self.penalty_time < 1.0:
                    self.penalty_time = 1.0
                print("Penalty time reduced to {}".format(self.penalty_time))

        if self.mode == self.Mode['Bad']:
            if rtt <= rtt_threshold:
                self.good_conditions_time = delta_time
            else:
                self.good_conditions_time = 0.0

            if self.good_conditions_time > self.penalty_time:
                print("Upgrade to good mode!")
                self.good_conditions_time = 0.0
                self.penalty_reduction_accumulator = 0.0
                self.mode = self.Mode['Good']
                return

    def get_send_rate(self):
        return 30.0 if self.mode == self.Mode['Good'] else 10.0

if __name__ == '__main__':
    main()
