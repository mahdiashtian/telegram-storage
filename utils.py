import random
import string

from keyboard import start_btn


def generate_random_text(n=15, existing_text=""):
    # Define a character set to choose random characters from
    characters = string.ascii_letters + string.digits

    # Generate random text by randomly selecting characters
    random_text = ''.join(random.choice(characters) for _ in range(n))

    # If existing text is provided, append it to the generated text
    if existing_text:
        random_text = existing_text + random_text

    return random_text


def send_file(app, client, message, file, db, keyboard=start_btn):
    file.count += 1
    db.commit()
    caption = file.caption or ""
    caption += f"\nتعداد دانلود : {file.count}\n\n@{client.me.username}"

    if file.type == 'animation':
        return app.send_animation(message.chat.id, file.file_id, caption=caption,
                                  reply_markup=start_btn)

    elif file.type == 'photo':
        return app.send_photo(message.chat.id, file.file_id, caption=caption,
                              reply_markup=start_btn)

    elif file.type == 'video':
        return app.send_video(message.chat.id, file.file_id, caption=caption,
                              reply_markup=start_btn)

    elif file.type == 'voice':
        return app.send_voice(message.chat.id, file.file_id, caption=caption,
                              reply_markup=start_btn)

    elif file.type == 'audio':
        return app.send_audio(message.chat.id, file.file_id, caption=caption,
                              reply_markup=start_btn)

    elif file.type == 'document':
        return app.send_document(message.chat.id, file.file_id, caption=caption,
                                 reply_markup=start_btn)
