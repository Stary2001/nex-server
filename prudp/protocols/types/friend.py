import nintendo.nex.common as common
from nintendo.nex.common import DateTime

class MiiV1(common.Data):
	def __init__(self, name, unk1, unk2, data):
		self.name = name
		self.unk1 = unk1
		self.unk2 = unk2
		self.data = data

	def get_name(self):
		return "Mii"
#TODO: pull in Mii from kinnay code
	def streamin(self, stream):
		stream.string(self.name)
		stream.u8(self.unk1)
		stream.u8(self.unk2)
		stream.buffer(self.data)
		#stream.buffer(self.data.build())

	def streamout(self, stream):
		self.name = stream.string()
		self.unk1 = stream.u8()
		self.unk2 = stream.u8()
		self.data = stream.buffer()
		#self.data = miis.MiiData.parse(stream.buffer())
common.DataHolder.register(MiiV1, "MiiV1")

class MiiV2(common.Data):
	def __init__(self, name, unk1, unk2, data, datetime):
		self.name = name
		self.unk1 = unk1
		self.unk2 = unk2
		self.data = data
		self.datetime = datetime

	@staticmethod
	def from_miiv1(mii):
		s = MiiV2.__new__(MiiV2) # Bypass __init__!!!!
		s.name = mii.name
		s.unk1 = mii.unk1
		s.unk2 = mii.unk2
		s.data = mii.data
		s.datetime = DateTime(0)
		return s

	def get_name(self):
		return "Mii"

	def streamin(self, stream):
		stream.string(self.name)
		stream.u8(self.unk1)
		stream.u8(self.unk2)
		stream.buffer(self.data)
		#stream.buffer(self.data.build())
		stream.datetime(self.datetime)

	def streamout(self, stream):
		self.name = stream.string()
		self.unk1 = stream.u8()
		self.unk2 = stream.u8()
		self.data = stream.buffer()
		#self.data = miis.MiiData.parse(stream.buffer())
		self.datetime = stream.datetime()
common.DataHolder.register(MiiV2, "MiiV2")

class FriendMii(common.Data):
	def __init__(self, pid, mii):
		self.pid = pid
		self.mii = mii

	def get_name(self):
		return "FriendMii"
#TODO: pull in Mii from kinnay code
	def streamin(self, stream):
		stream.u32(self.pid)
		self.mii.streamin(stream)

	def streamout(self, stream):
		self.pid = stream.u32()
		self.mii = stream.extract("MiiV2")
common.DataHolder.register(FriendMii, "FriendMii")

class MiiList(common.Data):
	def __init__(self, name, unk1, unk2, mii_data_list):
		self.name = name
		self.unk1 = unk1
		self.unk2 = unk2
		self.mii_data_list = mii_data_list

	def get_name(self):
		return "MiiList"

	def streamin(self, stream):
		raise NotImplementedError("Mii list packing is unimplemented!")

	def streamout(self, stream):
		self.name = stream.string()
		self.unk_bool = stream.bool()
		self.unk_u8 = stream.u8()
		self.mii_data_list = stream.list(stream.buffer)

common.DataHolder.register(MiiList, "MiiList")

class PrincipalBasicInfo(common.Data):
	def __init__(self, pid, nnid, mii, unk):
		self.pid = pid
		self.nnid = nnid
		self.mii = mii
		self.unk = unk

	def get_name(self):
		return "PrincipalBasicInfo"

	def streamin(self, stream):
		stream.u32(self.pid)
		stream.string(self.nnid)
		stream.add(self.mii)
		stream.u8(self.unk)

	def streamout(self, stream):
		self.pid = stream.u32()
		self.nnid = stream.string()
		self.mii = stream.extract(MiiV2)
		self.unk = stream.u8()
common.DataHolder.register(PrincipalBasicInfo, "PrincipalBasicInfo")

class NNAInfo(common.Data):
	def __init__(self, principal_info, unk1, unk2):
		self.principal_info = principal_info
		self.unk1 = unk1
		self.unk2 = unk2

	def get_name(self):
		return "NNAInfo"

	def streamin(self, stream):
		stream.add(self.principal_info)
		stream.u8(self.unk1)
		stream.u8(self.unk2)

	def streamout(self, stream):
		self.principal_info = stream.extract(PrincipalBasicInfo)
		self.unk1 = stream.u8()
		self.unk2 = stream.u8()
