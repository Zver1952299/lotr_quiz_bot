import aiosqlite
from aiogram import Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from questions import quiz_data
from settings import DB_NAME


dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text='Начать игру'))
    builder.add(types.KeyboardButton(text='Статистика'))
    await message.answer(('Привет! Это квиз по вселенной "Властелин колец". Для старта введите "/quiz", либо нажмите "Начать игру"'), reply_markup=builder.as_markup(resize_keyboard=True))


async def get_question(message, user_id):
    current_question_index = await get_data_from_db(user_id, 'question_index')
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']

    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    current_right_answers = 0
    await update_quiz_index(user_id, current_question_index, current_right_answers)
    await get_question(message, user_id)


async def get_data_from_db(user_id, data):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(f'SELECT {data} FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            result = await cursor.fetchone()
            if result is not None:
                return result[0]
            else:
                return 0


async def update_quiz_index(user_id, index, right_answers):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index, right_answers) VALUES (?, ?, ?)', (user_id, index, right_answers))
        await db.commit()


def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=f"r {option}" if option == right_answer else f"w {option}")
        )

    builder.adjust(1)
    return builder.as_markup()


@dp.message(F.text == 'Начать игру')
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer('Давайте начнем квиз')
    await new_quiz(message)


@dp.message(F.text == 'Статистика')
@dp.message(Command("stat"))
async def get_stat(message: types.Message):
    current_right_answers = await get_data_from_db(message.from_user.id, 'right_answers')
    await message.answer(f'Ваш последний результат: {current_right_answers} из {len(quiz_data)}')


async def create_table():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER, right_answers INTEGER)''')
        await db.commit()


@dp.callback_query(F.data[:1] == "r")
async def right_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    current_question_index = await get_data_from_db(callback.from_user.id, 'question_index')
    current_right_answers = await get_data_from_db(callback.from_user.id, 'right_answers')

    await callback.message.answer(f"Ваш ответ: {callback.data[2:]}. Верно!")

    current_question_index += 1
    current_right_answers += 1
    await update_quiz_index(callback.from_user.id, current_question_index, current_right_answers)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Ваш результат: {current_right_answers} из {len(quiz_data)}")


@dp.callback_query(F.data[:1] == "w")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    current_question_index = await get_data_from_db(callback.from_user.id, 'question_index')
    current_right_answers = await get_data_from_db(callback.from_user.id, 'right_answers')

    correct_option = quiz_data[current_question_index]['correct_option']

    await callback.message.answer(f"Неправильно. Ваш ответ: {callback.data[2:]}. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    current_question_index += 1
    current_right_answers += 0
    await update_quiz_index(callback.from_user.id, current_question_index, current_right_answers)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Ваш результат: {current_right_answers} из {len(quiz_data)}")
