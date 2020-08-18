from modules.commands.utils import *
from modules.commands.kick import execute_kicks

async def check_ban(box, user_id):
    if base.is_banned(user_id, box.msg.peer_id):
        await log_respond(box, f"Ban triggered at {box.msg.peer_id} by {user_id}")
        await execute_kicks(box.api, box.msg.peer_id, user_id)
        return True
    return False

async def catch_runner(box, user_id):
    enters = await base.handle_enter(user_id, box.msg.peer_id, int(time.time()))
    count_of_enters = len(enters)
    if count_of_enters == stor.config['MAXENTERS']:
        await send_answer(box, "You will be kicked for any enterance in 24 hours")
    if count_of_enters > stor.config['MAXENTERS']:
        print(enters)
        print('KICK THEM')
        await log_respond(box, f"Runner {user_id} was caught at {box.peer_id-2000000000}")
        # await execute_kicks(box.api, enters, user_id)
        return True
    return False
    
async def undesirable (box, user_id):
    if user_id<0 and user_id != box.event.group_id:
        await log_respond(box, f"Bot was caught at {box.msg.peer_id}", "I am the only bot here")
        await execute_kicks(box.api, box.msg.peer_id, user_id)
    if base.check_gate(box.msg.peer_id):
        await log_respond(box, f"{user_id} kicked by closed gates at {box.msg.peer_id}")
        await execute_kicks(box.api, box.msg.peer_id, user_id)

async def check_all(box, user_id):
    if not verify_chat(chat_id):
        return
    if await check_ban(box, user_id):
        return
    if base.is_chat_admin(user_id, box.msg.peer_id):
        pass
        #return
    if await catch_runner(box, user_id):
        return
    await undesirable(box, user_id)