common.DataHolder.register(NNAInfo, "NNAInfo")

class GameKey(common.Data):
	def __init__(self, title_id, title_version):
		self.title_id = title_id
		self.title_version = title_version

	def get_name(self):
		return "GameKey"

	def streamin(self, stream):
		stream.u64(self.title_id)
		stream.u16(self.title_version)

	def streamout(self, stream):
		self.title_id = stream.u64()
		self.title_version = stream.u16()
common.DataHolder.register(GameKey, "GameKey")


class NintendoPresenceV1(common.Data):
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

	def get_name(self):
		return "NintendoPresence"

	def streamin(self, stream):
		stream.u32(self.unk_u32_1)
		self.game_key.streamin(stream)
		stream.string(self.message)
		stream.u32(self.unk_u32_2)
		stream.u8(self.unk_u8)
		stream.u32(self.unk_u32_3)
		stream.u32(self.unk_u32_4)
		stream.u32(self.unk_u32_5)
		stream.u32(self.unk_u32_6)
		stream.buffer(self.unk_buffer)

	def streamout(self, stream):
		self.unk_u32_1 = stream.u32()
		self.game_key = stream.extract(GameKey)
		self.message = stream.string()
		self.unk_u32_2 = stream.u32()
		self.unk_u8 = stream.u8()
		self.unk_u32_3 = stream.u32()
		self.unk_u32_4 = stream.u32()
		self.unk_u32_5 = stream.u32()
		self.unk_u32_6 = stream.u32()
		self.unk_buffer = stream.buffer()
common.DataHolder.register(NintendoPresenceV1, "NintendoPresenceV1")

class NintendoPresenceV2(common.Data):
	def __init__(self, unk1, is_online, game_key, unk3, message, unk4, unk5,
				 game_server_id, unk7, pid, gathering_id, data, unk10, unk11, unk12):
		self.unk1 = unk1
		self.is_online = is_online
		self.game_key = game_key
		self.unk3 = unk3
		self.message = message
		self.unk4 = unk4
		self.unk5 = unk5
		self.game_server_id = game_server_id
		self.unk7 = unk7
		self.pid = pid
		self.gathering_id = gathering_id
		self.data = data
		self.unk10 = unk10
		self.unk11 = unk11
		self.unk12 = unk12

	def get_name(self):
		return "NintendoPresence"

	def streamin(self, stream):
		stream.u32(self.unk1)
		stream.u8(self.is_online)
		stream.add(self.game_key)
		stream.u8(self.unk3)
		stream.string(self.message)
		stream.u32(self.unk4)
		stream.u8(self.unk5)
		stream.u32(self.game_server_id)
		stream.u32(self.unk7)
		stream.u32(self.pid)
		stream.u32(self.gathering_id)
		stream.buffer(self.data)
		stream.u8(self.unk10)
		stream.u8(self.unk11)
		stream.u8(self.unk12)

	def streamout(self, stream):
		self.unk1 = stream.u32()
		self.is_online = stream.u8()
		self.game_key = stream.extract(GameKey)
		self.unk3 = stream.u8()
		self.message = stream.string()
		self.unk4 = stream.u32()
		self.unk5 = stream.u8()
		self.game_server_id = stream.u32()
		self.unk7 = stream.u32()
		self.pid = stream.u32()
		self.gathering_id = stream.u32()
		self.data = stream.buffer()
		self.unk10 = stream.u8()
		self.unk11 = stream.u8()
		self.unk12 = stream.u8()
common.DataHolder.register(NintendoPresenceV2, "NintendoPresenceV2")


class PrincipalPreference(common.Data):
	def get_name(self):
		return "PrincipalPreference"

	def streamout(self, stream):
		self.unk1 = stream.bool()
		self.unk2 = stream.bool()
		self.unk3 = stream.bool()
common.DataHolder.register(PrincipalPreference, "PrincipalPreference")


