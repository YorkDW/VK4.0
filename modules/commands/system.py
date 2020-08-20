import datetime
from modules.commands.utils import *

@log_and_respond_decorator
async def uptime(box):
    start = datetime.datetime.fromtimestamp(stor.start_time)
    delta = datetime.datetime.today() - start
    hours, temp = divmod(delta.seconds,3600)
    minutes, seconds = divmod(temp, 60)
    for_send = f"{str(hours).zfill(2)}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"
    if delta.days == 1:
        for_send = f"1 day, {for_send}"
    elif delta.days > 1:
        for_send = f"{delta.days} days, {for_send}"
    return (True, for_send, for_send)

async def stop(box):
    log = f"{box.msg.from_id} used stop"
    await log_respond(box, log, "Stopped")
    stor.asyncio_loop.stop()

@log_and_respond_decorator
async def log(box):
    if box.msg.peer_id > 2000000000:
        return (False, "Unable to send log in conversation", "You can't request logs here")
    try:
        count = int(box.param)
    except:
        return (False, "Wrong param", "Wrong log length")
    
    with open (stor.config['LOGFILE'], 'r') as file:
        lines = file.readlines()

    if count == 0:
        count = len(lines)
    
    answer = ''.join(lines[len(lines)-count:])
    return (True, "Log sended", answer)

@log_and_respond_decorator
async def clear_log(box):
    try:
        count = int(box.param)
    except:
        return (False, "Wrong param", "Wrong log length")
    
    with open (stor.config['LOGFILE'], 'r') as file:
        lines = file.readlines()

    count = int(box.param) if box.param.isdigit() else 0
    
    with open (stor.config['LOGFILE'], 'w') as file:
        file.write(''.join(lines[len(lines)-count:]))

    return (True, "Log was cleared", "Log was cleared")
    
@log_and_respond_decorator
async def base_dump(box):
    if box.msg.peer_id > 2000000000:
        return (False, "Unable to send base dump in conversation", "You can't request dump here")
    return (True, "TODO", "TODO")
    