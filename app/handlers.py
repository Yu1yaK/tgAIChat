from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.database.requests as rq
import app.keybords as kb
import app.payment as pay
import app.gpt as gpt


router = Router()
from main import bot


class Stasus(StatesGroup):
    number = State()
    dialog = State()
    now_pay = State()
    rubles = State()

message_storage = {}



@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == Stasus.dialog:
        await message.answer("Вы уже начали диалог, вы не можете использовать эту команду сейчас")
    elif current_state == Stasus.rubles or current_state == Stasus.now_pay:
        await message.answer("Вы начали оплату. Пожалуйста, завершите оплату, прежде чем использовать другие команды")
    elif await rq.have_user(message.from_user.id):
        if current_state != Stasus.number:
            await state.set_state(Stasus.number)
            await message.answer('Здравствуйте. Я - телеграмм бот, и постараюсь помочь Вам. Я могу напиисать статью, эссе, код, найти рецепт, решить пример и многое другое\n\n' +
                                'Для продолжения работы подтвердите Ваш номер телефона', reply_markup=kb.get_number)
        else:
            await message.answer('Пожалуйста, отправьте ваш номер телефона, используя кнопку ниже', reply_markup=kb.get_number)
    else:
        await message.answer('Выберите необходимую опцию ниже', reply_markup=kb.main)

@router.message(Stasus.number, F.contact)
async def Stasus_number(message: Message, state: FSMContext):
    await state.update_data(number=message.contact.phone_number)
    data = await state.get_data()
    await rq.set_user(message.from_user.id, data["number"])
    await message.answer('Регистрация успешно выполнена.\n\nВы можете узнать свой баланс используя кнопку "Статус". ' +
                          'Кнопка "Пополнить баланс" позволит Вам пополнить баланс своего аккаунта. Кнопка "Начать диалог" запускает диалог со мной при положительном балансе. ' +
                          'Одно сообщение стоит один рубль.\n\nВыберите необходимую опцию ниже', reply_markup=kb.main)
    await state.clear()

@router.message(Stasus.number)
async def handle_other_messages(message: Message):
    await message.answer('Пожалуйста, отправьте ваш номер телефона, используя кнопку ниже\n\nЕсли кнопка отсутсвует, то можете воспользоваться командой\n\n/start')




@router.message(Stasus.dialog, F.text == 'Закончить')
async def stop_dialog(message: Message, state: FSMContext): 
    await message.answer('Ваш дилог закончен. История очищена', reply_markup=kb.main)
    await rq.update_history(message.from_user.id, [])
    await state.clear()

@router.message(Stasus.dialog, F.text == 'Приостановить')
async def pause_dialog(message: Message, state: FSMContext): 
    await message.answer('Ваш дилог приостановлен. Можете вернуться к нему в любое время', reply_markup=kb.main)
    await state.clear()

@router.message(Stasus.dialog, F.text == 'Очистить историю')
async def clear_dialog(message: Message): 
    await message.answer('История диалога очищена')
    await rq.update_history(message.from_user.id, [])
    
@router.message(Stasus.dialog)
async def dialog(message: Message):
    if await rq.get_balance(message.from_user.id) < 1:
        await message.answer("На счёте недостаточно средств, пополните баланс")
    else:
        processing_message = await message.answer("Ваш запрос обрабатывается...")
        answer = await gpt.ask_gpt(message.text, message.from_user.id)
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
        await message.answer(answer, parse_mode='Markdown')
        await rq.update_balance_dialog(message.from_user.id)

@router.message(Stasus.dialog)
async def handle_invalid_commands(message: Message):
    await message.answer("Вы начали диалог. Пожалуйста, завершите диалог, прежде чем использовать другие команды")



