import random

import modules.storage as stor
import modules.basemaster as base
from modules.databox import DataBox

class st:
    logger:None

async def send_message(api, send_args:dict):
    send_args.update({"random_id":random.randint(50000,2000000000)})
    await api.messages.send(**send_args)
    
async def send_answer(box, text):
    send_args = {"peer_id":box.msg.peer_id, "message":text}
    await send_message(box.api, send_args)

async def log_respond(box, log, answer = False,level=12):
    st.logger.log(level, f" {log}")
    if answer:
        await send_answer(box, answer)

def log_and_respond_decorator(func):
    async def body(*args, **kwargs):
        status, log, answer = await func(*args, **kwargs)

        intro = 'Done:' if status else 'FAIL:'
        level = 12 if status else 14
        log_for_send = f"{intro} {func.__name__}{args}{kwargs} - {log}"

        if len(args)>0 and isinstance(args[0], DataBox):
            await log_respond(args[0], log_for_send, answer, level)
        else:
            print('ERROR')
            raise SystemExit
        return (status, log, answer)
    return body

def check_zeros(name_and_val):
    res = []
    for key, value in name_and_val.items():
        if not value:
            res.append(f"Wrong {key}")
    return False if not res else ', '.join(res)

def get_stat(ex_res:list):
    errors = 0
    for elem in ex_res:
        if isinstance(elem, bool) and elem == False:
            errors += 1
    return f"{len(ex_res)-errors}/{len(ex_res)}"