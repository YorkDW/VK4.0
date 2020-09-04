import json
from modules.commands.utils import *

async def save_config():
    with open(stor.config['CONFIG'], "r") as file:
        for_save = json.load(file)
    
    for key in for_save.keys():
        if key not in ('LOGFILE', 'BASEFILE'):
            for_save[key] = stor.config[key]

    with open(stor.config['CONFIG'], "w", encoding="utf-8") as file:
        json.dump(for_save, file, ensure_ascii = False, indent = 2)

    return True

@log_and_respond_decorator
async def set_target_count(box):
    if not box.param.isdigit():
        answer = f"Current target count is {stor.config['MAXTARGETS']}"
        return (True, answer, answer)
    stor.config['MAXTARGETS'] = int(box.param)
    await save_config()
    log = f"Target count set to {box.param}"
    return (True, log, log)

@log_and_respond_decorator
async def set_enter_count(box):
    if not box.param.isdigit():
        answer = f"Current catch count is {str(stor.config['MAXENTERS'])}"
        return (True, answer, answer)
    stor.config['MAXENTERS'] = int(box.param)
    await save_config()
    log = f"Enter count set to {box.param}"
    return (True, log, log)

@log_and_respond_decorator
async def get_target_count(box):
    if box.admin_level > 2:
        return (True, "All", "Do what ever you want")

    result = stor.config['MAXTARGETS']
    cur_targets = stor.vault['admins'][box.msg.from_id]['targets']
    for num, target in enumerate(cur_targets['users']):
        if cur_targets['times'][num] > time.time():
            result -= 1

    answer = f"You have {result} target slot{'' if result==1 else 's'}"
    return (True, f"{result} targets free", answer)

@log_and_respond_decorator
async def log_level(box): # add loglevel param in conig
    try:
        level = int(box.param)
    except:
        answer = f"Current logging level is {stor.config['LOGLEVEL']}"
        return (True, answer, answer)
    
    await log_respond(box, f"{stor.vault['admins'][box.msg.from_id]['name']} set logging level to {level}")
    logging.getLogger('base').setLevel(level)
    logging.getLogger('co').setLevel(level)
    stor.config['LOGLEVEL'] = level
    await save_config()
    
    return (True, f"logging level set to {level}", f"logging level set to {level}")
    

        