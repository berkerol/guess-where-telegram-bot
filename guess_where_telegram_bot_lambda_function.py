import json
import logging
import os
import random
import urllib.request

import boto3

from botocore.client import Config

import helper

S3_BUCKET = os.environ['S3_BUCKET']
S3_BUCKET_PREFIX = os.environ['S3_BUCKET_PREFIX']

s3_client = boto3.client('s3', 'eu-central-1', config=Config(signature_version='s3v4'))
dynamodb = boto3.resource('dynamodb', 'eu-central-1')
table = dynamodb.Table('guess-where-telegram-bot')
ssm_client = boto3.client('ssm', 'eu-central-1')
TELEGRAM_BOT_TOKEN = ssm_client.get_parameter(Name='/guess-where-telegram-bot/TELEGRAM_BOT_TOKEN', WithDecryption=True)['Parameter']['Value']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_files(chat_id, set_filter: str):
    files = []
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=f'{chat_id}_{set_filter}.json')
        files = json.loads(response['Body'].read())
    except s3_client.exceptions.NoSuchKey:
        paginator = s3_client.get_paginator('list_objects_v2')
        for prefix in set_filter.split(' '):
            if prefix == 'all':
                prefix = ''
            for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_BUCKET_PREFIX + prefix):
                files.extend([obj['Key'] for obj in page.get('Contents', [])])
        s3_client.put_object(Bucket=S3_BUCKET, Key=f'{chat_id}_{set_filter}.json', Body=json.dumps(files))
    return files


def send_telegram(payload, type_name):
    with urllib.request.urlopen(urllib.request.Request(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/send{type_name}', json.dumps(payload).encode('utf-8'), {'Content-Type': 'application/json'})):
        pass


def send_telegram_message(chat_id, text):
    send_telegram({
        'chat_id': chat_id,
        'text': text
    }, 'Message')


def send_telegram_photo(chat_id, photo):
    send_telegram({
        'chat_id': chat_id,
        'photo': photo,
        'caption': 'Guess the city or country!'
    }, 'Photo')


def send_random_photo(chat_id, file_key):
    city, country = helper.extract_city_and_country(file_key, S3_BUCKET_PREFIX)
    file_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': file_key})
    logger.info(file_key)
    logger.info(city)
    logger.info(country)
    logger.info(file_url)

    table.put_item(Item={'chat_id': str(chat_id), 'city': city.lower(), 'country': country.lower()})
    send_telegram_photo(chat_id, file_url)


def check_location_guess(chat_id, text):
    user_guess = text.lower().strip()
    correct_location = table.get_item(Key={'chat_id': str(chat_id)})

    if 'Item' not in correct_location:
        send_telegram_message(chat_id, 'No photo has been sent yet. Use /random first!')
        return

    table.delete_item(Key={'chat_id': str(chat_id)})
    city = correct_location['Item']['city']
    country = correct_location['Item']['country']
    if user_guess == city or user_guess in city.split(' '):
        send_telegram_message(chat_id, '✅ Correct!')
    elif user_guess == country or user_guess in country.split(' '):
        send_telegram_message(chat_id, f'✅ Correct! City was {city.title()}')
    else:
        send_telegram_message(chat_id, f'❌ Wrong! The correct location was: {city.title()} in {country.title()}')


def lambda_handler(event, context):  # pylint: disable=W0613
    chat_id = json.loads(event.get('body', '{}')).get('message', {}).get('chat', {}).get('id', '')
    text = json.loads(event.get('body', '{}')).get('message', {}).get('text', '')
    if chat_id == '' or text == '':
        return {
            'statusCode': 400,
            'body': json.dumps('body.message.chat.id or body.message.text is missing!')
        }
    if text == '/random':
        set_filter = table.get_item(Key={'chat_id': f'{chat_id}_filter'})
        if 'Item' in set_filter:
            set_filter = set_filter['Item']['filter']
        else:
            set_filter = 'all'
            table.put_item(Item={'chat_id': f'{chat_id}_filter', 'filter': set_filter})
        send_random_photo(chat_id, random.choice(get_files(chat_id, set_filter)))
    elif text.startswith('/filter'):
        set_filter = text[8:]
        table.put_item(Item={'chat_id': f'{chat_id}_filter', 'filter': set_filter})
        get_files(chat_id, set_filter)
        send_telegram_message(chat_id, f'Filter is set to {set_filter}')
    else:
        check_location_guess(chat_id, text)
    return {
        'statusCode': 200,
        'body': json.dumps('Telegram message is handled successfully!')
    }
