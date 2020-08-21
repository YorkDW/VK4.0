from modules.commands.utils import *

@log_and_respond_decorator
async def add_chat(box):  # add a selection option for chat
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
    for user in box.targets:
        if user in stor.vault['admins'].keys():
            a_status, a_message = await base.add_admin_to_chat(box.msg.peer_id, user)
            if not a_status:
                c_message += f" {user} {a_message}"
    await base.update_vault_all()
    return (True, c_message, c_message)

@log_and_respond_decorator
async def del_chat(box): # add a selection option for chat
    status, message = await base.del_chat(box.msg.peer_id)
    await base.update_vault_all()
    return (status, message, message)

@log_and_respond_decorator
async def add_admin(box):
    if len(box.targets)==0:
        return (False, "Wrong admin", "Choose admin")
    func = base.add_admin
    if box.targets[0] in stor.vault['admins'].keys():
        func = base.update_admin
        # return (False, "Admin already added", "Admin already added")
    if not box.param.isdigit():
        return (False, "Wrong level", "Choose level")
    if not int(box.param) in (1,2,3,4):
        return (False, "Wrong level", "Level must be from 1 to 4")
    status, message = await func(box.targets[0], int(box.param), str(box.targets[0]))
    await base.update_vault_admins()
    return (status, message, message)

@log_and_respond_decorator
async def del_admin(box):
    if len(box.targets) == 0:
        return (False, "Wrong admin", "Choose admin")
    if box.targets[0] not in stor.vault['admins'].keys():
        return (False, "No such admin", "Target is not an admin")
    status, message = await base.del_admin(box.targets[0])
    await base.update_vault_all()
    return (status, message, message)

@log_and_respond_decorator
async def add_group(box):
    text_list = box.msg.text.split(' ')
    if len(text_list)<3:
        return (False, "Wrong name", "Choose name")
    if text_list[2] in stor.vault['groups'].keys():
        return (False, "Group already exists", "Group already exists")
    status, answer = await base.add_group(text_list[2])
    await base.update_vault_groups()
    return (status, answer, answer)

@log_and_respond_decorator
async def del_group(box):
    text_list = box.msg.text.split(' ')
    if len(text_list)<3:
        return (False, "Wrong name", "Choose name")
    if text_list[2] not in stor.vault['groups'].keys():
        return (False, "Group is not exists", "Group is not exists")
    status, answer = await base.del_group(text_list[2])
    await base.update_vault_groups()
    return (status, answer, answer)

async def admin_and_chat(box, add_or_delet):
    if add_or_delet not in ("add", "delet"):
        return (False, "WRONG ADD_OR_DELET NAME", "Internal error")
    func = base.add_admin_to_chat if add_or_delet=="add" else base.del_admin_from_chat
    
    errors = check_zeros({"Admin":box.targets, "Chats":box.chats})
    if errors:
        return (False, errors, errors)
    
    completed = 0
    add_errors = []
    for chat in box.chats:
        status, answer = await func(chat, box.targets[0])
        if status:
            completed += 1
        else:
            add_errors.append(answer)
    await base.update_vault_admins()
    log = ", ".join(add_errors) if add_errors else f"{add_or_delet}ed"
    return (completed != 0, log, f"{add_or_delet}ed {completed}/{len(box.chats)}")

@log_and_respond_decorator
async def add_admin_to_chat(box):
    return await admin_and_chat(box, "add")

@log_and_respond_decorator
async def del_admin_from_chat(box):
    return await admin_and_chat(box, "delet")

async def chat_and_group(box, add_or_delet):
    func = base.add_chat_to_group if add_or_delet=="add" else base.del_chat_from_group

    text_list = box.msg.text.split(' ')
    if len(text_list)<3:
        return (False, "Wrong name", "Choose name")
    if text_list[2] not in stor.vault['groups'].keys():
        return (False, "Group is not exists", "Group is not exists")
    if len(box.chats) == 0:
        return (False, "Wrong chats", "Wrong chats")
    

    status, answer = await func(box.msg.peer_id, text_list[2])
    await base.update_vault_groups()
    return (status, answer, answer)

@log_and_respond_decorator
async def add_chat_to_group(box):
    return await chat_and_group(box, "add")

@log_and_respond_decorator
async def del_chat_from_group(box):
    return await chat_and_group(box, "delet")