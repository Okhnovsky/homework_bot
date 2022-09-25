from dotenv import load_dotenv
from exceptions import APIErrException, NotSendMessage
from http import HTTPStatus
import logging
import os
import requests
import sys
import time
import telegram


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logging.info(f'Бот отправил сообщение: {message}')
    except Exception as error:
        raise NotSendMessage(f'Бот не отправил собщение "{error}"')


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException:
        raise APIErrException('Ошибка доступа к эндпоинту')

    if response.status_code != HTTPStatus.OK:
        message = (
            f'Эндпоинт {ENDPOINT} недоступен, '
            f'http status: {response.status_code}'
        )
        raise APIErrException(message)
    return response.json()


def check_response(response):
    """Функция проверки корректности ответа API Яндекс.Практикум."""
    if 'homeworks' not in response:
        raise TypeError('Отсутствует значение "homeworks"')

    hw_list = response['homeworks']

    if not isinstance(hw_list, list):
        message = (
            'Значение "homeworks" соответствует'
            f'"{type(hw_list)}" , а не "list"'
        )
        raise APIErrException(message)
    return hw_list


def parse_status(homework):
    """Функция, проверяющая статус домашнего задания."""
    if 'homework_name' in homework:
        homework_name = homework.get('homework_name')
    else:
        raise KeyError('Отсутсвует ключ "homework_name"')
    homework_status = homework.get('status')

    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError:
        message = (
            'API вернул'
            f'неизвестный статус {homework_status} для "{homework_name}"'
        )
        raise APIErrException(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функция проверки наличия токена и чат id телеграмма."""
    tokens = {
        'practicum_token': PRACTICUM_TOKEN,
        'telegram_token': TELEGRAM_TOKEN,
        'telegram_chat_id': TELEGRAM_CHAT_ID,
    }
    return all(tokens.values())


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        filename=os.path.join(os.path.dirname(__file__), 'main.log'),
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )

    if not check_tokens():
        logging.critical('Прблема с check_tokens()')
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            hw_list = check_response(response)
            if len(hw_list) > 0:
                send_message(bot, parse_status(hw_list[0]))
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except APIErrException as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
