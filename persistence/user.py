class User:
	def __init__(self, pid, password):
		self.pid = pid
		self.password = password

	# this is obviously dumb!
	@staticmethod
	def get(pid):
		global _users
		return _users[pid]

_users = {
	1863211397: User(1863211397, "|+GF-i):/7Z87_:q"),
	1862483632: User(1862483632, "4i(acJ#OsfDJXr>b")
}