@router.message(Stasus.rubles)
async def handle_integer_message(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer('Необходимо ввести целое число!')
        return
    
    chat_id = message.chat.id
    message_id = message_storage.pop(chat_id)
    await message.chat.delete_message(message_id)

    await state.update_data(amount=amount)
    await state.set_state(Stasus.now_pay)
    payment_url, payment_id = pay.create(amount, message.chat.id)
    processing_message = await message.answer('Счёт сформирован', reply_markup=kb.create_payment_keyboard(payment_url, payment_id))
    message_storage[message.chat.id] = processing_message.message_id

@router.callback_query(lambda c: 'rubles' in c.data, Stasus.rubles)
async def top_up_balance(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    message_id = message_storage.pop(chat_id)
    await callback.message.chat.delete_message(message_id)
    
    amount = int(callback.data.split('_')[1])
    await state.update_data(amount=amount)
    await callback.answer('Сумма выбрана')
    await state.set_state(Stasus.now_pay)
    payment_url, payment_id = pay.create(amount, callback.message.chat.id)
    processing_message = await callback.message.answer('Счёт сформирован', reply_markup=kb.create_payment_keyboard(payment_url, payment_id))
    message_storage[callback.message.chat.id] = processing_message.message_id

@router.callback_query(F.data == 'end_status', Stasus.rubles)
async def end_status(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    message_id = message_storage.pop(chat_id)
    await callback.message.chat.delete_message(message_id)
    
    await callback.answer('Оплата отменена')
    await state.clear()

@router.message(Stasus.rubles)
async def handle_invalid_commands(message: Message):
    await message.answer("Вы начали оплату. Пожалуйста, завершите оплату, прежде чем использовать другие команды")



@router.callback_query(lambda c: 'check' in c.data, Stasus.now_pay)
async def check_pay_status(callback: CallbackQuery, state: FSMContext):
    result = pay.check(callback.data.split('_')[-1])
    if result:
        data = await state.get_data()
        amount = data.get('amount')
        await state.clear()

        chat_id = callback.message.chat.id
        message_id = message_storage.pop(chat_id)
        await callback.message.chat.delete_message(message_id)
        await callback.answer('Платёж успешно прошёл', show_alert=True)
        await rq.update_balance_pay(callback.from_user.id, amount)
    else:
        await callback.answer('Оплата еще не прошла или возникла ошибка', show_alert=True)

@router.callback_query(lambda c: 'close' in c.data, Stasus.now_pay)
async def close_pay(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        amount = data.get('amount')
        await state.clear()

        chat_id = callback.message.chat.id
        message_id = message_storage.pop(chat_id)
        await callback.message.chat.delete_message(message_id)
        
        result = pay.check(callback.data.split('_')[-1])
        if result:
            await callback.answer('Платёж успешно прошёл', show_alert=True) 
            await rq.update_balance_pay(callback.from_user.id, amount)
        else:
            await callback.answer('Оплата отменена', show_alert=True)

@router.message(Stasus.now_pay)
async def handle_invalid_commands(message: Message):
    await message.answer("Вы начали оплату. Пожалуйста, завершите оплату, прежде чем использовать другие команды")




@router.message(F.text == 'Статус')
async def get_status(message: Message):
    await message.answer(f'Ваш номер телефона: {await rq.get_number(message.from_user.id)}\nВаш баланс: {await rq.get_balance(message.from_user.id)} руб')

@router.message(F.text == 'Начать диалог')
async def start_dialog(message: Message, state: FSMContext):
    if await rq.get_balance(message.from_user.id) < 1:
        await message.answer("На счёте недостаточно средств, пополните баланс")
    else:
        await state.set_state(Stasus.dialog)
        await message.answer('Ваш дилог начат', reply_markup=kb.dialog)

@router.message(F.text == 'Пополнить баланс')
async def choose_rubles(message: Message, state: FSMContext):
    processing_message = await message.answer('Выберите сумму для пополнения или отправьте в сообщении:', reply_markup = kb.rubles)
    message_storage[message.chat.id] = processing_message.message_id
    await state.set_state(Stasus.rubles)
