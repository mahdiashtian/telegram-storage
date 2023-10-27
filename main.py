# -*- coding:utf-8 -*-
import logging
from enum import Enum, auto

from decouple import config
from pyrogram import Client, filters
from pyrogram import enums

from database import SessionLocal
from filters import conversation
from keyboard import start_btn, back_btn
from services import read_user_from_db, create_user_from_db, create_file_from_db, delete_file_from_db, \
    read_file_from_db, read_files_from_db
from text import start_text, get_file_text, tracing_file_text, delete_file_text, account_text
from utils import generate_random_text, send_file

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s ',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

admin_master = 1017215648

api_id = config("API_ID")

api_hash = config("API_HASH")

bot_token = config("BOT_TOKEN")

app = Client(
    'mahdi',
    api_id,
    api_hash,
    bot_token=bot_token)

app.set_parse_mode(enums.ParseMode.MARKDOWN)

conversation_state = {}
conversation_object = {}

db = SessionLocal()


class State(Enum):
    USER_UPLOAD_FILE = auto()
    USER_DELETE_FILE = auto()
    USER_SEND_ID_FOR_SET_CAPTION = auto()
    USER_SEND_TEXT_FOR_SET_CAPTION = auto()
    USER_SEND_ID_FOR_UNSET_CAPTION = auto()
    USER_SEND_ID_FOR_SET_PASSWORD = auto()
    USER_SEND_TEXT_FOR_SET_PASSWORD = auto()
    USER_SEND_ID_FOR_UNSET_PASSWORD = auto()
    USER_SEND_PASSWORD_FOR_GET_FILE = auto()
    USER_SEND_ID_FILE_FOR_TRACKING = auto()


@app.on_message(filters.text & filters.regex("^/start$"))
async def start(client, message):
    if read_user_from_db(db, message.from_user.id) is None:
        user = {
            "userid": message.from_user.id,
        }
        create_user_from_db(db, user)

    sender = message.from_user
    conversation_state[sender.id] = None
    await app.send_message(message.from_user.id, start_text.format(sender.first_name), reply_markup=start_btn)


@app.on_message(filters.text & filters.regex("^/start get_*"))
async def get_file(client, message):
    code = message.text.replace("/start get_", "")
    file = read_file_from_db(db, code)
    if file is None:
        await app.send_message(message.from_user.id, "❌ فایل یافت نشد !")

    elif file.password is None or file.owner_id == message.from_user.id:
        await send_file(app, client, message, file, db)
    else:
        conversation_object[message.from_user.id] = file
        conversation_state[message.from_user.id] = State.USER_SEND_PASSWORD_FOR_GET_FILE
        await app.send_message(message.from_user.id, "🔑 لطفا پسورد فایل را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🔙 بازگشت"))
async def back(client, message):
    conversation_state[message.from_user.id] = None
    conversation_object[message.from_user.id] = None
    await app.send_message(message.from_user.id, start_text, reply_markup=start_btn)


@app.on_message(filters.text & filters.regex("🗳 آپلود فایل"))
async def upload_file(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_UPLOAD_FILE
    await app.send_message(message.from_user.id, "📤 لطفا فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🗑 حذف فایل"))
