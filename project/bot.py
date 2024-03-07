import asyncio
import datetime
import os
import random
import threading

import telethon
import telebot
import channels
import avatar

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telethon import TelegramClient
import validators
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
from app.models import API, User, Orders

API_TOKEN = '6825127387:AAGZbujn5d0wdr9eyIXG3E3Yfr8tKxCC13c'
bot = telebot.TeleBot(API_TOKEN)
admins_id = ['595650100', '1288389919']
loop = asyncio.new_event_loop()
lp1 = asyncio.new_event_loop()
lp2 = asyncio.new_event_loop()
phone_code_hash = [0]


def create_user(chat_id, username):
    user = User.objects.create(username=username, tg_id=chat_id)
    return user


def button():
    markup = InlineKeyboardMarkup(row_width=1)
    urlButton = InlineKeyboardButton(text='Создать заказ', callback_data='create_order')
    my_orders = InlineKeyboardButton(text='Мои заказы', callback_data='my_orders')
    markup.add(urlButton)
    markup.add(my_orders)
    return markup


def menu(chat_id):
    markup = button()
    bot.send_message(chat_id=chat_id, text='Главное меню', reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    print(message.chat.id)
    chat_id = message.chat.id
    try:
        user = User.objects.get(tg_id=chat_id)
    except Exception:
        username = message.from_user.username
        user = create_user(chat_id=chat_id, username=username)
    menu(chat_id=chat_id)


async def activate(code, chat_id, api):
    client = TelegramClient(f'session/{api.id}', api_id=api.api_id, api_hash=api.api_hash,
                            system_version="4.16.30-vxCUSTOM")
    await client.connect()
    try:
        await client.sign_in(api.phone, code=code, phone_code_hash=str(phone_code_hash[0]))
    except telethon.errors.SessionPasswordNeededError:
        password = '19097007'
        await client.sign_in(password=password)
        bot.send_message(chat_id=chat_id, text='Аккаунт успешно активирован')


async def send_code(api, phone):
    client = TelegramClient(f'session/{api.id}', api_id=api.api_id, api_hash=api.api_hash,
                            system_version="4.16.30-vxCUSTOM")
    await client.connect()
    code = await client.send_code_request(phone, force_sms=False)
    phone_code_hash[0] = code.phone_code_hash


def add_account(message, user):
    chat_id = user.tg_id
    code, phone, gender, username, api_id, api_hash = message.split()
    phone = f'+{phone}'
    next_update_photo_time = datetime.datetime.now() + datetime.timedelta(
        minutes=random.randint(1 * 24 * 60, 4 * 24 * 60))
    api = API.objects.create(phone=phone, gender=gender, username=username, api_id=api_id, api_hash=api_hash,
                             next_update_photo_time=next_update_photo_time)
    user.action = f'code|{api.id}'
    user.save()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_code(api, phone))
    bot.send_message(chat_id=chat_id, text=f'Введите код для аккаунта номер {api.id}')


@bot.message_handler(content_types='text')
def input(message):
    chat_id = message.chat.id
    user = User.objects.get(tg_id=chat_id)
    action = user.action.split('|')[0]
    if message.text == 'Меню':
        user.action = ''
        user.create_order = ''
        user.save()
    elif action == 'code':
        api_id = user.action.split('|')[1]
        user.action = ''
        user.save()
        code = message.text
        api = API.objects.get(id=api_id)
        loop.run_until_complete(activate(code, chat_id, api, ))
    elif action == 'choose_gender':
        gender = {
            'Женский': '1',
            'Мужской': '2',
            'Любой': '3',
        }
        text = message.text
        if text == 'Меню':
            menu(chat_id=chat_id)
        else:
            try:
                gndr = gender[text]
            except KeyError:
                choose_gender(chat_id=chat_id, user=user, error='❌Ошибка❌\n')
            else:
                user.action = f'send_link'
                user.create_order = gndr
                user.save()
                send_link(chat_id=chat_id)
    if action == 'send_link':
        url = message.text
        if validators.url(url) and 'https://t.me/' in url and not Orders.objects.filter(url=url):
            user.action = f'choose_user'
            user.create_order += f'|{url}'
            user.save()
            choose_users(chat_id=chat_id)
        else:
            send_link(chat_id=chat_id, error='❌Ошибка, ссылка не валидна или уже используется❌\n')
    if action == 'choose_user':
        try:
            count = int(message.text)
        except Exception:
            choose_users(chat_id=chat_id, error='❌Ошибка. Введите число❌\n')
        else:
            if count > len(API.objects.all()):
                count = len(API.objects.all())
            user.action = 'get_date'
            user.create_order += f'|{count}'
            user.save()
            get_start_date(chat_id=chat_id)
    if action == 'get_date':
        try:
            hours = abs(int(message.text))
        except Exception:
            get_start_date(chat_id=chat_id, error='❌Ошибка. Введите число❌\n')
        else:
            gender, url, users = user.create_order.split('|')
            date = datetime.datetime.now() + datetime.timedelta(hours=hours)
            end_date = date + datetime.timedelta(days=30)
            if gender == '1' or gender == '2':
                api = API.objects.filter(gender=gender)
                if len(api) < users:
                    users = len(api)
                apis = random.choices(API.objects.filter(gender=gender), k=int(users))
            else:
                apis = random.choices(API.objects.all(), k=int(users))
            order = Orders.objects.create(
                url=url,
                gender=gender,
                start=date,
                end=end_date
            )
            for i in apis:
                order.apis.add(i)
            user.orders.add(order)
            bot.send_message(chat_id=chat_id, text='Канал успешно добвален')
            menu(chat_id=chat_id)
    if 'YWN0aXZhdF9hY2NvdW50X2FsbA' in message.text:
        add_account(message.text, user)


