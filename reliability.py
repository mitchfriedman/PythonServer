from connection import Connection
from packet import PacketData, PacketQueue, sequence_more_recent


class ReliabilitySystem(object):
    def __init__(self, max_sequence=0xFFFFFFFF):
        self.rtt_max = 1.0
        self.rtt = 0.0

        self.max_sequence = max_sequence

        self.local_sequence = 0
        self.remote_sequence = 0

        self.sent_packets = 0
        self.recv_packets = 0
        self.lost_packets = 0
        self.acked_packets = 0
        self.sent_bandwidth = 0.0
        self.acked_bandwidth = 0.0

        self.acks = []

        self.sent_queue = PacketQueue()
        self.pending_ack_queue = PacketQueue()
        self.received_queue = PacketQueue()
        self.acked_queue = PacketQueue()


    def reset(self):
        self.local_sequence = 0
        self.remote_sequence = 0

        self.sent_queue.clear()
        self.received_queue.clear()
        self.acked_queue.clear()
        self.sent_packets = 0
        self.recv_packets = 0
        self.lost_packets = 0
        self.acked_packets = 0
        self.sent_bandwidth = 0.0
        self.acked_bandwidth = 0.0
        self.rtt = 0.0
        self.rtt_max = 1.0

    def packet_sent(self, size):
        if self.sent_queue.exists(self.local_sequence):
            print("Local sequence {} exists".format(self.local_sequence))
            for packet in self.sent_queue.queue:
                print(" + {}", packet.sequence)

        assert(not self.sent_queue.exists(self.local_sequence))
        assert(not self.pending_ack_queue.exists(self.local_sequence))
        packet = PacketData()
        packet.sequence = self.local_sequence
        packet._time = 0.0
        packet.size = size

        self.sent_queue.queue.append(packet)
        self.pending_ack_queue.queue.append(packet)

        self.sent_packets += 1
        self.local_sequence += 1
        if self.local_sequence > self.max_sequence:
            self.local_sequence = 0

    def packet_received(self, sequence, size):
        self.recv_packets += 1
        if self.received_queue.exists(sequence):
            return
        packet = PacketData()
        packet.sequence = sequence
        packet._time = 0
        packet.size = size
        self.received_queue.queue.append(packet)
        if sequence_more_recent(sequence, self.remote_sequence, self.max_sequence):
            self.remote_sequence = sequence
    
    def generate_ack_bits(self):
        return ReliabilitySystem._generate_ack_bits(self.remote_sequence, self.received_queue, self.max_sequence)

    @staticmethod
    def _generate_ack_bits(ack, received_queue, max_sequence):
        ack_bits = 0
        for packet in received_queue.queue:
            if packet.sequence == ack or sequence_more_recent(packet.sequence, ack, max_sequence):
                break
            bit_index = ReliabilitySystem.bit_index_for_sequence(packet.sequence, ack, max_sequence)
            if bit_index <= 31:
                ack_bits |= 1 << bit_index

        return ack_bits

    @staticmethod
    def bit_index_for_sequence(sequence, ack, max_sequence):
        assert(sequence != ack)
        assert(not sequence_more_recent(sequence, ack, max_sequence))
        if sequence > ack:
            assert(ack < 33)
            assert(max_sequence >= sequence)
            return ack + (max_sequence - sequence)
        else:
            assert(ack >= 1)
            assert(sequence <= ack - 1)
            return ack - 1 - sequence

    def process_ack(self, ack, ack_bits):
        if not len(self.pending_ack_queue.queue):
            return

        should_remove = []
        for packet in self.pending_ack_queue.queue:
            acked = False
            if packet.sequence == ack:
                acked = True
            elif not sequence_more_recent(packet.sequence, ack, self.max_sequence):
                bit_index = ReliabilitySystem.bit_index_for_sequence(packet.sequence, ack, self.max_sequence)
                if bit_index <= 31:
                    acked = (ack_bits >> bit_index) & 1

            if acked:
                self.rtt += (packet._time - self.rtt) * 0.1 # exponentially smoothed moving average

                self.acked_queue.insert_sorted(packet, self.max_sequence)
                self.acks.append(packet.sequence)
                self.acked_packets += 1
                should_remove.append(packet)
        
        for pack in should_remove:
            self.pending_ack_queue.queue.remove(pack)
    
    def advance_queue_time(self, delta_time):
        for packet in self.sent_queue.queue:
            packet._time += delta_time

        for packet in self.received_queue.queue:
            packet._time += delta_time

        for packet in self.pending_ack_queue.queue:
            packet._time += delta_time

        for packet in self.acked_queue.queue:
            packet._time += delta_time

    def update(self, delta_time):
        self.acks = []
        self.advance_queue_time(delta_time)
        #self.update_queues()
        self.update_stats()
        self.validate()

    def validate(self):
        self.sent_queue.verify_sorted(self.max_sequence)
        self.received_queue.verify_sorted(self.max_sequence)
        self.pending_ack_queue.verify_sorted(self.max_sequence)
        self.acked_queue.verify_sorted(self.max_sequence)

    def update_queues(self):
        epsilon = 0.001

        to_remove = []
        for packet in self.sent_queue.queue:
            if packet._time <= self.rtt_max + epsilon:
                break
            to_remove.append(packet)

        for packet in to_remove:
            self.sent_queue.queue.remove(packet)

        if len(self.received_queue.queue):
            latest_sequence = self.received_queue.queue[-1].sequence
            min_sequence = latest_sequence - 34 if latest_sequence >= 34 else self.max_sequence - (34 - latest_sequence)

            to_remove = []
            for i, packet in enumerate(self.received_queue.queue, 1):
                if sequence_more_recent(packet.sequence, min_sequence, self.max_sequence):
                    break
                to_remove.append(packet)

            for packet in to_remove:
                self.received_queue.queue.remove(packet)

        to_remove = []
        for packet in self.acked_queue.queue:
            if packet._time <= self.rtt_max * 2 - epsilon:
                to_remove.append(packet)

        for packet in to_remove:
            self.acked_queue.queue.remove(packet)

        to_remove = []
        for packet in self.pending_ack_queue.queue:
            if packet._time <= self.rtt_max + epsilon:
                to_remove.append(packet)

        for packet in to_remove:
            self.pending_ack_queue.queue.remove(packet)
            self.lost_packets += 1

    def update_stats(self):
        self.sent_bytes_per_sec = 0
        for packet in self.sent_queue.queue:
            self.sent_bytes_per_sec += packet.size

        self.acked_bytes_per_sec = 0
        self.acked_packets_per_sec = 0
        for packet in self.acked_queue.queue:
            if packet._time > self.rtt_max:
                self.acked_bytes_per_sec += packet.size
                self.acked_packets_per_sec += 1

        self.sent_bytes_per_sec /= self.rtt_max
        self.acked_bytes_per_sec /= self.rtt_max
        self.sent_bandwidth = self.sent_bytes_per_sec * (8 / 1000.0)
        self.acked_bandwidth = self.acked_bytes_per_sec * (8 / 1000.0)


