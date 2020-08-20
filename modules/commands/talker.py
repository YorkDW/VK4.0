from modules.commands.utils import *
from modules.message import resend_message

async def talker_handle(box):
    if box.msg.peer_id == stor.talker['target']:
        user_obj = (await box.api.users.get(user_ids = box.msg.from_id)).response
        first_name = user_obj[0].first_name
        last_name = user_obj[0].last_name
        target = box.msg.peer_id-2*10**9 if box.msg.peer_id > 2*10**9 else box.msg.peer_id
        box.msg.text = f"{target} : {first_name} {last_name}\n{box.msg.text}"
        await resend_message(box, stor.talker['console']) 
    elif box.msg.peer_id == stor.talker['console'] and box.msg.from_id == stor.talker['user']:
        await resend_message(box, stor.talker['target'])

@log_and_respond_decorator
async def activate_talker(box):         # TODO add talker for multiple users
    errors = check_zeros({'chats':box.chats})
    if errors:
        return (False, errors, errors)

    stor.talker['console'] = box.msg.peer_id
    stor.talker['user'] = box.msg.from_id
    stor.talker['target'] = box.chats[0]

    return (True, "Talker activated", "Talker activated")

@log_and_respond_decorator
async def deactivate_talker(box):
    if stor.talker['user'] == 0:
        return (False, "Talker is not activated", "Talker is not activated")

    stor.talker['console'] = 0
    stor.talker['user'] = 0
    stor.talker['target'] = 0
    
    return (True, "Talker deactivated", "Talker deactivated")