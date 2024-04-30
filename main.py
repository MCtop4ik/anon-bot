import asyncio
import dataclasses
import datetime
import logging
import sys
from functools import wraps
from queue import PriorityQueue
from tokenize import String

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from functools import wraps

TOKEN = '6458361579:AAGIClCCdj5FLHS8mJ9dfIvEQGTWhCmH20o'

bot = Bot(token=TOKEN)
dp = Dispatcher()


def session_commit(func):
    @wraps(func)
    def wrapper(self, **kwargs):
        session = self.Session()
        try:
            result = func(self, session, **kwargs)
            session.commit()
            return result
        except:
            session.rollback()
            raise
        finally:
            session.close()

    return wrapper


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Models:
    engine = create_engine('sqlite:///database/database.db')
    Base = declarative_base()

    class User(Base):
        __tablename__ = 'users'

        id = Column(Integer, primary_key=True)
        name = Column(String)
        age = Column(Integer)

    class Channel(Base):
        __tablename__ = 'channel'
        id = Column(Integer, primary_key=True)
        user_id_1 = Column(Integer)
        user_id_2 = Column(Integer)


class Database(Models, metaclass=SingletonMeta):

    def __init__(self):
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        self.Base.metadata.create_all(self.engine)

    @session_commit
    def add_user_data(self, session, **kwargs):
        name = kwargs['name']
        age = kwargs['age']
        new_user = self.User(name=name, age=age)
        session.add(new_user)

    @session_commit
    def create_channel(self, session, **kwargs):
        user_id_1 = kwargs['user_id_1']
        user_id_2 = kwargs['user_id_2']
        new_channel = self.Channel(user_id_1=user_id_1, user_id_2=user_id_2)
        session.add(new_channel)
        session.flush()
        return new_channel.id

    def get_channels_data(self):
        session = self.Session()
        try:
            channels = session.query(self.Channel).all()
            return channels
        finally:
            session.close()

    def get_channel_data(self, channel_id):
        session = self.Session()
        try:
            channel = session.query(self.Channel).filter_by(id=channel_id).first()
            return channel
        finally:
            session.close()

    def return_base(self):
        return self.Base


class TalkingChannel:

    def __init__(self, user_id_1, user_id_2):
        self.database = Database()
        self.user_id_1 = user_id_1
        self.user_id_2 = user_id_2
        self.channel_id = self.create_channel()
        self.chat_logs = []

    def create_channel(self):
        channel_id = self.database.create_channel(user_id_1=self.user_id_1, user_id_2=self.user_id_2)
        return channel_id

    @property
    def channel_id(self):
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value):
        self._channel_id = value

    def get_companion(self, user_id):
        if user_id == self.user_id_1:
            return self.user_id_2
        if user_id == self.user_id_2:
            return self.user_id_1
        raise ValueError('User id not in this chat')


class ChannelsController(metaclass=SingletonMeta):

    def __init__(self):
        self.all_channels = list()
        self.user_chat = dict()

    def add_in_channel(self, user_id_1, user_id_2):
        channel = TalkingChannel(user_id_1, user_id_2)
        self.all_channels.append(channel)
        self.user_chat[user_id_1] = channel.channel_id
        self.user_chat[user_id_2] = channel.channel_id

    def check_is_user_active(self, user):
        return user in self.user_chat.keys()


@dataclasses.dataclass(order=True)
class QueueData:
    user_id: int
    time: datetime.datetime


class UsersQueue(PriorityQueue):

    def __init__(self):
        super().__init__()
        self.channel_controller = ChannelsController()

    def add_user(self, user_id):
        print(self.channel_controller.check_is_user_active(user_id))
        if self.channel_controller.check_is_user_active(user_id):
            return

        adding_data = QueueData(
            user_id=user_id,
            time=datetime.datetime.now()
        )
        print(adding_data)
        self.put(adding_data)
        if len(self.queue) > 1:
            self.start_dialog()

    def start_dialog(self):
        user_id_1 = self.queue.pop()
        user_id_2 = self.queue.pop()
        ChannelsController().add_in_channel(user_id_1, user_id_2)

    def show_queue(self):
        print(self.queue)


class MessageSender:

    def __init__(self):
        self.channel_controller = ChannelsController()
        self.database = Database()

    def user_passer(self, user_id) -> Column[int]:
        channel_id = self.channel_controller.user_chat[user_id]
        channel = self.database.get_channel_data(channel_id)
        print(channel)
        speaker_id = channel.user_id_2 if user_id == channel.user_id_1 else channel.user_id_1
        return speaker_id


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!")


#
# @dp.message(Command('test'))
# async def test(message: Message):
#     print(message.from_user)
#     await message.answer("This is a test message." + message.text)

@dp.message(Command('queue'))
async def test(message: Message):
    users_queue.add_user(message.from_user.id)
    users_queue.show_queue()
    print(message.from_user)
    await message.answer("You have added in queue" + message.text)


@dp.message()
async def message_handler(message: Message) -> None:
    try:
        print(message.sticker)
        print(message.author_signature)
        user_id = message.from_user.id
        if ChannelsController().check_is_user_active(user_id):
            print(user_id)
            await bot.send_message(user_id, "Вы не в диалоге")
        # user_id = 5422839870
        else:
            send_user = MessageSender().user_passer(user_id)
            await bot.send_message(send_user, message.text)
        # await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Ошибка!")


async def main() -> None:
    await dp.start_polling(bot)


users_queue = UsersQueue()


def test():
    q = UsersQueue()
    print(q.__dict__)
    q.add_user('senya')
    db = Database()
    db.create_tables()
    db.add_user_data(name='Arseniy', age='16')


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
    # test()
