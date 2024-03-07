import asyncio
import datetime
import json
from time import sleep

import telethon
from telethon import types
from telethon.sync import TelegramClient
from telethon.tl.functions import messages, channels, stories, account, photos

chnls = [[False, 'https://t.me/+6gFniEb3yAMyMWJi', 0]]
story_link = 'https://t.me/toplesofficial/s/76'

client = TelegramClient('test', api_id=26204346, api_hash='7d5e7f858870d425aa1b708d68aba39e',
                        system_version="4.16.30-vxCUSTOM")
# client.connect()
# phone = '+79188084639'
# client.send_code_request(phone, force_sms=False)
# value = input("Enter login code: ")
# try:
#     client.sign_in(phone, code=value)
# except telethon.errors.SessionPasswordNeededError:
#     password = '19097007'
#     client.sign_in(password=password)

# 79188084639 1 servis_akk 26204346 7d5e7f858870d425aa1b708d68aba39e
client.start(phone='+79188084639', password='19097007')

# client.download_profile_photo('me', 'img.jpg')
# client(photos.DeletePhotosRequest(client.get_profile_photos('me')))
# client(photos.UploadProfilePhotoRequest(file=client.upload_file('img.jpg')))
urls = ['https://t.me/FontiumBot']
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
async def bot(url1):
    await client.send_message(entity=url1, message='/start')
    sleep(2)
    messages = await client.get_messages(url1)
    try:
        for entity in messages[0].entities:
            try:
                url = entity.url
                await subscribe_on_channels(client, url)
            except Exception:
                pass
    except Exception:
        pass
    try:
        for row in messages[0].reply_markup.rows:
            for button in row.buttons:
                try:
                    url = button.url
                    await subscribe_on_channels(client, url)
                except Exception:
                    try:
                        button.data
                    except Exception:
                        pass
                    else:
                        text = button.text
        await messages[0].click(text=text)
    except Exception:
        pass
    await client.disconnect()


async def read_messages_and_set_reactions():
    offset_msg = 0
    limit_msg = 5
    finish_check_message = True
    a = True
    entity = await client.get_entity(url)
    while finish_check_message:
        history = await client(messages.GetHistoryRequest(
            peer=entity,
            offset_id=offset_msg,
            offset_date=None, add_offset=0,
            limit=limit_msg, max_id=0, min_id=0,
            hash=0))
        msgs = history.messages
        for msg in msgs:
            try:
                a = await msg.click(text='🟢Купить')
                print(a)
                print(msg.to_json())
            except Exception:
                pass
        break



async def leave_channel(url):
    try:
        entety = await client.get_entity(url)
        print(entety.to_json())
        await client(channels.LeaveChannelRequest(channel=entety.id))
    except Exception as e:
        print(e)


async def send_reaction_on_story(url):
    try:
        peer, id = url.split('/s/')
        print(peer)
        print(id)
        await client(stories.SendReactionRequest(
            peer=peer,
            story_id=int(id),
            reaction=types.ReactionEmoji(emoticon='❤️')
        ))
    except Exception as ex:
        print(ex)


async def send_start_message(url):
    await client.send_message(entity=url, message='/start')


async def main():
    while True:
        await subscribe_on_channels()
        for channel in range(len(chnls)):
            try:
                url = chnls[channel][1]
                entity = await client.get_entity(url)
                await read_messages_and_set_reactions(channel, entity)
            except Exception:
                pass


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # loop.run_until_complete(send_start_message(url))
    # sleep(1)
    # loop.run_until_complete(read_messages_and_set_reactions())
    for i in urls:
        loop.run_until_complete(bot(i))
    # loop.run_until_complete(send_reaction_on_story('https://t.me/toplesofficial/s/78'))
    # loop.run_until_complete(main())
# loop.run_until_complete(leave_channel(chnls[0][1]))
