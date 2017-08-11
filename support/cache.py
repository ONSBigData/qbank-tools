import hashlib
import queue


class Cache:
    MAX_ITEMS = 1000

    def __init__(self):
        self.cache = {}
        self.keys = queue.Queue()

    def _hash_key(self, key):
        return hashlib.md5(key.encode()).hexdigest()

    def store(self, key, item):
        key = self._hash_key(key)

        self.keys.put(key)
        if self.keys.qsize() > self.MAX_ITEMS:
            key_to_rem = self.keys.get()
            del self.cache[key_to_rem]

        self.cache[key] = item

    def retrieve(self, key):
        key = self._hash_key(key)

        if key in self.cache:
            return self.cache[key]

        return None
