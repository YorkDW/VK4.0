from modules.commands.utils import *
from modules.commands.kick import execute_kicks

async def check_ban(box, user_id):
    if base.is_banned(user_id, box.msg.peer_id):
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return True
    return False

async def catch_runner(box, user_id):
    enters = await base.handle_enter(user_id, box.msg.peer_id, int(time.time())+60*60*24)
    count_of_enters = len(enters)
    if count_of_enters == stor.config['MAXENTERS']:
        await send_answer(box, "You will be kicked for any enterance in 24 hours")
    if count_of_enters > stor.config['MAXENTERS']:
        print(enters)
        print('KICK THEM')
        # await execute_kicks(box.api, enters, user_id)
        return True
    return False
    
async def undesirable (box, user_id):
    if user_id<0 and user_id != box.event.group_id:
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return (True, f"Bot was caught at {box.msg.peer_id}", "I am the only bot here")
    if base.check_gate(box.msg.peer_id):                                    # use asyncio here
        await send_answer(box, "Gate is closed")
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return (True, f"User {user_id} kicked by closed gate at {box.msg.peer_id}")
    return (True, f"User {user_id} was welcomed")

@log_and_respond_decorator
async def check_all(box, user_id):
    if not base.verify_chat(box.msg.peer_id):
        return (False, f"New user {user_id} in wrong chat")
    if await check_ban(box, user_id):
        return (True, f"Ban triggered by {user_id}")
    if base.is_chat_admin(user_id, box.msg.peer_id):
        return (True, "Admin entered")
    if await catch_runner(box, user_id):
        return (True, f"Runner {user_id} was caught")
    return await undesirable(box, user_id)
