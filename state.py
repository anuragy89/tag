# utils/state.py

TAG_STATE = {}  # chat_id -> True / False


def start_tag(chat_id: int):
    TAG_STATE[chat_id] = True


def stop_tag(chat_id: int):
    TAG_STATE[chat_id] = False


def is_running(chat_id: int) -> bool:
    return TAG_STATE.get(chat_id, False)
