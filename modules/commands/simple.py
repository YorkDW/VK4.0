from modules.commands.utils import *
from modules.commands.kick import execute_kicks
from modules.commands.talker import talker_handle

async def handle_simple_message(box):
    if base.is_muted(box.msg.from_id, box.msg.peer_id):
        if not is_chat_admin(box.msg.from_id, box.msg.peer_id):
            await execute_kicks(box.api, box.msg.peer_id, box.msg.from_id)

    if box.msg.peer_id > 2*10**9:
        if box.msg.peer_id not in stor.vault['chats'].keys():
            await log_respond(box, f"VOID in {box.msg.peer_id-2*10**9} from {box.msg.from_id} - {box.msg.text}")
    
    await talker_handle(box)