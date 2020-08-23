from modules.commands.utils import *
from modules.commands.kick import execute_kicks

async def check_ban(box, user_id):
    if base.is_banned(user_id, box.msg.peer_id):
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return True
    return False

async def catch_runner(box, user_id):
    if user_id not in stor.vault['enters'].keys():
        stor.vault['enters'][user_id] = {
            'chats':[box.msg.peer_id],
            'times':[int(time.time())+stor.time_day]
        }
    else:
        cur_user_enters = stor.vault['enters'][user_id]
        for_delete = []
        for num, expire_time in enumerate(cur_user_enters['times']):
            if expire_time < time.time():
                for_delete.append(num)
        for num in for_delete:
            cur_user_enters['chats'].pop(num)
            cur_user_enters['times'].pop(num)

    if box.msg.peer_id not in stor.vault['enters'][user_id]['chats']:
        stor.vault['enters'][user_id]['chats'].append(box.msg.peer_id)
        stor.vault['enters'][user_id]['times'].append(int(time.time())+stor.time_day)
    
    count_of_enters = len(stor.vault['enters'][user_id]['chats'])

    if count_of_enters == stor.config['MAXENTERS']:
        await send_answer(box, "You will be kicked for any enterance in 24 hours")
    if count_of_enters > stor.config['MAXENTERS']:
        await execute_kicks(box.api, stor.vault['enters'][user_id]['chats'], user_id)

    await base.handle_enter(user_id, box.msg.peer_id, int(time.time())+stor.time_day)

    return count_of_enters > stor.config['MAXENTERS']

    
async def undesirable (box, user_id):
    if user_id<0:
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return (True, f"Bot was caught at {box.msg.peer_id}", "I am the only bot here")
    if base.check_gate(box.msg.peer_id):                                    # use asyncio here
        await send_answer(box, "Gate is closed")
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return (True, f"User {user_id} kicked by closed gate at {box.msg.peer_id}")
    return (True, f"User {user_id} was welcomed")

@log_and_respond_decorator
async def check_all(box, user_id):
    if user_id == box.event.object.group_id*-1:
        return (True, f"I'm in")
    if not base.verify_chat(box.msg.peer_id):
        return (False, f"New user {user_id} in wrong chat")
    if await check_ban(box, user_id):
        return (True, f"Ban triggered by {user_id}")
    if base.is_chat_admin(box.msg.from_id, box.msg.peer_id):
        return (True, "Under admin's control")
    if await catch_runner(box, user_id):
        return (True, f"Runner {user_id} was caught")
    return await undesirable(box, user_id)
