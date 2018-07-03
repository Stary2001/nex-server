import asyncio
import time

class Event:
	def __init__(self, cb, timeout, repeat=False, params=None):
		self.cb = cb
		self.timeout = timeout
		self.repeat = repeat
		self.deadline = time.time() + timeout

		if params == None:
			self.params = ()
		else:
			self.params = params
		self.scheduler = None

	def reset(self):
		self.deadline = time.time() + self.timeout

class Scheduler:
	def __init__(self):
		self.running = True
		self.events = []

	def add(self, ev):
		ev.scheudler = self
		self.events.append(ev)

	def remove(self, ev):
		if ev in self.events:
			self.events.remove(ev)

	def stop(self):
		self.running = False
		self.events = []

	async def go(self):
		while self.running:
			for ev in self.events[:]: # This makes a copy - we might alter the list while iterating it.
				if time.time() > ev.deadline:
					ev.cb(ev, *ev.params)
					if ev.repeat:
						ev.reset()
					else:
						self.remove(ev)
			await asyncio.sleep(0.2)