import logging
import aiogram
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from db import *
from aiogram.types.web_app_info import WebAppInfo


API_TOKEN = '6095169791:AAEQM5y8u1IPLPMhvOZDVQlqTDSMAadjmL0'  # Replace with your API token


        
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)




from sqlalchemy import func
class CheckUserState(StatesGroup):
    put_number = State()
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message, state: FSMContext):
    db_user = db.query(User).filter(User.tg_id == message.from_user.id).first()
    if db_user:
        kb = types.InlineKeyboardMarkup()
        all_groups_of_qestions = db.query(GroupQuestion).all()
        if db_user.is_superuser:
            create_post = types.InlineKeyboardButton(text="Создать Пост", web_app=WebAppInfo(url="https://vladlenkhan.github.io/minzifa/"))
            kb.add(create_post)

        for group in all_groups_of_qestions:
            kb.add(types.InlineKeyboardButton(text=f"{group.name}", callback_data=f"get_questions_of_group:{group.id}"))

        await message.answer(text=f"Здравствуйте, {db_user.first_name} {db_user.last_name}\n\nВыберите тематику вопроса:", reply_markup=kb)
    else:    
        await message.answer("Введите номер телефона:\n*Включительно '+998/+7' и без пробелов!\nНапример:\n+998905553535\n+79015553535")
        await CheckUserState.put_number.set()
        

@dp.message_handler(state=CheckUserState.put_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    phone_number = message.text
    db_user = db.query(User).filter(User.phone_number == phone_number).first()

    if db_user:
        db_user.tg_id = message.from_user.id
        db_user.username = message.from_user.username or "Скрытый username"
        db_user.first_name = message.from_user.first_name or "Скрытое имя"
        db_user.last_name = message.from_user.last_name or "Скрытая фамилия"
        db.commit()

        kb = types.InlineKeyboardMarkup()
        all_groups_of_qestions = db.query(GroupQuestion).all()
        if db_user.is_superuser:
            create_post = types.InlineKeyboardButton(text="Создать Пост", web_app=WebAppInfo(url="https://vladlenkhan.github.io/minzifa/"))
            kb.add(create_post)

        for group in all_groups_of_qestions:
            kb.add(types.InlineKeyboardButton(text=f"{group.name}", callback_data=f"get_questions_of_group:{group.id}"))
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        edit_success = False
        while not edit_success and message.message_id > 0:
            try:
                await bot.edit_message_text(chat_id=message.from_user.id, message_id=message.message_id - 1, text=f"Здравствуйте, {db_user.first_name} {db_user.last_name}\n\nВыберите тематику вопроса:", reply_markup=kb)
                edit_success = True
            except aiogram.utils.exceptions.MessageToEditNotFound:
                message.message_id -= 1
        await state.finish()
    else:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        edit_success = False
        while not edit_success and message.message_id > 0:
            try:
                await bot.edit_message_text(chat_id=message.from_user.id, message_id=message.message_id - 1, text="Номер введен неправильно или у вас нет доступа!\nВведите номер еще раз!\nВключительно '+998/+7' и без пробелов!\n Например: <b>+998905553535</b>\n\nНапишите о проблеме Администратору @UnLuckyLoX", parse_mode="HTML")
                edit_success = True
            except aiogram.utils.exceptions.MessageToEditNotFound:
                message.message_id -= 1

        await CheckUserState.put_number.set()




    

class QuestionState(StatesGroup):
    choice = State()
@dp.callback_query_handler(lambda c: c.data.startswith('get_questions_of_group:'))
async def get_all_questions_for_group(callback_query: types.CallbackQuery, state: FSMContext):
    group_id = int(callback_query.data.split(':')[-1])

    group = db.query(GroupQuestion).filter(GroupQuestion.id == group_id).first()

    if len(group.questions) == 1:
        # The group has only an answer, no questions
        text = (
            f"Ответ:\n"
            f"<u>{group.name}</u>\n"
            f"{group.questions[0].answer}"
            )
    else:
        # The group has questions
        all_questions = db.query(Question).filter(Question.group_id == group_id).all()

        text = ""
        for question in all_questions:
            text += f"{question.question_number}. {question.question}\n"

        text += "\nНапишите номер вопроса, чтобы получить ответ."

    kb = types.InlineKeyboardMarkup()
    back_to_topics = types.InlineKeyboardButton("Тематики", callback_data="back_to_topics_for_questions")
    kb.add(back_to_topics)
    await callback_query.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await state.update_data(group_id=group_id)
    await QuestionState.choice.set()

@dp.message_handler(state=QuestionState.choice)
async def get_answer_for_question(message: types.Message, state: FSMContext):
    try:
        question_number = int(message.text)
        if question_number <= 0:
            raise ValueError
    except ValueError:
        await message.reply("Некорректный номер вопроса. Пожалуйста, введите правильный номер.")
        return

    data = await state.get_data()
    group_id = data.get('group_id')

    answer = db.query(Question).filter(Question.question_number == question_number).first()

    if not answer:
        await message.reply("Вопрос с указанным номером не найден. Пожалуйста, введите правильный номер.")
        return

    if answer.group_id != group_id:
        await message.reply("Вопрос с указанным номером не принадлежит выбранной группе. Пожалуйста, введите правильный номер.")
        return
    
    
    # Update the message_text with the new horizontal line
    message_text = (
        f"Ответ на вопрос:\n"
        f"<u>{question_number}.{answer.question}</u>\n"
        
        f"{answer.answer}"
    )
    kb = types.InlineKeyboardMarkup()
    back_to_topics = types.InlineKeyboardButton("Тематики", callback_data="back_to_topics_for_questions")
    back_to_questions = types.InlineKeyboardButton("Назад", callback_data=f"get_questions_of_group:{group_id}")
    kb.add(back_to_questions).add(back_to_topics)
    await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
    edit_success = False
    while not edit_success and message.message_id > 0:
        try:
            await bot.edit_message_text(chat_id=message.from_user.id, message_id=message.message_id - 1, text=message_text, reply_markup=kb, parse_mode="HTML")
            edit_success = True
        except aiogram.utils.exceptions.MessageToEditNotFound:
            message.message_id -= 1


    await state.reset_state(with_data=False)
    await state.finish()




@dp.callback_query_handler(lambda c: c.data == "back_to_topics_for_questions", state='*')
async def get_topics_for_questions_again(callback_query: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    all_groups_of_questions = db.query(GroupQuestion).all()
    db_user = db.query(User).filter(User.tg_id == callback_query.from_user.id).first()
    if db_user.is_superuser:
        create_post = types.InlineKeyboardButton(text="Создать Пост", web_app=WebAppInfo(url="https://vladlenkhan.github.io/minzifa/"))
        kb.add(create_post)

    for group in all_groups_of_questions:
        kb.add(types.InlineKeyboardButton(text=f"{group.name}", callback_data=f"get_questions_of_group:{group.id}"))

    await callback_query.message.edit_text("Выберите тематику вопроса:", reply_markup=kb, parse_mode="HTML")
    await state.reset_state(with_data=False)
    await state.finish()



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)