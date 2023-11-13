from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379/0')  # Replace with your Redis server information


@celery.task
def delete_video(app, chat_id, message_id):
    app.delete_messages(chat_id=chat_id, message_ids=message_id)


if __name__ == '__main__':
    celery.start()
