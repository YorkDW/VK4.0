import random, time

import modules.storage as stor
import modules.basemaster as base
from modules.databox import DataBox
from modules.message import send_new

class st:
    logger:None
    
async def send_answer(box, text):
    send_args = {"message":text}
    await send_new(box.api, send_args, [box.msg.peer_id])

async def log_respond(box, log, answer = False,level=12):
    st.logger.log(level, f" {log}")
    if answer:
        await send_answer(box, answer)

def log_and_respond_decorator(func):
    async def body(*args, **kwargs):
        status_log_answer = await func(*args, **kwargs)
        if any([
            len(args)>0 and not isinstance(args[0], DataBox),
            not isinstance(status_log_answer, tuple),
            len(status_log_answer) not in (2,3)
        ]):
            await log_respond(args, "BOX ERROR", False, 20)
            raise SystemExit

        status, log = status_log_answer[0], status_log_answer[1]
        answer = status_log_answer[2] if len(status_log_answer) == 3 else False
        
        time.perf_counter()
        intro = 'Done:' if status else 'FAIL:'
        level = 12 if status else 14
        work_time = int((time.perf_counter() - args[0].start_time)*1000)
        begin = f"{intro} ({work_time}ms) {func.__name__}{args[1:]}{kwargs if kwargs else ''}"
        peer = args[0].msg.peer_id-2000000000 if args[0].msg.peer_id > 2000000000 else args[0].msg.peer_id
        for_log = f"{begin} from {peer} by {args[0].msg.from_id} - {log}"

        await log_respond(args[0], for_log, answer, level)
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

def str_to_sec(in_str:str): # 1d:24h:33m:44s
    if in_str.isdigit():
        return int(in_str)*60
    time_dict = {'s':1, 'm':60, 'h':60*60, 'd':60*60*24}
    parts = in_str.lower().split(':')
    res = 0
    for part in parts:
        if not part:
            continue
        key = part[-1]
        try:
            res += int(part[:-1])*time_dict[key]
        except:
            return False
    return res
