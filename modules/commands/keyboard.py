from modules.commands.utils import *

async def handle_keyboard(box):
    if box.msg.payload == '{"command":"start"}':
        answer = '''There are no functions here
            Contact the admins if you need:
            First year - [id464575769|Speaker Sr]
            Second and third years - [id530706817|Speaker Lr]'''
        await log_respond(box, f"{box.msg.from_id} used button start", answer)
        return True
    return False