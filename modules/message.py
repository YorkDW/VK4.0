import random

from vkwave.bots.utils.uploaders.photo_uploader import PhotoUploader
from vkwave.bots.utils.uploaders.doc_uploader import DocUploader
from vkwave.vkscript import execute
from vkwave.types.objects import (
    MessagesMessageAttachment,
    MessagesMessageAttachmentType,
    PhotosPhoto,
    DocsDoc
)

import modules.storage as stor 


async def handle_photo(photo:PhotosPhoto, api):
    max_height = 0
    max_width = 0
    better_size = None
    for each in photo.sizes:
        if each.height >= max_height and each.width >= max_width:
            max_height = each.height
            each.width = max_width
            better_size = each
    uploader = PhotoUploader(api)
    return await uploader.get_attachment_from_link(peer_id=2000000001, link = better_size.url)

async def handle_doc(doc:DocsDoc, api): #do not work
    return False
    uploader = DocUploader(api)
    return await uploader.get_attachment_from_link(peer_id=2000000001, link = doc.url, title='test.test')

async def handle_simple_attach(attach):
    type_ = attach.type.value
    owner_id = attach.__getattribute__(type_).owner_id
    attach_id = attach.__getattribute__(type_).id
    return f"{type_}{owner_id}_{attach_id}"

async def handle_attachmen(attach:MessagesMessageAttachment, api):
    if attach.type == MessagesMessageAttachmentType.PHOTO:
        return await handle_photo(attach.photo, api)
    if attach.type == MessagesMessageAttachmentType.DOC:
        return await handle_doc(attach.doc, api)
    if attach.type in (
        MessagesMessageAttachmentType.POLL,
    ):
        return await handle_simple_attach(attach)
    return False

# update, add request for full msg if possible
async def get_message_resend_dict(api, msgs):
    if not isinstance(msgs, (list, tuple)):
        msgs = [msgs]
    resend_dict = {"message":"", 'attachment':[]}
    for msg in msgs:
        if not msg:
            continue
        if msg.text:
            resend_dict['message'] += "\n" + msg.text if len(resend_dict['message']) > 0 else msg.text
        if msg.attachments:
            attach_list = []
            for attach in msg.attachments:
                attach_list.append(await handle_attachmen(attach, api))
            attach_list = list(filter(None, attach_list))
            resend_dict['attachment'] += attach_list
    return resend_dict

def split_text(text:str):  #split by parts <=4096 sybols
    result = []
    text = text.strip()
    while len(text)>4096:
        temp = text[:4096]
        if temp.rfind('\n')>0:
            marker = temp.rfind('\n')
        elif temp.rfind(' ')>0:
            marker = temp.rfind(' ')
        else:
            marker = 4096
        result.append(text[:marker])
        text = text[marker:]
    result.append(text)
    return result

async def split_message_dict(message_dict:dict):
    text_list = split_text(message_dict.get('message',""))
    attach_list = message_dict.get('attachment', [])
    message_dict['attachment'] = attach_list[:10]
    message_dict['message'] = text_list[-1]
    result = []
    for text in text_list[:-1]:
        result.append({"message":text})
    result.append(message_dict)
    for i in range(10,len(attach_list),10):
        result.append({"attachment":attach_list[i:i+10]})
    return result

async def send_new(api, msg_dict, peer_ids):
    if not isinstance(peer_ids, (list, tuple)):
        peer_ids = [peer_ids]
    msg_list = await split_message_dict(msg_dict)
    for_execue = []
    for peer in peer_ids:
        for msg in msg_list:
            for_execue.append(("messages.send",msg.copy()))
            for_execue[-1][1].update({"peer_id":peer, "random_id":random.randint(50000,2000000000)})

    return await stor.execue(api, for_execue)

async def resend_message(box, peer_ids):
    msgs = [box.msg]
    if box.msg.reply_message:
        msgs.append(box.msg.reply_message)
    if box.msg.fwd_messages:
        msgs.append(box.msg.fwd_messages)
    msg_dict = await get_message_resend_dict(box.api, msgs)
    await send_new(box.api, msg_dict, peer_ids)