class Comment(common.Data):
	"""This is the status message shown in the friend list"""
	def get_name(self):
		return "Comment"

	def streamout(self, stream):
		self.unk = stream.u8()
		self.text = stream.string()
		self.changed = stream.datetime()
common.DataHolder.register(Comment, "Comment")


class FriendInfo(common.Data):
	def get_name(self):
		return "FriendInfo"

	def streamout(self, stream):
		self.nna_info = stream.extract(NNAInfo)
		self.presence = stream.extract(NintendoPresenceV2)
		self.comment = stream.extract(Comment)
		self.befriended = stream.datetime()
		self.last_online = stream.datetime()
		self.unk = stream.u64()
common.DataHolder.register(FriendInfo, "FriendInfo")


class FriendRequestMessage(common.Data):
	def get_name(self):
		return "FriendRequestMessage"

	def streamout(self, stream):
		self.unk1 = stream.u64()
		self.unk2 = stream.u8()
		self.unk3 = stream.u8()
		self.message = stream.string()
		self.unk4 = stream.u8()
		self.string = stream.string()
		self.game_key = stream.extract(GameKey)
		self.datetime = stream.datetime()
		self.expires = stream.datetime()
common.DataHolder.register(FriendRequestMessage, "FriendRequestMessage")


class FriendRequest(common.Data):
	def get_name(self):
		return "FriendRequest"

	def streamout(self, stream):
		self.principal_info = stream.extract(PrincipalBasicInfo)
		self.message = stream.extract(FriendRequestMessage)
		self.sent = stream.datetime()
common.DataHolder.register(FriendRequest, "FriendRequest")


class FriendRelationship(common.Data):
	def __init__(self, principal_id, friend_code, is_complete):
		self.principal_id = principal_id
		self.friend_code = friend_code
		self.is_complete = is_complete

	def get_name(self):
		return "FriendRelationship"

	def streamin(self, stream):
		stream.u32(self.principal_id)
		stream.u64(self.friend_code)
		stream.bool(self.is_complete)

	def streamout(self, stream):
		self.principal_id = stream.u32()
		self.friend_code = stream.u64()
		self.is_complete = stream.bool()

common.DataHolder.register(FriendRelationship, "FriendRelationship")

class FriendPersistentInfo():
	def __init__(self, unk_u32, unk_u8_1, unk_u8_2, unk_u8_3, unk_u8_4, unk_u8_5, game_key, status, unk_timestamp_1, unk_timestamp_2, unk_timestamp_3):
		self.unk_u32 = unk_u32
		self.unk_u8_1 = unk_u8_1
		self.unk_u8_2 = unk_u8_2
		self.unk_u8_3 = unk_u8_3
		self.unk_u8_4 = unk_u8_4
		self.unk_u8_5 = unk_u8_5
		self.game_key = game_key
		self.status = status
		self.unk_timestamp_1 = unk_timestamp_1
		self.unk_timestamp_2 = unk_timestamp_2
		self.unk_timestamp_3 = unk_timestamp_3

	def get_name(self):
		return "FriendPersistentInfo"

	def streamout(self, stream):
		self.unk_u32 = stream.u32()
		self.unk_u8_1 = stream.u8()
		self.unk_u8_2 = stream.u8()
		self.unk_u8_3 = stream.u8()
		self.unk_u8_4 = stream.u8()
		self.unk_u8_5 = stream.u8()

		self.game_key = stream.extract(GameKey)
		self.status = stream.string()
		self.unk_timestamp_1 = stream.datetime()
		self.unk_timestamp_2 = stream.datetime()
		self.unk_timestamp_3 = stream.datetime()

	def streamin(self, stream):
		stream.u32(self.unk_u32)
		stream.u8(self.unk_u8_1)
		stream.u8(self.unk_u8_2)
		stream.u8(self.unk_u8_3)
		stream.u8(self.unk_u8_4)
		stream.u8(self.unk_u8_5)
		self.game_key.streamin(stream)
		stream.string(self.status)
		stream.datetime(self.unk_timestamp_1)
		stream.datetime(self.unk_timestamp_2)
		stream.datetime(self.unk_timestamp_3)

common.DataHolder.register(FriendPersistentInfo, "FriendPersistentInfo")

