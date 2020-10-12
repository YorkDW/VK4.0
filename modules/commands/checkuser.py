from modules.commands.utils import *
from modules.commands.kick import execute_kicks
from vkwave.bots.storage.storages.ttl import TTLStorage

def catch_runner(box, user_id):
    if user_id not in stor.vault['enters'].keys():
        stor.vault['enters'][user_id] = {
            'chats':[box.msg.peer_id],
            'times':[int(time.time())]
        }
    else:
        cur_user_enters = stor.vault['enters'][user_id]
        for_delete = []
        time_delete_border = int(time.time() - stor.time_day)
        for num, expire_time in enumerate(cur_user_enters['times']):
            if expire_time < time_delete_border:
                for_delete.append(num)
        for_delete.reverse()
        for num in for_delete:
            cur_user_enters['chats'].pop(num)
            cur_user_enters['times'].pop(num)

    if box.msg.peer_id not in stor.vault['enters'][user_id]['chats']:
        stor.vault['enters'][user_id]['chats'].append(box.msg.peer_id)
        stor.vault['enters'][user_id]['times'].append(int(time.time()))
    
    count_of_enters = len(stor.vault['enters'][user_id]['chats'])

    if count_of_enters == stor.config['MAXENTERS']:
        stor.do(send_answer(box, "You will be kicked for entering any chat in 24 hours"))

    return count_of_enters > stor.config['MAXENTERS']
    

@log_and_respond_decorator
async def check_all(box, user_id):
    if user_id == box.event.object.group_id*-1:
        return (True, f"I'm in")

    if not base.verify_chat(box.msg.peer_id):
        return (False, f"New user in wrong chat")

    if base.is_banned(user_id, box.msg.peer_id):
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return (True, f"Ban was triggered")

    if base.is_chat_admin(box.msg.from_id, box.msg.peer_id):
        return (True, "Under admin's control")

    if user_id<0:
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return (True, f"Bot was caught at {box.msg.peer_id}", "I am the only bot here")

    if base.check_gate(box.msg.peer_id):
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return (True, f"User {user_id} kicked by closed gate at {box.msg.peer_id}", "Gate is closed")

    if catch_runner(box, user_id):
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return (True, f"Runner was caught")

    not_from_target = f"{user_id} " if user_id != box.msg.from_id else ''
    return (True, f"User {not_from_target}welcomed")
