import logging
import os
import random
import re

import boto3

from botocore.client import Config
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

S3_BUCKET = os.environ['S3_BUCKET']
S3_BUCKET_PREFIX = os.environ['S3_BUCKET_PREFIX']
AWS_ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']

s3_client = boto3.client('s3', 'eu-central-1', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, config=Config(signature_version='s3v4'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

files = []


def get_files(prefixes: list[str]):
    paginator = s3_client.get_paginator('list_objects_v2')
    global files
    files = []
    for prefix in prefixes:
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_BUCKET_PREFIX + prefix):
            files.extend([obj['Key'] for obj in page.get('Contents', [])])


def extract_location(file_path):
    file_path = file_path.removeprefix(S3_BUCKET_PREFIX)
    parts = file_path.split('/')
    if re.match(r'^\d{4}$', parts[0]) is not None:  # remove the first dir with year if it exists
        parts = parts[1:]
    # format: date - order - country - city/**/jpg
    if ' - ' in parts[0]:
        return parts[0].split(' - ')[-1]
    # format: country/city/**/jpg
    return parts[1]


async def set_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args == ['all']:
        get_files([''])
    else:
        get_files(context.args)
    await update.message.reply_text('Filter is set!')


async def send_random_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file_key = random.choice(files)
    location = extract_location(file_key)
    file_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': file_key})
    logger.info(file_key)
    logger.info(location)
    logger.info(file_url)

    context.chat_data['correct_location'] = location.lower()
    await update.message.reply_photo(photo=file_url, caption='Guess the location!')


async def check_location_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_guess = update.message.text.strip().lower()
    correct_location = context.chat_data.get('correct_location', '')

    if not correct_location:
        await update.message.reply_text('No photo has been sent yet. Use /random first!')
        return

    if user_guess == correct_location or user_guess in correct_location.split(' '):
        await update.message.reply_text('✅ Correct!')
    else:
        await update.message.reply_text(f"❌ Wrong! The correct location was: {correct_location.title()}")

if __name__ == '__main__':
    get_files([''])
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler('filter', set_filter))
    application.add_handler(CommandHandler('random', send_random_photo))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_location_guess))

    application.run_polling()
