from prudp.protocols import incoming,outgoing
import struct
from binascii import unhexlify,hexlify

class MatchmakingExtensionProtocol:
	def __init__(self, client):
		self.client = client
		self.server = client.server

		self.methods = {}
		self.methods[0x16] = self.FindCommunityByParticipant

	@incoming("u32")
	@outgoing("u32", "u32")
	def FindCommunityByParticipant(self, pid):
		success = True
		result = 0x00010001
		return (success, result, (result, 0x0))