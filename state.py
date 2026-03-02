# state.py

BOT_RUNNING = True


def stop():
    global BOT_RUNNING
    BOT_RUNNING = False


def resume():
    global BOT_RUNNING
    BOT_RUNNING = True


def is_running():
    return BOT_RUNNING
