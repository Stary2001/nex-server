from prudp.protocols import incoming,outgoing

class AuthenticationProtocol:
	def __init__(self):
		self.methods = {}
		self.methods[1] = self.login

	@incoming('string')
	@outgoing('u32', 'u32', 'u8[*]', 'string', 'u8[]', 'string')
	def login(self, device_id):
		print("LOGIN!!!!!", device_id)

		result = 0
		user_id = 0
		return (result, user_id, b't o k e n', 'connection_string_blah_blah', b'\x00'*7, 'idk_unk_blah')