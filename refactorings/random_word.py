import random
import string
import re

rng = random.Random(0)
with open('words') as f:
    all_words = [re.sub('[^0-9a-zA-Z_]', '', w.strip()) for w in f.read().splitlines()]

def get_random_word():
    return rng.choice(all_words)

def get_random_typename_value():
    return rng.choice((
        ('int', f'{"".join(rng.sample("1234567890", rng.randint(1, 10)))}'),
        ('char', f'\'{rng.choice(string.ascii_letters)}\''),
        ('char *', f'"{get_random_word()}"'),
    ))


