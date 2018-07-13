from prudp.protocols import incoming,outgoing
import struct
from binascii import unhexlify
import hmac
import hashlib
from rc4 import RC4
import persistence
from prudp.protocols.types import NintendoNotificationEventGeneral, MiiV2
from nintendo.nex.common import DateTime

class Friends3DSProtocol:
    def __init__(self, client):
        self.client = client
        self.server = client.server

        self.methods = {}
        self.methods[0x01] = self.update_my_profile
        self.methods[0x02] = self.update_mii
        self.methods[0x03] = self.update_mii_list
        self.methods[0x04] = self.update_played_games
        self.methods[0x05] = self.update_preference
        self.methods[0x06] = self.get_friend_mii
        # 0x07
        # 0x08
        self.methods[0x09] = self.get_principal_id_by_friend_code
        # 0x0a
        self.methods[0x0b] = self.add_friend_by_principal_id
        # 0x0b
        # 0x0c
        # 0x0d
        self.methods[0x0e] = self.remove_friend
        # 0x10
        self.methods[0x11] = self.sync_friend
        self.methods[0x12] = self.update_presence
        self.methods[0x13] = self.update_favorite_game_key
        self.methods[0x14] = self.update_comment
        # 0x15
        self.methods[0x16] = self.get_friend_presence
        # 0x17
        self.methods[0x18] = self.get_friend_picture
        self.methods[0x19] = self.get_friend_persistent_info
        # 0x1a

    @incoming("MyProfile")
    def update_my_profile(self, profile):
        print(profile)
        return (True, 0x00010001, None)

    @incoming("MiiV1")
    def update_mii(self, mii):
        # TODO: Save it or something?
        self.client.user.mii = MiiV2.from_miiv1(mii)
        self.broadcast_notification(5, NintendoNotificationEventGeneral(0,0,0,DateTime.utcnow(),''))

        return (True, 0x00010001, None)

    @incoming("MiiList") # Not List<Mii>!
    def update_mii_list(self, mii_list):
        print(mii_list)
        return (True, 0x00010001, None)

    @incoming("list<PlayedGame>")
    def update_played_games(self, games):
        print(games)
        return (True, 0x00010001, None)

    @incoming("bool", "bool", "bool")
    def update_preference(self, a, b, c):
        print("update_preference:", a, b, c)
        return (True, 0x00010001, None)

    @incoming("list<u32>")
    @outgoing("list<FriendMii>")
    def get_friend_mii(self, principal_ids):
        miis = []
        for pid in principal_ids:
            miis.append(persistence.User.get(pid).get_mii())
        return  (True, 0x00010001, (miis,))

    @incoming("list<u32>")
    @outgoing("list<FriendRelationship>")
    def get_friend_relationships(self, principal_ids):
        if len(principal_ids) == 0:
            relationships = []
        else:
            relationships = self.client.user.get_friend_relationships(filter=principal_ids)
        return (True, 0x00010001, (relationships,))

    @incoming("u64", "u32")
    @outgoing("FriendRelationship")
    def add_friend_by_principal_id(self, mostly_lfcs, principal_id):
        relationship = self.client.user.add_friend(mostly_lfcs, principal_id)
        if relationship.is_complete == True:
            # ok, relationship complete
            # send a notif to the other side
            self.send_notification(principal_id, 7, NintendoNotificationEventGeneral(0,0,0,DateTime.utcnow(),''))

        return (True, 0x00010001, (relationship,))

    @incoming("u64")
    @outgoing("u32")
    def get_principal_id_by_friend_code(self, friend_code):
        pid = 0
        return (True, 0x00010001, (pid,))

    @incoming("u32")
    def remove_friend(self, principal_id):
        self.client.user.remove_friend(principal_id)
        return (True, 0x00010001, None)

    @outgoing("list<FriendRelationship>")
    def get_all_friends(self, _):
        relationships = self.client.user.get_friend_relationships()
        return (True, 0x00010001, (relationships,))

    @incoming("u64", "list<u32>", "list<u64>")
    @outgoing("list<FriendRelationship>")
    def sync_friend(self, mostly_lfcs, principal_ids, unknown):
        if len(principal_ids) == 0:
            relationships = []
        else:
            relationships = self.client.user.get_friend_relationships(filter=principal_ids)
        return (True, 0x00010001, (relationships,))

    @incoming("NintendoPresenceV1", "bool")
    def update_presence(self, presence, unk_bool):
        # TODO: Save it? Not really needed. Sorta.
        self.client.user.presence = presence
        self.broadcast_notification(1, presence)
        return (True, 0x00010001, None)

    @incoming("GameKey")
    def update_favorite_game_key(self, game_key):
        # TODO: Save it!
        self.client.user.persistent_info.game_key = game_key
        return (True, 0x00010001, None)

    @incoming("string")
    def update_comment(self, comment):
        # TODO: Save it!
        self.client.user.persistent_info.status = comment
        self.broadcast_notification(3, NintendoNotificationEventGeneral(0,0,0,DateTime.utcnow(),comment))
        return (True, 0x00010001, None)

    @incoming("list<u32>")
    @outgoing("list<FriendPresence>")
    def get_friend_presence(self, principal_ids):
        print("GetFriendPresence", principal_ids)
        infos = []
        for pid in principal_ids:
            p = persistence.User.get(pid).get_presence()
            if p != None:
                infos.append(p)
        return (True, 0x00010001, (infos,))

    @incoming("list<u32>")
    @outgoing("list<FriendPicture>")
    def get_friend_picture(self, ):
        return (True, 0x00010001, ([],))

    @incoming("list<u32>")
    @outgoing("list<FriendPersistentInfo>")
    def get_friend_persistent_info(self, principal_ids):
        print("GetFriendPersistentInfo", principal_ids)
        infos = []
        for pid in principal_ids:
            i = persistence.User.get(pid).get_friend_persistent_info()
            infos.append(i)
        return (True, 0x00010001, (infos,))

    def broadcast_notification(self, notif_type, payload):
        print("Broadcasting type {}, payload = {}".format(notif_type, payload))
        friends = persistence.User.get_friend_pids(self.client.user.pid)
        for client_ip in self.server.connections:
            client = self.server.connections[client_ip]
            if hasattr(client, 'user'):
                if client.user.pid in friends:
                    client.send_notification(notif_type, self.client.user.pid, payload)

    def send_notification(self, remote_pid, notif_type, payload):
        print("Sending type {} to pid {}, payload = {}".format(notif_type, remote_pid, payload))
        for client_ip in self.server.connections:
            client = self.server.connections[client_ip]
            if hasattr(client, 'user'):
                if client.user.pid == remote_pid:
                    client.send_notification(notif_type, self.client.user.pid, payload)
                    break
                else:
                    # TODO: queue notifications if the target isn't online!
                    # For now, drop them into the void.
                    print("Queueing notifs when?????")