class FriendPresence(common.Data):
	def __init__(self, pid, nintendo_presence):
		self.pid = pid
		self.nintendo_presence = nintendo_presence

	def get_name(self):
		return "FriendPresence"

	def streamin(self, stream):
		stream.u32(self.pid)
		self.nintendo_presence.streamin(stream)

	def streamout(self, stream):
		self.pid = stream.u32()
		self.nintendo_presence = stream.extract(NintendoPresenceV1)
common.DataHolder.register(FriendPresence, "FriendPresence")

class FriendPicture:
	def __init__(self, unk_u32, data, timestamp):
		self.unk_u32 = unk_u32
		self.data = data
		self.timestamp = timestamp

	def get_name(self):
		return "FriendPicture"

	def streamin(self, stream):
		raise NotImplementedError("no")

	def streamout(self, stream):
		self.unk_u32 = data.u32()
		self.data = data.buffer()
		self.timestamp = data.datetime()


common.DataHolder.register(FriendPicture, "FriendPicture")

class BlacklistedPrincipal(common.Data):
	def get_name(self):
		return "BlacklistedPrincipal"

	def streamout(self, stream):
		self.principal_info = stream.extract(PrincipalBasicInfo)
		self.game_key = stream.extract(GameKey)
		self.since = stream.datetime()
common.DataHolder.register(BlacklistedPrincipal, "BlacklistedPrincipal")


class PersistentNotification(common.Data):
	def get_name(self):
		return "PersistentNotification"

	def streamout(self, stream):
		self.unk1 = stream.u64()
		self.unk2 = stream.u32()
		self.unk3 = stream.u32()
		self.unk4 = stream.u32()
		self.string = stream.string()
common.DataHolder.register(PersistentNotification, "PersistentNotification")


class PlayedGame(common.Data):
	def __init__(self, game_key, timestamp):
		self.game_key = game_key
		self.timestamp = timestamp

	def get_name(self):
		return "PlayedGame"

	def streamin(self, stream):
		raise NotImplementedError("PlayedGame packing is unimplemented!")

	def streamout(self, stream):
		self.game_key = stream.extract(GameKey)
		self.timestamp = stream.datetime()
common.DataHolder.register(PlayedGame, "PlayedGame")

class MyProfile(common.Data):
	def __init__(self, unk_u8_1, unk_u8_2, unk_u8_3, unk_u8_4, unk_u8_5, unk_u64, unk_string_1, unk_string_2):
		self.unk_u8_1 = unk_u8_1
		self.unk_u8_2 = unk_u8_2
		self.unk_u8_3 = unk_u8_3
		self.unk_u8_4 = unk_u8_4
		self.unk_u8_5 = unk_u8_5
		self.unk_u64 = unk_u64
		self.unk_string_1 = unk_string_1
		self.unk_string_2 = unk_string_2

	def get_name(self):
		return "MyProfile"

	def streamout(self, stream):
		self.unk_u8_1 = stream.u8()
		self.unk_u8_2 = stream.u8()
		self.unk_u8_3 = stream.u8()
		self.unk_u8_4 = stream.u8()
		self.unk_u8_5 = stream.u8()
		self.unk_u64 = stream.u64()
		self.unk_string_1 = stream.string()
		self.unk_string_2 = stream.string()
common.DataHolder.register(MyProfile, "MyProfile")

class NintendoNotificationEventGeneral(common.Data):
	def __init__(self, a, b, c, timestamp, status):
		self.unk_u32_1 = a
		self.unk_u32_2 = b
		self.unk_u32_3 = c
		self.timestamp = timestamp
		self.status = status

	def get_name(self):
		return "NintendoNotificationEventGeneral"

	def streamin(self, stream):
		stream.u32(self.unk_u32_1)
		stream.u32(self.unk_u32_2)
		stream.u32(self.unk_u32_3)
		stream.datetime(self.timestamp)
		stream.string(self.status)

	def streamout(self, stream):
		self.unk_u32_1 = stream.u32()
		self.unk_u32_2 = stream.u32()
		self.unk_u32_3 = stream.u32()
		self.timestamp = stream.datetime()
		self.status = stream.string()
common.DataHolder.register(NintendoNotificationEventGeneral, "NintendoNotificationEventGeneral")
