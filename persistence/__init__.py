import sqlite3
from prudp.protocols.types import FriendRelationship, FriendPersistentInfo, GameKey, FriendMii, MiiV2, FriendPresence, NintendoPresenceV1
from nintendo.nex.common import DateTime

_user_cache = {}

_db_conn = sqlite3.connect('friends.db')
_db_cursor = _db_conn.cursor()

_db_cursor.execute("""create table if not exists users (pid int, password text)""")
_db_cursor.execute("""create table if not exists friends (our_pid int, our_lfcs text, other_pid int, confirmed bool)""")

if len(_db_cursor.execute("select * from users").fetchall()) == 0:
	_db_cursor.execute("insert into users (pid, password) values (?, ?)", (1863211397, "|+GF-i):/7Z87_:q"))
	_db_cursor.execute("insert into users (pid, password) values (?, ?)", (1862483632, "4i(acJ#OsfDJXr>b"))
	_db_conn.commit()

class User:
	def __init__(self, pid, password):
		self.pid = pid
		self.password = password
		self.presence = None
		data = b'\x90\x00\x84\x88@\xd2\x8a\xe1\xc3\xb0\x15\xdc\xf6V\xafM,]\xd7W\x01\xaa\xeb\xe8oM\xc1\xe2\x7fc\xcd`\xbc\xb1\xc0\xeaY \x85\xab\xf7\xf6\xc3\xbf*\xd2vr\xdcD\xf5\x80\xc6!\x19\x1e\n$6\xc6R\xce\x19P1\x07\xeadY-\xb4\x15\x8a\xd6\xd7\xe0\xbf\xdd0jj\xc6\x07\xc4;\xfe\\P\xb3t\xba\xfa\xd7\xd0\x8c\xf4\x9d_\xbd\x99\xb6p\x95\xc2<\xb9\x9aj\xd1F\xfe\xaa'
		self.mii = MiiV2("not jaames", 0, 0, data, DateTime(0))
		self.persistent_info = FriendPersistentInfo(self.pid, 0, 1, 0, 0, 0, GameKey(1125899907046656, 0), "Meme Maker", DateTime(6), DateTime(7), DateTime(8))

	@staticmethod
	def get(pid):
		global _db_cursor, _db_conn, _user_cache
		if pid in _user_cache:
			return _user_cache[pid]

		row = _db_cursor.execute("select * from users where pid=?", (pid,)).fetchone()
		if row == None:
			return None
		u = User(*row)
		_user_cache[pid] = u
		return u

	@staticmethod
	def get_friend_pids(pid):
		global _db_cursor
		rows = _db_cursor.execute("select other_pid from friends where our_pid=?", (pid,)).fetchall()
		print(rows)
		return list(map(lambda a: a[0], rows))

	def add_friend(self, our_lfcs, other_pid):
		global _db_cursor, _db_conn
		# Did someone already add us?
		existing_request = _db_cursor.execute("select * from friends where our_pid=? and other_pid=? and confirmed=0", (other_pid, self.pid)).fetchone()
		if existing_request == None:
			_db_cursor.execute("insert into friends (our_pid, our_lfcs, other_pid, confirmed) values (?,?,?,?)", (self.pid, str(our_lfcs), other_pid, False))
			_db_conn.commit()
			return FriendRelationship(other_pid, 0, False)
		else:
			if existing_request[2] == True:
				# Wtf?
				pass
			else:
				_db_cursor.execute("insert into friends (our_pid, our_lfcs, other_pid, confirmed) values (?,?,?,?)", (self.pid, str(our_lfcs), other_pid, True))
				_db_cursor.execute("update friends set confirmed=1 where our_pid=? and other_pid=?", (other_pid, self.pid))
				_db_conn.commit()
				row = _db_cursor.execute("select our_pid, our_lfcs, confirmed from friends where our_pid=? and other_pid=?", (other_pid, self.pid)).fetchone()
				return FriendRelationship(row[0], int(row[1]), row[2])

	def remove_friend(self, other_pid):
		global _db_cursor, _db_conn
		# If there is a completed friend relationship (flag=1), un-complete it.
		completed_relationship = _db_cursor.execute("select * from friends where our_pid=? and other_pid=? and confirmed=1", (self.pid, other_pid)).fetchone()
		if completed_relationship != None:
			# Reset the _other_ side of the relationship.
			_db_cursor.execute("update friends set confirmed=0 where our_pid=? and other_pid=?", (other_pid, self.pid))
			_db_conn.commit()
		# Delete!
		_db_cursor.execute("delete from friends where our_pid=? and other_pid=?", (self.pid, other_pid))
		_db_conn.commit()

	def get_friend_relationships(self, filter=None):
		global _db_cursor, _db_conn
		if filter != None:
			filter_str = f'({",".join(map(str,filter))})'
			all_friends = _db_cursor.execute(f"select our_pid, our_lfcs, confirmed from friends where our_pid in {filter_str} and other_pid=?", (self.pid,)).fetchall()
		else:
			all_friends = _db_cursor.execute("select our_pid, our_lfcs, confirmed from friends where other_pid=?", (self.pid,)).fetchall()

		relationships = []
		for f in all_friends:
			print(f)
			relationships.append(FriendRelationship(f[0], int(f[1]), f[2])) # Skip other_pid because it's always our pid here.
		return relationships

	def get_friend_persistent_info(self):
		return self.persistent_info
	
	def get_mii(self):
		return FriendMii(self.pid, self.mii)

	def get_presence(self):
		if self.presence == None:
			return None
		else:
			return FriendPresence(self.pid, self.presence)