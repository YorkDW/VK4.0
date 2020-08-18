from modules.commands.utils import *

@log_and_respond_decorator
async def add_chat(box):
    text_list = box.msg.text.split(' ')
    if box.msg.peer_id < 2000000000:
        return (False, "pm was not added", "You can't add this dialog")
    if base.verify_chat(box.msg.peer_id):
        return (False, "Chat already added", "Chat already added")
    c_status, c_message = await base.add_chat(box.msg.peer_id, str(box.msg.peer_id-2000000000))
    if not c_status:
        return (False, message, message)
    if len(text_list) >= 3:
        if text_list[2] in stor.vault['groups'].keys():
            g_status, g_message = await base.add_chat_to_group(box.msg.peer_id, text_list[2])
            if not g_status:
                c_message += f" {g_message}"
    for user in await box.targets:
        if user in stor.vault['admins'].keys():
            a_status, a_message = await base.add_admin_to_chat(box.msg.peer_id, user)
            if not a_status:
                c_message += f" {user} {a_message}"
    await base.update_vault_chats()
    await base.update_vault_groups()
    await base.update_vault_admins()
    return (True, c_message, c_message)

@log_and_respond_decorator
async def del_chat(box):
    status, message = await base.del_chat(box.msg.peer_id)
    await base.update_vault_all()
    return (status, message, message)

@log_and_respond_decorator
async def add_admin(box):
    if len(await box.targets)==0:
        return (False, "Wrong admin", "Choose admin")
    func = base.add_admin
    if (await box.targets)[0] in stor.vault['admins'].keys():
        func = base.update_admin
        # return (False, "Admin already added", "Admin already added")
    if not str(box.param).isdigit():
        return (False, "Wrong level", "Choose level")
    if not int(box.param) in (1,2,3,4):
        return (False, "Wrong level", "Level must be from 1 to 4")
    status, message = await func((await box.targets)[0], int(box.param), str((await box.targets)[0]))
    await base.update_vault_admins()
    return (status, message, message)

@log_and_respond_decorator
async def del_admin(box):
    if len(await box.targets) == 0:
        return (False, "Wrong admin", "Choose admin")
    if (await box.targets)[0] not in stor.vault['admins'].keys():
        return (False, "No such admin", "Target is not an admin")
    status, message = await base.del_admin((await box.targets)[0])
    await base.update_vault_all()
    return (status, message, message)
    