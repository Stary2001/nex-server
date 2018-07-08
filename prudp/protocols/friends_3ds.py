from prudp.protocols import incoming,outgoing
import struct
from binascii import unhexlify
import hmac
import hashlib
from rc4 import RC4

class Friends3DSProtocol:
    def __init__(self, server):
        self.server = server
        self.methods = {}
        self.methods[0x01] = self.update_my_profile
        self.methods[0x02] = self.update_mii
        self.methods[0x03] = self.update_mii_list
        self.methods[0x04] = self.update_played_games
        self.methods[0x05] = self.update_preference
        self.methods[0x0b] = self.add_friend_by_principal_id
        self.methods[0x09] = self.get_principal_id_by_friend_code
        # 0x0a
        # 0x0b
        # 0x0c
        # 0x0d
        self.methods[0x0e] = self.method0e
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
        print(mii)
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
    @outgoing("list<FriendRelationship>")
    def get_friend_relationships(self, principal_ids):
        return (True, 0x00010001, ([],))

    @incoming("u64", "u32")
    @outgoing("FriendRelationship")
    def add_friend_by_principal_id(self, mostly_lfcs, principal_id):
        print("add friend by principal id:", mostly_lfcs, principal_id)
        return (True, 0x00010001, None)

    @incoming("u64")
    def get_principal_id_by_friend_code(self, friend_code):
        print("get principal id by friend code:", friend_code)
        return (True, 0x00010001, None)

    def method0e(self, data):
        print("method 0e:", data)
        return (True, 0x00010001, None)

    @outgoing("list<FriendRelationship>")
    def get_all_friends(self, _):
        return (True, 0x00010001, ([],))

    @incoming("u64", "list<u32>", "list<u64>")
    @outgoing("list<FriendRelationship>")
    def sync_friend(self, mostly_lfcs, principal_ids, unknown):
        print("SyncFriend: {:016x}".format(mostly_lfcs), principal_ids, unknown)
        return (True, 0x00010001, ([],))

    @incoming("NintendoPresenceV1", "bool")
    def update_presence(self, presence, unk_bool):
        print("update_presence:", "{:016x}".format(presence.game_key.title_id), unk_bool)
        return (True, 0x00010001, None)

    @incoming("GameKey")
    def update_favorite_game_key(self, game_key):
        print("update_favorite_game_key:", game_key)
        return (True, 0x00010001, None)

    @incoming("string")
    def update_comment(self, comment):
        print("update_comment:", comment)
        return (True, 0x00010001, None)

    @incoming("list<u32>")
    @outgoing("list<FriendPresence>")
    def get_friend_presence(self, ):
        return (True, 0x00010001, ([],))

    @incoming("list<u32>")
    @outgoing("list<FriendPicture>")
    def get_friend_picture(self, ):
        return (True, 0x00010001, ([],))

    @incoming("list<u32>")
    @outgoing("list<FriendPersistentInfo>")
    def get_friend_persistent_info(self):
        return (True, 0x00010001, ([],))