from random import choice
from string import ascii_letters


def key_generator():
    return ''.join(choice(ascii_letters) for i in range(24))
