import random

EN = [
    "Hey {m}, how are you 😄",
    "{m}, hope you’re doing great 🔥",
    "Yo {m}! Stay awesome 😎"
]

HI = [
    "{m} भाई कैसे हो? 😄",
    "{m} उम्मीद है सब बढ़िया होगा 🔥",
    "{m} आज बड़े शांत लग रहे हो 😄"
]

HINGLISH = [
    "{m} bro kya scene hai 😎",
    "Hey {m}, kaise ho 🔥",
    "{m} aaj mood mast lag raha 😄"
]

FLIRTY = [
    "{m} tum toh group ki jaan ho 😏",
    "Hey {m}, smile kar do 😊",
    "{m} aaj smart lag rahe ho 🔥"
]

def pick(pool, last):
    msg = random.choice(pool)
    while msg == last:
        msg = random.choice(pool)
    return msg
