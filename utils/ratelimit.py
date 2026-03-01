import time

RATE_LIMIT = {}  # {(chat_id, user_id): last_timestamp}
LIMIT_SECONDS = 3

def check_rate(chat_id: int, user_id: int) -> bool:
    key = (chat_id, user_id)
    now = time.time()

    last = RATE_LIMIT.get(key, 0)
    if now - last < LIMIT_SECONDS:
        return False

    RATE_LIMIT[key] = now
    return True
