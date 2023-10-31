from pyrogram import filters
from pyrogram.types import Update

from services import read_user_from_db


def conversation(conversation_state: dict, state: str):
    async def func(_, __, update: Update):
        return bool(_.conversation_state.get(update.from_user.id, None) == _.state)

    return filters.create(
        func,
        name="ConversationStateFilter",
        conversation_state=conversation_state,
        state=state
    )


def admin_filter(db: object):
    async def func(_, __, update: Update):
        user = read_user_from_db(_.db, update.from_user.id)
        return bool(user and (user.is_superuser or user.is_staff))

    return filters.create(
        func,
        name="AdminFilter",
        db=db
    )
