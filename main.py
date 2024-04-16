import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import asyncpg
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

API_TOKEN = '7101489001:AAHqTeZ-0MH79Yzdnn3mFbFycQ_xZuXH9W0'
USERNAME_BUTTON = 'Username'
EMAIL_BUTTON = 'Email'
PHONE_BUTTON = 'Phone'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

Base = declarative_base()
metadata = MetaData()
engine = create_async_engine('postgresql+asyncpg://postgres:123@localhost:5432/Tgbot')
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

markup = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text=USERNAME_BUTTON),
        KeyboardButton(text=EMAIL_BUTTON),
        KeyboardButton(text=PHONE_BUTTON)
    ]
],
    )
buttons = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Актуальные работы", callback_data="latest_jobs"),
        InlineKeyboardButton(text="Последняя выполненная работа", callback_data="last_completed_job"),
        InlineKeyboardButton(text="Забрать скидочный купон", callback_data="get_discount_coupon"),
    ]
]

class User(Base):
    __table__ = Table(
        'users', metadata,
        Column('id', Integer, primary_key=True),
        Column('nickname', String),
        Column('username', String),
        Column('email', String),
        Column('phone', String)
    )


class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.now)




async def validate_email(email):
    if "@" in email:
        await message.answer(f'Твоя электронная почта:\r\n{message.text}')
        return True
    else:
        return False


async def validate_phone(phone):
    if len(phone):
        await message.answer(f'Твой номер телефона:\r\n{message.text}')
        return True
    else:
        return False


@dp.message_handler(commands=['start'])
async def start(message: types.Message):

    await message.answer('Привет, пожалуйста введи свои данные', reply_markup=markup)


@dp.message_handler()
async def process_message(message: types.Message):
    user_id = message.from_user.id
    nickname = message.from_user.first_name
    state = await dp.current_state(user=user_id).get_data() and dp.current_state(nickname=user_id).get_data()

    if not state:
        state['user_id'] = user_id
        state['nickname'] = nickname

    if message.text == USERNAME_BUTTON:
        await message.answer('Введи свое имя')
        await dp.current_state(user=user_id).update_data({'next_state': 'email'})
    elif message.text == EMAIL_BUTTON:
        await message.answer('ВВеди свою почут')
        await dp.current_state(user=user_id).update_data({'next_state': 'phone'})
    elif message.text == PHONE_BUTTON:
        await message.answer('Введи свой номер телефона:')
        await dp.current_state(user=user_id).update_data({'next_state': 'save_data'})
    else:
        next_state = state.get('next_state')
        if next_state == 'email':
                state['username'] = message.text
        elif next_state == 'email':
            if await validate_email(message.text):
                state['email'] = message.text
            else:
                await message.answer('Неправильная почта, попробуй снова')
                return
        elif next_state == 'phone':
            if await validate_phone(message.text):
                state['phone'] = message.text
            else:
                await message.answer('Неправильный номер, попробуй еще раз')
                return


        async with async_session() as session:
            async with session.begin():
                user = User(id=state['user_id'], username=state['username'], email=state['email'], phone=state['phone'])
                session.add(user)
                await session.commit()

        await message.answer('Вы были зарегистрированы', reply_markup=buttons)


@dp.callback_query_handler(lambda query: query.data == 'latest_jobs')
async def latest_jobs_callback(callback_query: types.CallbackQuery):
    latest_jobs = session.query(Job).order_by(Job.created_at.desc()).limit(3).all()
    for job in latest_jobs:
        await callback_query.message.answer(f"Title: {job.title}\nDescription: {job.description}")


@dp.callback_query_handler(lambda query: query.data == 'last_completed_job')
async def last_completed_job_callback(callback_query: types.CallbackQuery):
    last_completed_job = session.query(Job).order_by(Job.created_at.desc()).first()
    await callback_query.message.answer(
        f"Title: {last_completed_job.title}\nDescription: {last_completed_job.description}")


@dp.callback_query_handler(lambda query: query.data == 'get_discount_coupon')
async def get_discount_coupon_callback(callback_query: types.CallbackQuery):
    discount_coupon_photo = "photo.jpg"
    with open(discount_coupon_photo, 'rb') as photo:
        await bot.send_photo(callback_query.from_user.id, photo)

if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    engine = create_async_engine('postgresql+asyncpg://username:password@host/dbname')
    Base.metadata.create_all(engine)
    updater = Updater(token=API_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(Command("start", start))
    dp.add_handler(MessageHandler(F.text & ~F.command, process_message))
    updater.start_polling()
    updater.idle()

