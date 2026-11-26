import random

# Drawn while the module loads, before the seeded rebinding: differs on every run (#359).
TOKEN = random.randint(1, 10**9)
