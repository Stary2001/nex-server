from .basic import Type, BasicU8, BasicU32, BasicU64, String, Bool, Buffer, ListBuffer, ListType, NEXDateTime
import struct

class Mii:
	def __init__(self, name, unk_bool, unk_u8, mii_data):
		self.name = name
		self.unk_bool = unk_bool
		self.unk_u8 = unk_u8
		self.mii_data = mii_data

class MiiType(Type):
	def __init__(self):
		super().__init__("Mii")

	def pack(self, to_pack):
		raise NotImplementedError("Mii packing is unimplemented!")

	def unpack(self, to_unpack):
		name, name_len = String.unpack(to_unpack)
		unk_bool, _ = Bool.unpack(to_unpack[name_len:])
		unk_u8, _ = BasicU8.unpack(to_unpack[name_len + 1:])
		mii_data, mii_data_len = Buffer.unpack(to_unpack[name_len + 2:])
		return Mii(name, unk_bool, unk_u8, mii_data), name_len + 2 + mii_data_len

class MiiList:
	def __init__(self, name, unk_bool, unk_u8, mii_data_list):
		self.name = name
		self.unk_bool = unk_bool
		self.unk_u8 = unk_u8
		self.mii_data_list = mii_data_list

class MiiListType(Type):
	def __init__(self):
		super().__init__("MiiList")

	def pack(self, to_pack):
		raise NotImplementedError("Mii list packing is unimplemented!")

	def unpack(self, to_unpack):
		name, name_len = String.unpack(to_unpack)
		unk_bool, unk_bool_len = Bool.unpack(to_unpack[name_len:])
		unk_u8, _ = BasicU8.unpack(to_unpack[name_len + 1:])
		mii_data_list, mii_data_list_len = ListBuffer.unpack(to_unpack[name_len + 2:])

		return MiiList(name, unk_bool, unk_u8, miis), name_len + 2 + mii_data_list_len

class FriendRelationship:
	def __init__(self, unk_u32, unk_u64, unk_u8):
		self.unk_u32 = unk_u32
		self.unk_u64 = unk_u64
		self.unk_u8 = unk_u8

class FriendRelationshipType(Type):
	def __init__(self):
		super().__init__("FriendRelationship")

	def pack(self, to_pack):
		raise NotImplementedError("FriendRelationship packing is unimplemented!")

	def unpack(self, to_unpack):
		raise NotImplementedError("FriendRelationship unpacking is unimplemented!")

class PlayedGame:
	def __init__(self, game_key, timestamp):
		self.game_key = game_key
		self.timestamp = timestamp

class PlayedGameType(Type):
	def __init__(self):
		super().__init__("PlayedGame")

	def pack(self, to_pack):
		raise NotImplementedError("PlayedGame packing is unimplemented!")
	
	def unpack(self, to_unpack):
		game_key, game_key_len = GameKey_Instance.unpack()
		timestamp = NEXDateTime.unpack(to_unpack[game_key_len:])

class GameKey:
	def __init__(self, title_id, title_version):
		self.title_id = title_id
		self.title_version = title_version

class GameKeyType(Type):
	def __init__(self):
		super().__init__("GameKey")

	def pack(self, to_pack):
		raise NotImplementedError("GameKey packing is unimplemented!")
	
	def unpack(self, to_unpack):
		tid, version = struct.unpack("<QH", to_unpack[:10])
		return GameKey(tid, version), 10

class FriendsPresence:
	def __init__(self, unk_u32_1, game_key, message, unk_u32_2, unk_u8, unk_u32_3, unk_u32_4, unk_u32_5, unk_u32_6, unk_buffer):
		self.unk_u32_1 = unk_u32_1
		self.game_key = game_key
		self.message = message
		self.unk_u32_2 = unk_u32_2
		self.unk_u8 = unk_u8
		self.unk_u32_3 = unk_u32_3
		self.unk_u32_4 = unk_u32_4
		self.unk_u32_5 = unk_u32_5
		self.unk_u32_6 = unk_u32_6
		self.unk_buffer = unk_buffer

