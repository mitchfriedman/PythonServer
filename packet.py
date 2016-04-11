class PacketData(object):
    def __init__(self):
        self.sequence = 0
        self._time = 0
        self.size = 0


def sequence_more_recent(seq1, seq2, max_seq):
    return seq1 >= seq2 and (seq1 - seq2 <= max_seq/2) or seq2 > seq1 and (seq2 - seq1 > max_seq/2)


class PacketQueue(object):
    def __init__(self):
        self.queue = []

    def exists(self, sequence):
        return sequence in self.queue

    def insert_sorted(self, packet_data, max_sequence):
        if not len(self.queue):
            self.queue.append(packet_data)
        else:
            if not sequence_more_recent(packet_data.sequence, self.queue[0].sequence, max_sequence):
                self.queue.insert(0, packet_data)
            elif sequence_more_recent(packet_data.sequence, self.queue[-1].sequence, max_sequence):
                self.queue.append(packet_data)
            else:
                for i, packet in enumerate(self.queue):
                    assert (packet.sequence != packet_data.sequence)
                    if sequence_more_recent(packet.sequence, packet_data.sequence, max_sequence):
                        self.queue.insert(i, packet_data)
                        break

    def verify_sorted(self, max_sequence):
        if len(self.queue) == 0:
            return

        prev = self.queue[0]
        
        for i, packet in enumerate(self.queue, 1):
            assert(packet.sequence <= max_sequence)
            assert(sequence_more_recent(packet.sequence, prev.sequence, max_sequence))
            prev = packet

    def clear(self):
        self.queue = []


