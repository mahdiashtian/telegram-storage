# -*- coding:utf-8 -*-
import asyncio
import logging
import re
import time
from enum import Enum, auto

import uvloop
from decouple import config
from pyrogram import Client, filters
from pyrogram import enums
from pyrogram.types import (InlineKeyboardMarkup)

from database import SessionLocal
from filters import conversation, admin_filter
from keyboard import start_btn, back_btn, admin_btn, join_btn, channel_join_btn
from services import create_user_from_db, create_file_from_db, delete_file_from_db, \
    read_file_from_db, read_files_from_db, change_admin_from_db, read_users, create_backup, read_channels_from_db, \
    create_channel_from_db, delete_channel_from_db, userid_list, channel_list
from text import start_text, get_file_text, tracing_file_text, delete_file_text, account_text, admin_panel_text, \
    join_panel_text, channel_list_text, channel_add_text, need_join_text
from utils import generate_random_text, send_file

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s ',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

admin_master = 1017215648

api_id = config("API_ID")

api_hash = config("API_HASH")

bot_token = config("BOT_TOKEN")

uvloop.install()

app = Client(
    'mahdi',
    api_id,
    api_hash,
    bot_token=bot_token)

db = SessionLocal()

app.set_parse_mode(enums.ParseMode.MARKDOWN)

conversation_state = {}
conversation_object = {}

user_list = userid_list(db)
channel_join_list = None


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
    USER_ADMIN_PANEL = auto()
    USER_SET_ADMIN = auto()
    UNSER_UNSET_ADMIN = auto()
    USER_FORWARD_MESSAGE_FOR_ALL = auto()
    USER_JOIN_CHANNEL_PANEL = auto()
    USER_ADD_CHANNEL = auto()
    USER_REMOVE_CHANNEL = auto()


def timer(func):
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.4f} sec")
        return result

    return wrapper


@timer
def check_user_in_db(func):
    async def wrapper(client, message):
        global user_list
        if message.from_user.id not in user_list:
            user = {
                "userid": message.from_user.id,
            }
            create_user_from_db(db, user)

            user_list = userid_list(db)
        await func(client, message)

    return wrapper


@timer
def check_joined(func):
    async def wrapper(client, message):
        global channel_join_list
        if not channel_join_list:
            channel_join_list = await channel_list(db, app)
        need_join = {}
        btn = []
        if channel_join_list != 1:
            for key, value in channel_join_list.items():

                title = value.get('title')
                link = value.get('link')
                try:
                    member = await client.get_chat_member(key, message.from_user.id)
                    if member.status.value in ["creator", "administrator", "member", "owner"]:
                        ...
                    else:
                        need_join[key] = {"title": title, "link": link}
                except:
                    need_join[key] = {"title": title, "link": link}
        if need_join:
            for key, value in need_join.items():
                title = value.get('title')
                link = value.get('link')
                btn.append([channel_join_btn(title, link)])
            text = message.text.split(" ")[-1]
            if "get_" not in text:
                text = None
            btn.append([channel_join_btn("✅ عضو شدم", f"https://t.me/{client.me.username}?start={text}")])
            await app.send_message(message.from_user.id, need_join_text, reply_markup=InlineKeyboardMarkup(btn))
        else:
            await func(client, message)

    return wrapper


@app.on_message(filters.text & filters.regex("^/start$"))
@check_joined
@check_user_in_db
async def start(client, message):
    conversation_state[message.from_user.id] = None
    await app.send_message(message.from_user.id, start_text.format(message.from_user.first_name),
                           reply_markup=start_btn)


