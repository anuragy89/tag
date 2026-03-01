tag_state = {}

def stop(chat_id):
    tag_state[chat_id] = False

def resume(chat_id):
    tag_state[chat_id] = True

def allowed(chat_id):
    return tag_state.get(chat_id, True)
