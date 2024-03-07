import asyncio
import datetime
import os
import random

from telethon import TelegramClient
from telethon.tl.functions import photos

import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
from app.models import API
async def update_my_photo(client):
    await client.download_profile_photo('me', 'user.jpg')
    await client(photos.DeletePhotosRequest(await client.get_profile_photos('me')))
    await client(photos.UploadProfilePhotoRequest(file=await client.upload_file('user.jpg')))


async def update_donor_photo(client, api):
    try:
        a = await client.get_profile_photos(api.username)
        if str(a[0].id) == api.last_photo_id:
            api.try_count += 1
            api.save()
            if api.try_count >= random.randint(4, 6):
                await client.download_media(random.choice(a), 'donor.jpg')
                await client(photos.DeletePhotosRequest(await client.get_profile_photos('me')))
                await client(photos.UploadProfilePhotoRequest(file=await client.upload_file('donor.jpg')))
        else:
            api.try_count = 0
            api.save()
            await client.download_profile_photo(api.username, 'donor.jpg')
            await client(photos.DeletePhotosRequest(await client.get_profile_photos('me')))
            await client(photos.UploadProfilePhotoRequest(file=await client.upload_file('donor.jpg')))
    except Exception as ex:
        print(f'update_donor_photo {ex}')
        await update_my_photo(client)


async def activate_user(api):
    client = TelegramClient(f'session/{api.id}', api_id=api.api_id, api_hash=api.api_hash,
                            system_version="4.16.30-vxCUSTOM")
    await client.start(phone=api.phone)
    return client


async def start():
    apis = API.objects.all()
    for api in apis:
        if datetime.datetime.now() <= api.next_update_photo_time:
            client = await activate_user(api)
            await update_donor_photo(client)
            next_update_photo_time = datetime.datetime.now() + datetime.timedelta(minutes=random.randint(6*24*60,8*24*60))
            api.next_update_photo_time = next_update_photo_time