@app.on_message(filters.text & filters.regex("^/start get_*"))
@check_joined
@check_user_in_db
async def get_file(client, message):
    conversation_state[message.from_user.id] = None
    code = message.text.replace("/start get_", "")
    file = read_file_from_db(db, code)
    if file is None:
        await app.send_message(message.from_user.id, "❌ فایل یافت نشد !")

    elif file.password is None or file.owner_id == message.from_user.id:
        file = await send_file(app, client, message, file, db)
        await asyncio.sleep(30)
        await app.delete_messages(message.chat.id, file.id)
    else:
        conversation_object[message.from_user.id] = file
        conversation_state[message.from_user.id] = State.USER_SEND_PASSWORD_FOR_GET_FILE
        await app.send_message(message.from_user.id, "🔑 لطفا پسورد فایل را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.command(['admin']) & admin_filter(db))
async def admin_panel(client, message):
    conversation_state[message.from_user.id] = State.USER_ADMIN_PANEL
    await app.send_message(message.from_user.id,
                           admin_panel_text.format(message.from_user.first_name),
                           reply_markup=admin_btn)


@app.on_message(filters.text & filters.regex("🔸 لیست کانال ها") &
                conversation(conversation_state, State.USER_JOIN_CHANNEL_PANEL) & admin_filter(db))
async def get_channels(client, message):
    text = "📃 لیست کانال های عضویت اجباری شما :\n"
    channels = read_channels_from_db(db)
    if channels:
        for channel in channels:
            text += channel_list_text.format(channel.channel_link, channel.channel_id)
        await app.send_message(message.from_user.id, text, reply_markup=join_btn)
    else:
        await app.send_message(message.from_user.id, "❌ هیچ کانالی یافت نشد !", reply_markup=join_btn)


@app.on_message(filters.text & filters.regex("▫️ اضافه کردن کانال") &
                conversation(conversation_state, State.USER_JOIN_CHANNEL_PANEL) & admin_filter(db))
async def add_channel(client, message):
    conversation_state[message.from_user.id] = State.USER_ADD_CHANNEL
    await app.send_message(message.from_user.id, channel_add_text, reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("▪️ حذف کانال") &
                conversation(conversation_state, State.USER_JOIN_CHANNEL_PANEL) & admin_filter(db))
async def remove_channel(client, message):
    conversation_state[message.from_user.id] = State.USER_REMOVE_CHANNEL
    await app.send_message(message.from_user.id, "🔗 لطفا آیدی عددی کانال را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🎯 عضویت اجباری") &
                conversation(conversation_state, State.USER_ADMIN_PANEL) & admin_filter(db))
async def join_panel(client, message):
    conversation_state[message.from_user.id] = State.USER_JOIN_CHANNEL_PANEL
    await app.send_message(message.from_user.id, join_panel_text.format(message.from_user.first_name),
                           reply_markup=join_btn)


@app.on_message(filters.text & filters.regex("👤 افزودن ادمین") &
                conversation(conversation_state, State.USER_ADMIN_PANEL) & admin_filter(db))
async def set_admin(client, message):
    conversation_state[message.from_user.id] = State.USER_SET_ADMIN
    await app.send_message(message.from_user.id, "👤 لطفا آیدی عددی ادمین جدید را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("❌ حذف ادمین") &
                conversation(conversation_state, State.USER_ADMIN_PANEL) & admin_filter(db))
async def unset_admin(client, message):
    conversation_state[message.from_user.id] = State.UNSER_UNSET_ADMIN
    await app.send_message(message.from_user.id, "👤 لطفا آیدی عددی ادمین را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("👥 نمایش لیست ادمین ها") &
                conversation(conversation_state, State.USER_ADMIN_PANEL) & admin_filter(db))
async def get_admins(client, message):
    users = read_users(db, is_admin=True)
    text = "👥 لیست ادمین ها : \n\n"
    for user in users:
        user_object = await app.get_users(user.userid)
        first_name = user_object.first_name
        last_name = user_object.last_name or ""
        text += "👤 {} \n🆔 {} \n\n".format(first_name + last_name, user.userid)
    await app.send_message(message.from_user.id, text, reply_markup=admin_btn)


@app.on_message(filters.text & filters.regex("🔌بک آپ") &
                conversation(conversation_state, State.USER_ADMIN_PANEL) & admin_filter(db))
async def backup(client, message):
    file_path = create_backup()
    if file_path:
        await app.send_document(message.from_user.id, file_path, caption="📤 بک آپ ربات شما ...", reply_markup=admin_btn)
    else:
        await app.send_message(message.from_user.id, "❌ مشکلی در ایجاد بک آپ رخ داده است !", reply_markup=admin_btn)


