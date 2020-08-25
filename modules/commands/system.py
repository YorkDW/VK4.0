import datetime, requests, logging
from vkwave.bots.utils.uploaders.doc_uploader import DocUploader
from modules.commands.utils import *
from modules.message import send_new

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
async def base_save(box):
    if box.msg.peer_id > 2000000000:
        return (False, "Unable to send base in conversation", "You can't request base here")
    
    uploader = DocUploader(box.api)
    attach = await uploader.get_attachment_from_path(box.msg.peer_id, stor.config['BASEFILE'])
    await send_new(box.api, {"attachment":[attach]}, box.msg.peer_id)
    return (True, "Base saved")

@log_and_respond_decorator
async def base_load(box):
    if not box.msg.attachments or not box.msg.attachments[0].doc:
        return(False, 'Wrong file', 'Wrong file')
    
    basefile = requests.get(box.msg.attachments[0].doc.url)
    with open(stor.config['BASEFILE'], 'wb') as file:
        file.write(basefile.content)
    return (True, "Base loaded", "Base loaded")

@log_and_respond_decorator
async def log_level(box):
    try:
        level = int(box.param)
    except:
        return (False, 'Wrong level', 'Wrong level')
    
    await log_respond(box, f"{stor.vault['admins'][box.msg.from_id]['name']} set logging level to {level}")
    logging.getLogger('base').setLevel(level)
    logging.getLogger('co').setLevel(level)
    
    return (True, f"logging level set to {level}", f"logging level set to {level}")
