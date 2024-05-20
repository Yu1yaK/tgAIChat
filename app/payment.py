import os
import uuid
from yookassa import Configuration, Payment
from dotenv import load_dotenv


load_dotenv()
Configuration.account_id = str(os.getenv('ACCOUNT_ID'))
Configuration.secret_key = str(os.getenv('SECRET_KEY'))

def create(amount, chat_id):
    payment = Payment.create({
        "amount": {
            "value": amount,
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/tgAIChatMy_BOT"
        },
        "capture": True,
        "metadata": {
            'chat_id': chat_id
        },
        "description": "Пополнение баланса"
    }, uuid.uuid4())

    return payment.confirmation.confirmation_url, payment.id

def check(payment_id):
    payment = Payment.find_one(payment_id)
    if payment.status == 'succeeded':
        return payment.metadata
    else:
        return False