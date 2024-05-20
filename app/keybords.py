from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Статус')],
                                     [KeyboardButton(text='Пополнить баланс')],
                                     [KeyboardButton(text='Начать диалог')]],
                                      resize_keyboard=True, 
                                      input_field_placeholder='Выберите пункт меню...')


dialog = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Приостановить')],
                                     [KeyboardButton(text='Закончить')],
                                     [KeyboardButton(text='Очистить историю')]],
                                      resize_keyboard=True, 
                                      input_field_placeholder='Выберите пункт меню...')


get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Подтвердить телефон', request_contact=True)]], resize_keyboard=True)

rubles = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='10', callback_data='rubles_10')],
                                        [InlineKeyboardButton(text='100', callback_data='rubles_100')],
                                        [InlineKeyboardButton(text='1000', callback_data='rubles_1000')],
                                        [InlineKeyboardButton(text='Отменить оплату', callback_data='end_status')]])


def create_payment_keyboard(payment_url: str, payment_id: str) -> InlineKeyboardMarkup:
    pay_buttons = [
        [InlineKeyboardButton(text='Оплатить', url=payment_url),
         InlineKeyboardButton(text='Проверить оплату', callback_data=f'check_{payment_id}')],
        [InlineKeyboardButton(text='Отменить оплату', callback_data=f'close_{payment_id}')]
    ]

    return InlineKeyboardMarkup(inline_keyboard=pay_buttons)