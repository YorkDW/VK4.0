from modules.commands.utils import *
from modules.message import resend_message

async def talker_handle(box):
    if box.msg.peer_id in stor.talker['targets']:
        user_obj = (await box.api.users.get(user_ids = box.msg.from_id)).response

        first_name = user_obj[0].first_name
        last_name = user_obj[0].last_name
        target_name = stor.vault['chats'].get(box.msg.peer_id, {}).get('name', None)
        if not target_name:
            target_name = box.msg.peer_id - 2*10**9 if box.msg.peer_id > 2*10**9 else box.msg.peer_id

        box.msg.text = f"{target_name}: {first_name} {last_name}\n{box.msg.text}"

        index = stor.talker['targets'].index(box.msg.peer_id)
        destination = stor.talker['consoles'][index]

        await resend_message(box, destination) 

    elif box.msg.peer_id in stor.talker['consoles'] and box.msg.from_id in stor.talker['users']:
        index = stor.talker['consoles'].index(box.msg.peer_id)
        destination = stor.talker['targets'][index]

        await resend_message(box, destination)

@log_and_respond_decorator
async def activate_talker(box):         # TODO add talker for multiple users
    delete_user_session(box.msg.from_id)

    count = len(box.chats) + len(box.targets)
    if count == 0:
        return (False, 'Wrong chat or target', 'Wrong chat or target')
    if count > 1:
        return (False, 'Only one chat or user is allowed', 'Only one chat or user is allowed')

    if box.chats:
        target = box.chats[0]
    else:
        target = box.targets[0]
        allowed = await box.api.messages.is_messages_from_group_allowed(
            group_id = box.event.object.group_id,
            user_id = target
        )
        if not allowed.response.is_allowed:
            return (False, "Messages are not allowed", "Messages are not allowed")

    stor.talker['users'].append(box.msg.from_id)
    stor.talker['consoles'].append(box.msg.peer_id)
    stor.talker['targets'].append(target)

    return (True, "Talker activated", "Talker activated")

@log_and_respond_decorator
async def deactivate_talker(box):
    if not delete_user_session(box.msg.from_id):
        return (False, "Talker is not activated", "Talker is not activated")
    
    return (True, "Talker deactivated", "Talker deactivated")

def delete_user_session(user_id):
    if user_id not in stor.talker['users']:
        return False

    index = stor.talker['users'].index(user_id)
    stor.talker['users'].pop(index)
    stor.talker['consoles'].pop(index)
    stor.talker['targets'].pop(index)
    
    return True
