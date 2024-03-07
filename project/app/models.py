from django.db import models


class API(models.Model):
    phone = models.CharField(max_length=16, verbose_name='Номер телефона')
    gender = models.CharField(max_length=16, verbose_name='Пол')
    username = models.CharField(max_length=128, verbose_name='Ник донора для фоток')
    api_id = models.CharField(max_length=32, verbose_name='ID из инструментов разработчика')
    api_hash = models.CharField(max_length=64, verbose_name='Hash из инструментов разработчика')


class User(models.Model):
    username = models.CharField(max_length=64, default='', null=True, verbose_name='Ник пользователя')
    tg_id = models.CharField(max_length=64, verbose_name='Id пользователя в телеграмме')
    action = models.CharField(max_length=128, default='', null=True, verbose_name='Действия пользхователя')
    orders = models.ManyToManyField('Orders', verbose_name='Заказы пользователя')
    create_order = models.CharField(max_length=256, default='', blank=True, null=True,
                                    verbose_name='Поля для создания ордера')


class Orders(models.Model):
    url = models.CharField(max_length=256, verbose_name='Url')
    apis = models.ManyToManyField('API', verbose_name='Исполнители заказа')
    number_wave = models.IntegerField(default=0, verbose_name='Номер волны подписок')
    gender = models.CharField(max_length=4, verbose_name='Пол исполнителя')
    subscribe = models.PositiveIntegerField(default=0, verbose_name='Сколько подписалось')
    next_action_time = models.DateTimeField(blank=True, null=True, verbose_name='Время Следующего действия')
    start = models.DateTimeField(verbose_name='Дата начала исполнения заказа')
    end = models.DateTimeField(verbose_name='Дата окончания выполнения заказа')


class WaveTime(models.Model):
    first = models.IntegerField(default=30,
                                verbose_name='Сколько минимально должно пройти времени для того, чтобы подписался еще один чловек в первой волне')
    second = models.IntegerField(default=60,
                                verbose_name='Сколько минимально должно пройти времени для того, чтобы подписался еще один человек во второй волне')
    third = models.IntegerField(default=120,
                                verbose_name='Сколько минимально должно пройти времени для того, чтобы подписался еще один человек в третьей волне')