class FriendsPresenceType(Type):
	def __init__(self):
		super().__init__("FriendsPresence")

	def pack(self, to_pack):
		raise NotImplementedError("FriendsPresence packing is unimplemented!")
	
	def unpack(self, to_unpack):
		print("FriendsPresence", len(to_unpack))

		unk_u32_1, _ = BasicU32.unpack(to_unpack)
		game_key, game_key_len = GameKey_Instance.unpack(to_unpack[4:])
		message, message_len = String.unpack(to_unpack[4+game_key_len:])
		unk_u32_2, _ = BasicU32.unpack(to_unpack[game_key_len+message_len+4:])
		unk_u8, _ = BasicU8.unpack(to_unpack[game_key_len+message_len+8:])
		unk_u32_3, _ = BasicU32.unpack(to_unpack[game_key_len+message_len+9:])
		unk_u32_4, _ = BasicU32.unpack(to_unpack[game_key_len+message_len+13:])
		unk_u32_5, _ = BasicU32.unpack(to_unpack[game_key_len+message_len+17:])
		unk_u32_6, _ = BasicU32.unpack(to_unpack[game_key_len+message_len+21:])
		unk_buffer, buffer_len = Buffer.unpack(to_unpack[game_key_len+message_len+25:])
		print(unk_buffer, buffer_len)
		return FriendsPresence(
			unk_u32_1,
			game_key,
			message,
			unk_u32_2,
			unk_u8,
			unk_u32_3,
			unk_u32_4,
			unk_u32_5,
			unk_u32_6,
			unk_buffer), 25 + game_key_len + message_len + buffer_len

class FriendsProfile:
	def __init__(self, unk_u8_1, unk_u8_2, unk_u8_3, unk_u8_4, unk_u8_5, unk_u64, unk_string_1, unk_string_2):
		self.unk_u8_1 = unk_u8_1
		self.unk_u8_2 = unk_u8_2
		self.unk_u8_3 = unk_u8_3
		self.unk_u8_4 = unk_u8_4
		self.unk_u8_5 = unk_u8_5

		self.unk_u64 = unk_u64
		self.unk_string_1 = unk_string_1
		self.unk_string_2 = unk_string_2

class FriendsProfileType(Type):
	def __init__(self):
		super().__init__("FriendsProfile")

	def pack(self, to_pack):
		raise NotImplementedError("FriendsProfile packing is unimplemented!")
	
	def unpack(self, to_unpack):
		unk_u8_1, _ = BasicU8.unpack(to_unpack)
		unk_u8_2, _ = BasicU8.unpack(to_unpack[1:])
		unk_u8_3, _ = BasicU8.unpack(to_unpack[2:])
		unk_u8_4, _ = BasicU8.unpack(to_unpack[3:])
		unk_u8_5, _ = BasicU8.unpack(to_unpack[4:])

		unk_u64, _ = BasicU64.unpack(to_unpack[5:])
		unk_string_1, unk_string_1_len = String.unpack(to_unpack[13:])
		unk_string_2, unk_string_2_len = String.unpack(to_unpack[13 + unk_string_1_len:])

		return FriendsProfile(unk_u8_1, unk_u8_2, unk_u8_3, unk_u8_4, unk_u8_5, unk_u64, unk_string_1, unk_string_2), 13 + unk_string_1_len + unk_string_2_len

Mii_Instance = MiiType()
MiiList_Instance = MiiListType()

FriendRelationship_Instance = FriendRelationshipType()
ListFriendRelationship = ListType(FriendRelationship_Instance)

PlayedGame_Instance = PlayedGameType()
ListPlayedGame = ListType(PlayedGame_Instance)

GameKey_Instance = GameKeyType()

FriendsPresence_Instance = FriendsPresenceType()

FriendsProfile_Instance = FriendsProfileType()