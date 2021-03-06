# импортируем библиотеки
import os
from flask import Flask, request

import logging

# библиотека, которая нам понадобится для работы с JSON
import json

# создаём приложение
# мы передаём __name__, в нем содержится информация, 
# в каком модуле мы находимся.
# В данном случае там содержится '__main__', 
# так как мы обращаемся к переменной из запущенного модуля.
# если бы такое обращение, например, 
# произошло внутри модуля logging, то мы бы получили 'logging'
app = Flask(__name__)

# Устанавливаем уровень логирования
logging.basicConfig(level=logging.INFO)

# Создадим словарь, чтобы для каждой сессии общения 
# с навыком хранились подсказки, которые видел пользователь.
# Это поможет нам немного разнообразить подсказки ответов 
# (buttons в JSON ответа).
# Когда новый пользователь напишет нашему навыку, 
# то мы сохраним в этот словарь запись формата
# sessionStorage[user_id] = {'suggests': ["Не хочу.", "Не буду.", "Отстань!" ]}
# Такая запись говорит, что мы показали пользователю эти три подсказки. 
# Когда он откажется купить слона,
# то мы уберем одну подсказку. Как будто что-то меняется :)
sessionStorage = {}


@app.route('/')
def info():
    return "Это мой навык Алисы"


@app.route('/post', methods=['POST'])
# Функция получает тело запроса и возвращает ответ.
# Внутри функции доступен request.json - это JSON, 
# который отправила нам Алиса в запросе POST
def main():
    logging.info(f'Request: {request.json!r}')

    # Начинаем формировать ответ, согласно документации
    # мы собираем словарь, который потом при помощи 
    # библиотеки json преобразуем в JSON и отдадим Алисе
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    # Отправляем request.json и response в функцию handle_dialog. 
    # Она сформирует оставшиеся поля JSON, которые отвечают
    # непосредственно за ведение диалога
    handle_dialog(request.json, response)

    logging.info(f'Response:  {response!r}')

    # Преобразовываем в JSON и возвращаем
    return json.dumps(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.
        # Запишем подсказки, которые мы ему покажем в первый раз

        sessionStorage[user_id] = {
            'suggests': [
                "Не хочу.",
                "Не буду.",
                "Отстань!",
            ], "слон": False
        }
        # Заполняем текст ответа
        # json_response = requests.get('http://127.0.0.1:8080/api/jobs/1')
        # print(json_response)
        res['response']['text'] = 'Привет! Купи слона!'
        # Получим подсказки
        res['response']['buttons'] = get_suggests(user_id)
        return

    # Сюда дойдем только, если пользователь не новый, 
    # и разговор с Алисой уже был начат
    # Обрабатываем ответ пользователя.
    # В req['request']['original_utterance'] лежит весь текст,
    # что нам прислал пользователь
    # Если он написал 'ладно', 'куплю', 'покупаю', 'хорошо', 
    # то мы считаем, что пользователь согласился.
    # Подумайте, всё ли в этом фрагменте написано "красиво"?
    t = False
    for i in ['ладно', 'куплю', 'покупаю', 'хорошо', 'я куплю', 'я покупаю']:
        if i in req['request']['original_utterance'].lower():
            t = True
    if t:
        # Пользователь согласился, прощаемся.
        if not sessionStorage[user_id]["слон"]:
            res['response']['text'] = 'Слона можно найти на Яндекс.Маркете!\nПривет! Купи кролика!'
            res['response']['buttons'] = get_suggests(user_id)
            sessionStorage[user_id] = {
                'suggests': [
                    "Не хочу",
                    "Не буду",
                    "Отстань!",
                ], "слон": True, "new": True
            }
        else:
            res['response']['text'] = 'Кролика можно найти на Яндекс.Маркете!'
            res['response']['buttons'] = get_suggests(user_id)
            res['response']['end_session'] = True
        return

    # Если нет, то убеждаем его купить слона!
    if sessionStorage[user_id]["слон"]:
        res['response']['text'] = \
            f"Все говорят '{req['request']['original_utterance']}', а ты купи кролика!"
    else:
        res['response']['text'] = \
            f"Все говорят '{req['request']['original_utterance']}', а ты купи слона!"
    res['response']['buttons'] = get_suggests(user_id)


# Функция возвращает две подсказки для ответа.
def get_suggests(user_id):
    session = sessionStorage[user_id]

    # Выбираем две первые подсказки из массива.
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests'][:2]
    ]

    # Убираем первую подсказку, чтобы подсказки менялись каждый раз.
    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    # Если осталась только одна подсказка, предлагаем подсказку
    # со ссылкой на Яндекс.Маркет.
    if len(suggests) < 2:
        if sessionStorage[user_id]["слон"]:
            suggests.append({
                "title": "Ладно",
                "url": "https://market.yandex.ru/search?text=кролика",
                "hide": True
            })
        else:
            suggests.append({
                "title": "Ладно",
                "url": "https://market.yandex.ru/search?text=слон",
                "hide": True
            })

    return suggests


if __name__ == '__main__':
    if 'HEROKU' in os.environ:
        port = int(os.environ.get("PORT", 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        app.run(port=8000)
