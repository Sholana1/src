import asyncio
from fastapi_mail import MessageSchema, MessageType, MultipartSubtypeEnum
from backend.app.core.celery_app import celery_app
from backend.app.core.logging import get_logger

from backend.app.core.emails.config import fastmail

logger = get_logger()

@celery_app.task(
    name="send_email_task",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,), # This only works if you don't catch the exception yourself
    retry_backoff=True
)
def send_email_task(self, *, recipients, subject, html_content, plain_content):
    # Create the message
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=html_content,
        subtype=MessageType.html,
        alternative_body=plain_content,
        multipart_subtype=MultipartSubtypeEnum.alternative
    )
    
    # We use a standard loop to avoid 'Event loop is closed' errors
    loop = asyncio.get_event_loop()
    
    # REMOVE the local try/except so Celery can see the error and RETRY
    loop.run_until_complete(fastmail.send_message(message))
    logger.info(f"Email sent to {recipients}")
    return True