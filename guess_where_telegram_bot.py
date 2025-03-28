import logging
import os
import random

import boto3

from botocore.client import Config
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import helper

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


async def set_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args == ['all']:
        get_files([''])
    else:
        get_files(context.args)
    await update.message.reply_text('Filter is set!')


async def send_random_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file_key = random.choice(files)
    city, country = helper.extract_city_and_country(file_key, S3_BUCKET_PREFIX)
    file_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': file_key})
    logger.info(file_key)
    logger.info(city)
    logger.info(country)
    logger.info(file_url)

    context.chat_data['correct_location'] = f'{city.lower()},{country.lower()}'
    await update.message.reply_photo(photo=file_url, caption='Guess the city or country!')


async def check_location_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_guess = update.message.text.strip().lower()
    correct_location = context.chat_data.get('correct_location', '')

    if not correct_location:
        await update.message.reply_text('No photo has been sent yet. Use /random first!')
        return

    context.chat_data['correct_location'] = ''
    city, country = correct_location.split(',')
    if user_guess == city or user_guess in city.split(' '):
        await update.message.reply_text('✅ Correct!')
    elif user_guess == country or user_guess in country.split(' '):
        await update.message.reply_text(f'✅ Correct! City was {city.title()}')
    else:
        await update.message.reply_text(f'❌ Wrong! The correct location was: {city.title()} in {country.title()}')

if __name__ == '__main__':
    get_files([''])
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler('filter', set_filter))
    application.add_handler(CommandHandler('random', send_random_photo))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_location_guess))

    application.run_polling()