def get_start_date(chat_id, error=''):
    markup = InlineKeyboardMarkup()
    menu = InlineKeyboardButton(text='Меню', callback_data='menu')
    markup.add(menu)
    text = f'{error}Выберите на сколько часов требуется отложить выполнение задания. Если это не требуется - введите 0'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def choose_users(chat_id, error=''):
    markup = InlineKeyboardMarkup()
    menu = InlineKeyboardButton(text='Меню', callback_data='menu')
    markup.add(menu)
    text = f'{error}Введите количество пользователей, которым нужно подписаться на ваш канал/группу/бота\n' \
           f'Максимум - {API.objects.all().count()}'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def send_link(chat_id, error=''):
    markup = InlineKeyboardMarkup()
    menu = InlineKeyboardButton(text='Меню', callback_data='menu')
    markup.add(menu)
    text = f'{error}Отправте ссылку на канал/группу/бота'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def choose_gender(chat_id, user, error=''):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    male = KeyboardButton(text='Мужской')
    female = KeyboardButton(text='Женский')
    universal = KeyboardButton(text='Любой')
    menu = KeyboardButton(text='Меню')
    markup.add(male, female, universal, menu)
    text = f'{error}Выберите пол пользователей, которые будут подписываться'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
    user.action = 'choose_gender'
    user.save()


def my_orders(chat_id, users):
    text = 'Ваши заказы'
    markup = InlineKeyboardMarkup()
    menu = InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(menu)
    for i in users.orders.all():
        order_button = InlineKeyboardButton(f'Заках номер {i.id}', callback_data=f'order|{i.id}')
        markup.add(order_button)
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)

def my_order(chat_id, order):
    text = f'Номер заказа: {order.id}' \
           f'URL заказа: {order.url}\n' \
           f'Сколько подписалось: {order.subscribe}/{order.apis.count()}\n' \
           f'Дата окончания: {order.end}'
    markup = InlineKeyboardMarkup()
    menu = InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(menu)
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    username = call.from_user.first_name
    message_id = call.message.id
    chat_id = call.message.chat.id
    user = User.objects.get(tg_id=chat_id)
    user.action = ''
    user.create_order = ''
    user.save()
    try:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
    if call.message:
        data = call.data
        if data == 'my_orders':
            my_orders(chat_id=chat_id, user=user)
        elif data == 'menu':
            menu(chat_id=chat_id)
        elif data.split('|')[0] == 'order':
            order_id = int(data.split('|')[1])
            order = Orders.objects.get(id=order_id)
            order_detail(chat_id, order)
        else:
            menu(chat_id=chat_id)


def avatar_start():
    lp1.run_until_complete(avatar.start())


def channels_start():
    lp2.run_until_complete(channels.start())


def start_server():
    os.system('python manage.py runserver')


def start_polling():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    polling_thread = threading.Thread(target=channels_start)
    polling_thread.start()
    channels_thread = threading.Thread(target=start_polling)
    channels_thread.start()
    avatar_thread = threading.Thread(target=avatar_start)
    avatar_thread.start()
    start_server = threading.Thread(target=start_server)
    start_server.start()
