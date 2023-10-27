from pyrogram import filters
from pyrogram.types import Update


def conversation(conversation_state: dict, state: str):
    async def func(_, __, update: Update):
        return bool(_.conversation_state.get(update.from_user.id, None) == _.state)

    return filters.create(
        func,
        name="ConversationStateFilter",
        conversation_state=conversation_state,
        state=state
    )