@app.on_message(filters.text & filters.regex("📈آمار") &
                conversation(conversation_state, State.USER_ADMIN_PANEL) & admin_filter(db))
async def status(client, message):
    users = read_users(db)
    files = read_files_from_db(db)
    text = "📊 آمار ربات : \n\n"
    text += "👥 تعداد کاربران : {} \n📤 تعداد فایل های آپلود شده : {}".format(len(users), len(files))
    await app.send_message(message.from_user.id, text, reply_markup=admin_btn)


@app.on_message(filters.text & filters.regex("📭 فوروارد همگانی") &
                conversation(conversation_state, State.USER_ADMIN_PANEL) & admin_filter(db))
async def forward_message_for_all(client, message):
    conversation_state[message.from_user.id] = State.USER_FORWARD_MESSAGE_FOR_ALL
    await app.send_message(message.from_user.id, "📭 لطفا پیام خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🔙 بازگشت"))
@check_joined
@check_user_in_db
async def back(client, message):
    if conversation_state[message.from_user.id] in [State.USER_ADD_CHANNEL, State.USER_REMOVE_CHANNEL]:
        conversation_state[message.from_user.id] = State.USER_JOIN_CHANNEL_PANEL
        await app.send_message(message.from_user.id,
                               join_panel_text.format(message.from_user.first_name),
                               reply_markup=join_btn)

    else:
        conversation_state[message.from_user.id] = None
        conversation_object[message.from_user.id] = None
        await app.send_message(message.from_user.id, start_text, reply_markup=start_btn)


@app.on_message(filters.text & filters.regex("🗳 آپلود فایل"))
@check_joined
@check_user_in_db
async def upload_file(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_UPLOAD_FILE
    await app.send_message(message.from_user.id, "📤 لطفا فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🗑 حذف فایل"))