async def remove_file(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_DELETE_FILE
    await app.send_message(message.from_user.id, "🗑 لطفا کد فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("📝تنظیم کپشن"))
async def set_caption(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_SEND_ID_FOR_SET_CAPTION
    await app.send_message(message.from_user.id, "📝 لطفا کد فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🗞حذف کپشن"))
async def unset_caption(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_SEND_ID_FOR_UNSET_CAPTION
    await app.send_message(message.from_user.id, "📝 لطفا کد فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🔐 تنظیم پسورد"))
async def set_password(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_SEND_ID_FOR_SET_PASSWORD
    await app.send_message(message.from_user.id, "🔑 لطفا کد فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🗝حذف پسورد"))
async def unset_password(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_SEND_ID_FOR_UNSET_PASSWORD
    await app.send_message(message.from_user.id, "🔑 لطفا کد فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🗂 کد پیگیری فایل"))
async def file_tracking(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_SEND_ID_FILE_FOR_TRACKING
    await app.send_message(message.from_user.id, "🗂 لطفا کد فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("📂 تاریخچه اپلود"))
async def file_history(client, message):
    files = read_files_from_db(db, None, message.from_user.id)
    if files is None:
        await app.send_message(message.from_user.id, "❌ فایلی یافت نشد !")
    else:
        for file in files:
            text = tracing_file_text.format(file.code, file.size, file.type, file.caption or "ندارد",
                                            file.password or "ندارد",
                                            file.created_at, client.me.username, file.code)
            await app.send_message(message.from_user.id, text, reply_markup=start_btn)


@app.on_message(filters.text & filters.regex("🎫 حساب کاربری"))
async def account(client, message):
    files = read_files_from_db(db, None, message.from_user.id)
    text = account_text.format(len(files), message.from_user.first_name, message.from_user.username, client.me.username)
    await app.send_message(message.from_user.id, text, reply_markup=start_btn)


@app.on_message(filters.text & filters.regex("🛠سازنده"))
async def creator(client, message):
    await app.send_message(message.from_user.id, "👤 سازنده ربات : @Mahdiashtian", reply_markup=start_btn)


@app.on_message(conversation(conversation_state, State.USER_SEND_ID_FILE_FOR_TRACKING))
async def get_file_for_tracking(client, message):
    code = message.text
    file = read_file_from_db(db, code, message.from_user.id)
    if file is None:
        await app.send_message(message.from_user.id, "❌ فایل یافت نشد !")
        return
    else:

        text = tracing_file_text.format(code, file.size, file.type, file.caption or "ندارد", file.password or "ندارد",
                                        file.created_at, client.me.username, code)
        await app.send_message(message.from_user.id, text, reply_markup=start_btn)
        conversation_state[message.from_user.id] = None
        conversation_object[message.from_user.id] = None


@app.on_message(conversation(conversation_state, State.USER_SEND_PASSWORD_FOR_GET_FILE))
async def get_file_has_password(client, message):
    file = conversation_object.get(message.from_user.id, None)
    if file.password == message.text:
        await send_file(app, client, message, file, db)
        sender = message.from_user
        await app.send_message(message.from_user.id, start_text.format(sender.first_name), reply_markup=start_btn)
        conversation_state[message.from_user.id] = None
        conversation_object[message.from_user.id] = None

    else:
        await app.send_message(message.from_user.id, "❌ پسورد اشتباه است !", reply_markup=back_btn)


@app.on_message(conversation(conversation_state, State.USER_SEND_ID_FOR_UNSET_PASSWORD))
async def get_object_for_unset_password(client, message):
    code = message.text
    file = read_file_from_db(db, code, message.from_user.id)
    if file is None:
        await app.send_message(message.from_user.id, "❌ فایل یافت نشد !")
        return
    else:
        file.password = None
        db.commit()
        await app.send_message(message.from_user.id, "✅ پسورد با موفقیت حذف شد !", reply_markup=start_btn)
        conversation_state[message.from_user.id] = None
        conversation_object[message.from_user.id] = None


@app.on_message(conversation(conversation_state, State.USER_SEND_ID_FOR_SET_PASSWORD))
async def get_object_for_set_password(client, message):
    code = message.text
    file = read_file_from_db(db, code, message.from_user.id)
    if file is None:
        await app.send_message(message.from_user.id, "❌ فایل یافت نشد !", reply_markup=back_btn)
        return
    else:
        conversation_object[message.from_user.id] = file
        conversation_state[message.from_user.id] = State.USER_SEND_TEXT_FOR_SET_PASSWORD
        await app.send_message(message.from_user.id, "🔑 لطفا پسورد خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(conversation(conversation_state, State.USER_SEND_TEXT_FOR_SET_PASSWORD))
async def set_password_(client, message):
    file = conversation_object.get(message.from_user.id, None)
    file.password = message.text
    db.commit()
    await app.send_message(message.from_user.id, "✅ پسورد با موفقیت ثبت شد !", reply_markup=start_btn)
    conversation_state[message.from_user.id] = None
    conversation_object[message.from_user.id] = None


@app.on_message(conversation(conversation_state, State.USER_SEND_ID_FOR_UNSET_CAPTION))
async def get_object_for_unset_caption(client, message):
    code = message.text
    file = read_file_from_db(db, code, message.from_user.id)
    if file is None:
        await app.send_message(message.from_user.id, "❌ فایل یافت نشد !", reply_markup=back_btn)
        return
    else:
        file.caption = None
        db.commit()
        await app.send_message(message.from_user.id, "✅ کپشن با موفقیت حذف شد !", reply_markup=start_btn)
        conversation_state[message.from_user.id] = None
        conversation_object[message.from_user.id] = None


@app.on_message(conversation(conversation_state, State.USER_SEND_ID_FOR_SET_CAPTION))
async def get_object_for_set_caption(client, message):
    code = message.text
    file = read_file_from_db(db, code, message.from_user.id)
    if file is None:
        await app.send_message(message.from_user.id, "❌ فایل یافت نشد !", reply_markup=back_btn)
        return
    else:
        conversation_object[message.from_user.id] = file
        conversation_state[message.from_user.id] = State.USER_SEND_TEXT_FOR_SET_CAPTION
        await app.send_message(message.from_user.id, "📝 لطفا کپشن خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(conversation(conversation_state, State.USER_SEND_TEXT_FOR_SET_CAPTION))
async def set_caption_(client, message):
    file = conversation_object.get(message.from_user.id, None)
    file.caption = message.text
    db.commit()
    await app.send_message(message.from_user.id, "✅ کپشن با موفقیت ثبت شد !", reply_markup=start_btn)
    conversation_state[message.from_user.id] = None
    conversation_object[message.from_user.id] = None


@app.on_message(conversation(conversation_state, State.USER_DELETE_FILE))
async def remove_file_(client, message):
    code = message.text
    delete_file_from_db(db, message.from_user.id, code)
    await app.send_message(message.from_user.id, delete_file_text,
                           reply_markup=back_btn)


@app.on_message(conversation(conversation_state, State.USER_UPLOAD_FILE))
async def upload_file_(client, message):
    code = generate_random_text(15)

    if message.text or message.sticker:
        await app.send_message(message.from_user.id, "❌ فایل شما پشتیبانی نمیشود !")
        return

    elif message.sticker:
        file_id = message.sticker.file_id
        size = message.sticker.file_size
        media_type = message.media.__dict__.get('_value_')

    elif message.photo:
        file_id = message.photo.file_id
        size = message.photo.file_size
        media_type = message.media.__dict__.get('_value_')

    elif message.animation:
        file_id = message.animation.file_id
        size = message.animation.file_size
        media_type = message.media.__dict__.get('_value_')

    elif message.video:
        file_id = message.video.file_id
        size = message.video.file_size
        media_type = message.media.__dict__.get('_value_')

    elif message.voice:
        file_id = message.voice.file_id
        size = message.voice.file_size
        media_type = message.media.__dict__.get('_value_')

    elif message.audio:
        file_id = message.audio.file_id
        size = message.audio.file_size
        media_type = message.media.__dict__.get('_value_')

    elif message.document:
        file_id = message.document.file_id
        size = message.document.file_size
        media_type = message.media.__dict__.get('_value_')
    text = get_file_text.format(code, size, client.me.username, code)
    create_file_from_db(db,
                        {"type": media_type, "code": code, "file_id": file_id, "owner_id": message.from_user.id,
                         "size": size})
    await app.send_message(message.from_user.id, text, reply_markup=back_btn)


app.run()
