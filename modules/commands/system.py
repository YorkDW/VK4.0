import datetime, requests, logging
from vkwave.bots.utils.uploaders.doc_uploader import DocUploader
from modules.commands.utils import *
from modules.message import send_new

@log_and_respond_decorator
async def uptime(box):
    start = datetime.datetime.fromtimestamp(stor.start_time)
    delta = datetime.datetime.now() - start
    answer = str(delta)[:str(delta).rfind('.')]
    return (True, answer, answer)

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
async def log_level(box): # add loglevel param in conig
    try:
        level = int(box.param)
    except:
        answer = f"Current logging level is {logging.getLogger('base').level}"
        return (True, answer, answer)
    
    await log_respond(box, f"{stor.vault['admins'][box.msg.from_id]['name']} set logging level to {level}")
    logging.getLogger('base').setLevel(level)
    logging.getLogger('co').setLevel(level)
    
    return (True, f"logging level set to {level}", f"logging level set to {level}")

@log_and_respond_decorator
async def get_admins(box):
    await base.update_vault_admins()

    res = []
    for admin_id, data in stor.vault['admins'].items():
        block = []
        if box.targets:
            if admin_id not in box.targets:
                continue
        block.append(f"{data['name']}: [id{admin_id}|*id{admin_id}], level: {data['level']}")

        chat_list = []
        for chat in data['chats']:
            if chat != 0:
                chat_list.append(stor.vault['chats'][chat]['name'])
            else:
                chat_list.append('all')
        block.append("chats: " + ', '.join(chat_list))

        targets = []
        for i in range(len(data['targets']['users'])):
            user = f"[id{data['targets']['users'][i]}|*id{data['targets']['users'][i]}]"
            time_ = datetime.datetime.now()-datetime.datetime.fromtimestamp(data['targets']['times'][i])
            targets.append(f"{user}: {str(time_)[:str(time_).rfind('.')]}")
        block.append("targets:"+'\n'.join(targets))
        res.append('\n'.join(block))

    if not res:
        return (False, "Empty list", "Empty list")

    return (True, "Responded", '\n\n'.join(res))

@log_and_respond_decorator
async def get_banlist(box):
    everywhere = []
    others = []
    for user_id, chats in stor.vault['banlist'].items():
        if 0 in chats:
            everywhere.append(f"[id{user_id}|{user_id}]")
        if 0 not in chats or len(chats)>1:
            banned_chats = []
            for chat_id in chats:
                if not chat_id:
                    continue
                banned_chats.append(stor.vault['chats'][chat_id]['name'])
            others.append(f"[id{user_id}|{user_id}]: {', '.join(banned_chats)}")
    everywhere_str = f"everywhere: {', '.join(everywhere)}"
    other_str ='\n'.join(others)
    return (True, "Responded", everywhere_str + '\n' + other_str)
                