@check_joined
@check_user_in_db
async def remove_file(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_DELETE_FILE
    await app.send_message(message.from_user.id, "🗑 لطفا شناسه فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("📝 تنظیم کپشن"))
@check_joined
@check_user_in_db
async def set_caption(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_SEND_ID_FOR_SET_CAPTION
    await app.send_message(message.from_user.id, "📝 لطفا شناسه فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🗞 حذف کپشن"))
@check_joined
@check_user_in_db
async def unset_caption(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_SEND_ID_FOR_UNSET_CAPTION
    await app.send_message(message.from_user.id, "📝 لطفا شناسه فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🔐 تنظیم پسورد"))
@check_joined
@check_user_in_db
async def set_password(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_SEND_ID_FOR_SET_PASSWORD
    await app.send_message(message.from_user.id, "🔑 لطفا شناسه فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🗝 حذف پسورد"))
@check_joined
@check_user_in_db
async def unset_password(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_SEND_ID_FOR_UNSET_PASSWORD
    await app.send_message(message.from_user.id, "🔑 لطفا شناسه فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("🗂 شناسه پیگیری فایل"))
@check_joined
@check_user_in_db
async def file_tracking(client, message):
    sender = message.from_user
    conversation_state[sender.id] = State.USER_SEND_ID_FILE_FOR_TRACKING
    await app.send_message(message.from_user.id, "🗂 لطفا شناسه فایل خود را ارسال کنید ...", reply_markup=back_btn)


@app.on_message(filters.text & filters.regex("📂 تاریخچه اپلود"))
@check_joined
@check_user_in_db
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
@check_joined
@check_user_in_db
async def account(client, message):
    files = read_files_from_db(db, None, message.from_user.id)
    text = account_text.format(len(files), message.from_user.first_name, message.from_user.username, client.me.username)
    await app.send_message(message.from_user.id, text, reply_markup=start_btn)


@app.on_message(filters.text & filters.regex("🛠 سازنده"))
@check_joined
@check_user_in_db
async def creator(client, message):
    await app.send_message(message.from_user.id, "👤 سازنده ربات : @Mahdiashtian", reply_markup=start_btn)


@app.on_message(conversation(conversation_state, State.USER_ADD_CHANNEL))
async def add_channel_(client, message):
    global channel_join_list
    text = message.text
    pattern = r'@([^ ]+)'
    match = re.search(pattern, text)
    if match:
        result = match.group(1)
        create_channel_from_db(db, {"channel_id": result, "channel_link": f"https://t.me/{result}"})
    else:
        channel_link, channel_id = text.split()
        create_channel_from_db(db, {"channel_id": channel_id, "channel_link": channel_link})
    conversation_state[message.from_user.id] = State.USER_JOIN_CHANNEL_PANEL
    channel_join_list = await channel_list(db, app)
    await app.send_message(message.from_user.id, "✅ کانال با موفقیت اضافه شد !", reply_markup=join_btn)


@app.on_message(conversation(conversation_state, State.USER_REMOVE_CHANNEL))
async def remove_channel_(client, message):
    global channel_join_list
    text = message.text
    channel = delete_channel_from_db(db, text)
    if channel:
        conversation_state[message.from_user.id] = State.USER_JOIN_CHANNEL_PANEL
        channel_join_list = await channel_list(db, app)
        await app.send_message(message.from_user.id, "✅ کانال با موفقیت حذف شد !", reply_markup=join_btn)
    else:
        await app.send_message(message.from_user.id, "❌ کانال یافت نشد !", reply_markup=back_btn)


@app.on_message(conversation(conversation_state, State.USER_FORWARD_MESSAGE_FOR_ALL))
async def forward_message_for_all_(client, message):
    await app.send_message(message.from_user.id, "✅ پیام شما با موفقیت فوروارد شد !", reply_markup=admin_btn)
    conversation_state[message.from_user.id] = State.USER_ADMIN_PANEL
    users = read_users(db)
    for user in users:
        try:
            await app.forward_messages(user.userid, message.chat.id, message.id)
        except Exception as e:
            print(e)


@app.on_message(conversation(conversation_state, State.USER_SET_ADMIN))
async def set_admin_(client, message):
    userid = message.text
    result = change_admin_from_db(db, userid, is_staff=True)
    if result:
        await app.send_message(message.from_user.id, "✅ ادمین با موفقیت افزوده شد !", reply_markup=admin_btn)
        conversation_state[message.from_user.id] = State.USER_ADMIN_PANEL
        conversation_object[message.from_user.id] = None
    else:
        await app.send_message(message.from_user.id, "❌ کاربر یافت نشد !", reply_markup=back_btn)


@app.on_message(conversation(conversation_state, State.UNSER_UNSET_ADMIN))
async def unset_admin_(client, message):
    userid = message.text
    result = change_admin_from_db(db, userid, is_staff=False)
    if result:
        await app.send_message(message.from_user.id, "✅ ادمین با موفقیت حذف شد !", reply_markup=admin_btn)
        conversation_state[message.from_user.id] = State.USER_ADMIN_PANEL
        conversation_object[message.from_user.id] = None
    else:
        await app.send_message(message.from_user.id, "❌ کاربر یافت نشد !", reply_markup=back_btn)


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
        file = await send_file(app, client, message, file, db)
        sender = message.from_user
        await app.send_message(message.from_user.id, start_text.format(sender.first_name), reply_markup=start_btn)
        conversation_state[message.from_user.id] = None
        conversation_object[message.from_user.id] = None
        await asyncio.sleep(30)
        await app.delete_messages(message.chat.id, file.id)

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


@app.on_message(conversation(conversation_state, None))
@check_joined
@check_user_in_db
async def default_none(client, message):
    await app.send_message(message.from_user.id, start_text.format(message.from_user.first_name),
                           reply_markup=start_btn)


@app.on_message(conversation(conversation_state, State.USER_ADMIN_PANEL))
async def default_none(client, message):
    await app.send_message(message.from_user.id,
                           admin_panel_text.format(message.from_user.first_name),
                           reply_markup=admin_btn)


app.run()
