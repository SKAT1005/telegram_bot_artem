import datetime
import os
import random
import time

import telethon
from telethon import types
from telethon.sync import TelegramClient
from telethon.tl.functions import messages, channels, stories, account, photos

import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from app.models import API, Orders, WaveTime


async def create_new_order(client, url):
    try:
        order = Orders.objects.get(url=url)
    except Exception:
        order = Orders.objects.create(
            url=url,
            gender=3,
            start=datetime.datetime.now(),
            end=datetime.datetime.now() + datetime.timedelta(days=30)
        )
        order.apis.add(client)
    else:
        if client not in order.apis.all():
            order.apis.add(client)


async def read_messages_and_set_reactions(client, entity, client_data, limit=2):
    offset_msg = 0
    limit_msg = limit
    finish_check_message = True
    history = await client(messages.GetHistoryRequest(
        peer=entity,
        offset_id=offset_msg,
        offset_date=None, add_offset=0,
        limit=limit_msg, max_id=0, min_id=0,
        hash=0))
    msgs = history.messages
    for msg in msgs:
        if random.randint(0, 4) == 1:
            try:
                a = random.randint(0, len(msg.reactions.results) - 1)
                emotion = msg.reactions.results[a].reaction.emoticon
                try:
                    await client(messages.SendReactionRequest(
                        peer=entity,
                        msg_id=msg.id,
                        reaction=[types.ReactionEmoji(emoticon=emotion)]
                    ))
                except Exception as e:
                    print(msg.id)
                    print(e)
                    pass
            except Exception as e:
                print(e)
        if random.randint(0, 9) == 2:
            a = True
            for link in msg.message.split():
                if 'https://t.me/' in link:
                    await create_new_order(client_data, link)
            for entity in msg.entities:
                if 'https://t.me/' in entity.url:
                    await create_new_order(client_data, entity.url)


async def subscribe_privat_channel(client, hash):
    try:
        await client(messages.ImportChatInviteRequest(hash))
    except Exception as e:
        print(f'subscribe_privat_channel: {e}')


async def subscribe_public_channel(entity, client):
    try:
        await client(channels.JoinChannelRequest(entity))
    except Exception as e:
        print(f'subscribe_public_channel: {e}')


async def subscribe_on_channels(client, channel_url):
    try:
        entety = await client.get_entity(channel_url)
        await subscribe_public_channel(entety, client)
    except Exception:
        await subscribe_privat_channel(client, channel_url[14:])


async def activate_user(api):
    client = TelegramClient(api.id, api_id=api.api_id, api_hash=api.api_hash,
                            system_version="4.16.30-vxCUSTOM")
    await client.start(phone=api.phone)
    return client


async def channels(order, wave_time):
    if order.start <= datetime.datetime.now():
        count = len(order.apis.all())
        if order.number_wave == 0:
            sleep_time = wave_time.first
            count = int(count * 0.6)
        elif order.number_wave == 1:
            sleep_time = wave_time.second
            count = int(count * 0.9)
        elif order.number_wave >= 2:
            sleep_time = wave_time.therd
        no_subscribe = order.apis.all()[order.subscribe: count]
        subscribe = order.apis.all()[:order.subscribe]
        if order.next_action_time <= datetime.datetime.now() and len(no_subscribe) > 0:
            user = no_subscribe[0]
            client = await activate_user(user)
            await subscribe_on_channels(client, order.url)
            order.subscribe += 1
            order.next_action_time = datetime.datetime.now() + datetime.timedelta(seconds=sleep_time)
            if order.subscribe == count:
                order.number_wave += 1
            order.save()
            see_post = 3
            if random.randint(0, 100) <= 50:
                see_post += 2
            if random.randint(0, 100) <= 25:
                see_post += 2
            if random.randint(0, 100) <= 10:
                see_post += 2
            try:
                entity = await client.get_entity(order.url)
                await read_messages_and_set_reactions(client, entity, user, limit=see_post)
            except Exception:
                pass
            await client.disconnect()
        if subscribe:
            for user in subscribe:
                client = await activate_user(user)
                try:
                    entity = await client.get_entity(order.url)
                    await read_messages_and_set_reactions(client, entity, user)
                except Exception:
                    pass
                client.disconnect()
                time.sleep(random.randint(1, 5))
                await client.disconnect()


async def bot(bot_url, client):
    await client.send_message(entity=bot_url, message='/start')
    time.sleep(1)
    messages = await client.get_messages(bot_url)
    for entity in messages[0].entities:
        try:
            url = entity.url
            if url[-3:] == 'bot':
                await bot(url, client)
            else:
                await subscribe_on_channels(client, url)
        except Exception:
            pass
    for row in messages[0].reply_markup.rows:
        for button in row.buttons:
            try:
                url = button.url
                if url[-3:] == 'bot':
                    await bot(url, client)
                else:
                    await subscribe_on_channels(client, url)
            except Exception:
                try:
                    button.data
                except Exception:
                    pass
                else:
                    text = button.text
    await messages[0].click(text=text)
    await client.disconnect()


async def start():
    while True:
        wave_time = WaveTime.objects.all()[0]
        for order in Orders.objects.all():
            if order.url[-3:] == 'bot':
                for api in order.apis.all():
                    client = await activate_user(api)
                    await bot(order.url, client)
            else:
                await channels(order, wave_time)
