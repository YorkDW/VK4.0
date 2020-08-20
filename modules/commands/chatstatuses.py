import time
from modules.commands.utils import *


async def mute(box, add_or_del, time_ = None):
    func = base.add_mute if add_or_del == "add" else base.del_mute

    if not box.targets:
        box.targets = [0]

    errors = check_zeros({'chats':box.chats})
    if errors:
        return (False, errors, errors)

    fail = 0
    for chat in box.chats:
        for target in box.targets:
            kwargs = {"chat_id":chat, "user_id":target}
            if time_ is not None:
                kwargs.update({"time_":time_})
            status, message = await func(**kwargs)
            if not status:
                fail += 1

    await base.update_vault_chats()
    log = "Done with errors" if fail else "Done"
    return (True, log, log)


    

@log_and_respond_decorator
async def add_mute(box):
    time_delta = str_to_sec(box.param)
    if not time_delta:
        return (False, "Wrong time", "Wrong time")
    _time = int(time.time())+time_delta
    return await mute(box, "add", _time)

@log_and_respond_decorator
async def del_mute(box):
    return await mute(box, "del")


    
async def gate(box, add_or_del, time_ = None):
    func = base.add_gate if add_or_del == "add" else base.del_gate

    errors = check_zeros({'chats':box.chats})
    if errors:
        return (False, errors, errors)

    fail = 0
    for chat in box.chats:
        kwargs = {"chat_id":chat}
        if time_ is not None:
            kwargs.update({"time_":time_})
        status, message = await func(**kwargs)
        if not status:
            fail += 1

    await base.update_vault_chats()
    log = "Done with errors" if fail else "Done"
    return (True, log, log)


@log_and_respond_decorator
async def add_gate(box):
    time_delta = str_to_sec(box.param)
    if not time_delta:
        return (False, "Wrong time", "Wrong time")
    _time = int(time.time())+time_delta
    return await gate(box, "add", _time)

@log_and_respond_decorator
async def del_gate(box):
    return await gate(box, "del")

@log_and_respond_decorator
async def get_chat_statuses(box):
    errors = check_zeros({'chats':box.chats})
    if errors:
        return (False, errors, errors)
    
    answer = []
    for chat in box.chats:

        gate_status = 'open' if stor.vault['chats'][chat]['gate'] == 0 else 'closed'
        answer.append(f"{stor.vault['chats'][chat]['name']} - gate is {gate_status}")

        mutes = []
        for user, time_ in stor.vault['chats'][chat]['mute']:
            mutes.append('all') if user == 0 else mutes.append(f"[id{user}|*id{user}]") 
        
        if mutes:
            answer.append(f"mutes: {', '.join(mutes)}")
        else:
            answer.append("mutes: none")
    
    return (True, answer, '\n'.join(answer))