import asyncio
import struct

from prudp.v0packet import PRUDPV0Packet, PRUDPV0PacketOut
from prudp.protocols import protocol_list
from rc4 import RC4
from binascii  import hexlify
from prudp.protocols import incoming
from prudp.protocols.types.kerberos import KerberosContainer
from prudp.events import Event
from nintendo.nex.streams import StreamOut

class PRUDPClient:
    STATE_EXPECT_SYN = 0
    STATE_EXPECT_CONNECT = 1
    STATE_CONNECTED = 2

    def __init__(self, rc4_key, server, client_addr):
        self.key = rc4_key
        self.rc4_state_encrypt = RC4(rc4_key, reset=False)
        self.rc4_state_decrypt = RC4(rc4_key, reset=False)

        self.last_seq = 1
        self.state = PRUDPClient.STATE_EXPECT_SYN
        self.last_sig = None

        self.server = server
        self.client_addr = client_addr

        self.client_signature = None
        self.server_signature = b'\xaa\xbb\xcc\xdd'
        self.session = None

        self.ack_events = {}

        # self.heartbeat_event = None
        self.timeout_event = Event(self.handle_timeout, timeout=30)
        self.server.scheduler.add(self.timeout_event)

    def decode_packet(self, data):
        return PRUDPV0Packet.decode(data, self.rc4_state_decrypt)

    def handle_data(self, data):
        return self.handle_packet(self.decode_packet(data))

    def handle_packet(self, packet):
        #if self.heartbeat_event:
        #    self.heartbeat_event.reset()
        self.timeout_event.reset()

        if self.state == PRUDPClient.STATE_EXPECT_SYN:
            if packet.op == PRUDPV0Packet.OP_SYN: # SYN
                self.session = packet.session

                self.state = PRUDPClient.STATE_EXPECT_CONNECT

                packet_out = PRUDPV0PacketOut(client=self)
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_SYN
                packet_out.flags = PRUDPV0Packet.FLAG_ACK | PRUDPV0Packet.FLAG_HAS_SIZE
                packet_out.session = self.session
                packet_out.seq = packet.seq
                packet_out.data_size = 0
                p = packet_out.encode(self.rc4_state_encrypt)
                self.send_packet(packet_out)
                return True
            else:
                #print("Got a non-SYN in EXPECT_SYN")
                # return err
                pass
        elif self.state == PRUDPClient.STATE_EXPECT_CONNECT:
            if packet.op == PRUDPV0Packet.OP_CONNECT:
                self.client_signature = packet.conn_sig
                self.state = PRUDPClient.STATE_CONNECTED

                """self.heartbeat_event = Event(self.handle_heartbeat, timeout=5, repeat=True)
                self.server.scheduler.add(self.heartbeat_event)
                print("heartbeat event?")"""

                check = 0
                # TODO: eww, hack
                if packet.data != b'':
                    @incoming('buffer', 'buffer')
                    def parse_connect(fself, a, b):
                        nonlocal check
                        k2, k2_len = KerberosContainer(key=self.key).unpack(b)

                        pid = k2[0:4]
                        cid = k2[4:8]
                        check = struct.unpack("<I", k2[8:12])[0]

                    parse_connect(None, packet.data)

                packet_out = PRUDPV0PacketOut(client=self)
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_CONNECT
                packet_out.flags = PRUDPV0Packet.FLAG_ACK | PRUDPV0Packet.FLAG_HAS_SIZE
                packet_out.session = self.session
                packet_out.seq = packet.seq
                if packet.data != b'':
                    s = StreamOut()
                    s.buffer(struct.pack("<I", check + 1))
                    packet_out.data = s.data
                    packet_out.data_size = len(s.data)
                else:
                    packet_out.data_size = 0
                packet_out.sig = packet.conn_sig
                packet_out.conn_sig = self.server_signature

                self.send_packet(packet_out)
                return True
            else:
                #print("Got a non-CONNECT in EXPECT_CONNECT")
                # return err
                pass
        elif self.state == PRUDPClient.STATE_CONNECTED:
            if packet.op == PRUDPV0Packet.OP_DATA and packet.flags & PRUDPV0Packet.FLAG_ACK == 0:
                # Ack it.
                # TODO: Fragment reassembly here, if required.

                packet_out = PRUDPV0PacketOut(client=self)
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_DATA
                packet_out.flags = PRUDPV0Packet.FLAG_ACK
                packet_out.session = self.session
                packet_out.seq = packet.seq
                packet_out.fragment = 0
                packet_out.data_size = 0

                self.send_packet(packet_out)
                return False # Please handle this further.
            elif packet.op == PRUDPV0Packet.OP_HEARTBEAT:
                # Ack it.
                packet_out = PRUDPV0PacketOut(client=self)
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_HEARTBEAT
                packet_out.flags = PRUDPV0Packet.FLAG_ACK
                packet_out.session = self.session
                packet_out.seq = packet.seq
                packet_out.fragment = 0
                packet_out.data_size = 0
                self.send_packet(packet_out)
                return True
            elif packet.op == PRUDPV0Packet.OP_DISCONNECT:
                packet_out = PRUDPV0PacketOut(client=self)
                packet_out.source = 0xa1
                packet_out.dest = 0xaf
                packet_out.op = PRUDPV0Packet.OP_DISCONNECT
                packet_out.flags = PRUDPV0Packet.FLAG_ACK
                packet_out.session = self.session
                packet_out.seq = packet.seq
                packet_out.fragment = 0
                packet_out.data_size = 0

                self.send_packet(packet_out)
                self.send_packet(packet_out)
                self.send_packet(packet_out)

                del self.server.connections[self.client_addr]
                self.remove_events()

                return True
            elif packet.flags & PRUDPV0Packet.FLAG_ACK != 0:
                if packet.seq in self.ack_events:
                    self.server.scheduler.remove(self.ack_events[packet.seq])
                    del self.ack_events[packet.seq]

                return True

        print("Unhandled packet??")
        print(packet)
        return False

    def send_data(self, data):
        packet_out = PRUDPV0PacketOut(client=self)
        packet_out.source = 0xa1
        packet_out.dest = 0xaf
        packet_out.op = PRUDPV0Packet.OP_DATA
        packet_out.flags = PRUDPV0Packet.FLAG_NEEDS_ACK | PRUDPV0Packet.FLAG_RELIABLE | PRUDPV0Packet.FLAG_HAS_SIZE
        packet_out.session = self.session
        packet_out.seq = self.last_seq
        self.last_seq += 1
        packet_out.fragment = 0
        packet_out.data_size = len(data)
        packet_out.data = data

        self.send_packet(packet_out)


    """def handle_heartbeat(self, ev):
        print("Sending heartbeat {}!", self.last_seq)
        packet_out = PRUDPV0PacketOut(client=self)
        packet_out.source = 0xa1
        packet_out.dest = 0xaf
        packet_out.op = PRUDPV0Packet.OP_HEARTBEAT
        packet_out.flags = PRUDPV0Packet.FLAG_NEEDS_ACK | PRUDPV0Packet.FLAG_RELIABLE
        packet_out.session = self.session
        packet_out.seq = self.last_seq
        packet_out.sig = packet_out.calc_data_sig(b'', self.client_signature)
        self.last_seq += 1
        packet_out.fragment = 0
        packet_out.data_size = 0

        self.send_packet(packet_out)"""

    def handle_missing_ack(self, ev, packet_data, packet_seq):
        print("Missing ack.", ev.counter)
        if ev.counter == 3:
            # Disconnect.
            del self.server.connections[self.client_addr]
            self.remove_events()
        else:
            self.server.sendto(packet_data, self.client_addr)
            ev.counter += 1

    def handle_timeout(self, ev):
        print("Timeout, disconnecting.")
        del self.server.connections[self.client_addr]
        self.remove_events()

    def send_packet(self, packet):
        p = packet.encode(self.rc4_state_encrypt)

        if packet.flags & PRUDPV0Packet.FLAG_NEEDS_ACK:
            ack_ev = Event(self.handle_missing_ack, timeout=2, repeat=True, params=(p, packet.seq))
            ack_ev.counter = 0
            self.ack_events[packet.seq] = ack_ev
            self.server.scheduler.add(ack_ev)

        self.server.sendto(p, self.client_addr)

    def remove_events(self):
        self.server.scheduler.remove(self.timeout_event)
        """if self.heartbeat_event:
            self.server.scheduler.remove(self.heartbeat_event)"""

        for ev in self.ack_events:
            self.server.scheduler.remove(self.ack_events[ev])