class ReliableConnection(Connection):
    def __init__(self, protocol_id, time_out, max_sequence=0xFFFFFFFF):
        self.reliability_system = ReliabilitySystem(max_sequence)
        super().__init__(protocol_id, time_out)

    def send_packet(self, data):
        header = 12
        seq = self.reliability_system.local_sequence
        ack = self.reliability_system.remote_sequence
        ack_bits = self.reliability_system.generate_ack_bits()

        packet = self.write_header(seq, ack, ack_bits) + data
        if not super().send_packet(packet):
            return False
        self.reliability_system.packet_sent(len(data))

    def receive_packet(self, size):
        header = 12
        if size < header:
            return False

        size, received_bytes = super().receive_packet(size+header)

        if size <= header:
            return False

        seq, ack, ack_bits = self.read_header(received_bytes)
        self.reliability_system.packet_received(seq, size - header)
        self.reliability_system.process_ack(ack, ack_bits)

        return size-header, received_bytes[header:]

    def update(self, delta_time):
        super().update(delta_time)
        self.reliability_system.update(delta_time)

    def get_header_size(self):
        return super().header_size + self.reliability_system.get_header_size()

    def write_integer(self, value):
        return [(value >> 24), (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF]

    def write_header(self, sequence, ack, ack_bits):
        seq = self.write_integer(sequence)
        ack = self.write_integer(ack)
        bits = self.write_integer(ack_bits)

        return seq + ack + bits

    def read_integer(self, data, pos):
        return (data[pos] << 24) | (data[pos+1] << 16) | (data[pos+2] << 8) | (data[pos+3])

    def read_header(self, header):
        seq = self.read_integer(header, 0)
        ack = self.read_integer(header, 4)
        ack_bits = self.read_integer(header, 8)

        return seq, ack, ack_bits

    def on_stop(self):
        self.clear_data()

    def on_disconnect(self):
        self.clear_data()

    def clear_data(self):
        self.reliability_system.reset()
