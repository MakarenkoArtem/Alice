from flask import Flask, request
import logging
import json
import random
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# создаем словарь, в котором ключ — название города,
# а значение — массив, где перечислены id картинок,
# которые мы записали в прошлом пункте.

cities = {
    'москва': ['965417/7b04cb7d86def5c5050d',
               '965417/1eb9f4e1503259dabfc4'],
    'нью-йорк': ['213044/a32dc7c0f0cf783d6e58',
                 '1540737/61760720842520783ff6'],
    'париж': ["965417/050e31695385ed2ab2cc",
              '997614/3b46c606de4caeebdd48']
}

# создаем словарь, где для каждого пользователя
# мы будем хранить его имя
sessionStorage = {}


@app.route('/')
def info():
    return "Это мой 2 навык Алисы"


@app.route('/post', methods=['POST'])
def main():
    print("POST")
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    print("USER_ID", user_id)

    # если пользователь новый, то просим его представиться.
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        # создаем словарь в который в будущем положим имя пользователя
        sessionStorage[user_id] = {
            'first_name': None
        }
        return

    # если пользователь не новый, то попадаем сюда.
    # если поле имени пустое, то это говорит о том,
    # что пользователь еще не представился.
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id] = {'first_name': first_name, 'cities': None, 'city_now': None,
                                       "?": None}
            res['response'][
                'text'] = 'Приятно познакомиться, ' \
                          + first_name.title() \
                          + '. Отгадаешь город по фото?'
            # получаем варианты buttons из ключей нашего словаря cities
            res['response']['buttons'] = [
                {
                    'title': "да",
                    'hide': True
                },
                {
                    'title': "нет",
                    'hide': True
                }
            ]
            print('sessionStorage', sessionStorage)
    # если мы знакомы с пользователем и он нам что-то написал,
    # то это говорит о том, что он уже говорит о городе,
    # что хочет увидеть.
    elif sessionStorage[user_id]['?'] is None:
        print("*" * 50)
        if req['request']['original_utterance'].lower() == "нет":
            res['response']['text'] = "Пока"
            res['response']['end_session'] = True
            sessionStorage[user_id]['cities'] = None
        elif req['request']['original_utterance'].lower() == "да":
            if sessionStorage[user_id]['cities'] is None:
                sessionStorage[user_id]['cities'] = cities
            sessionStorage[user_id]['?'] = True
        else:
            res['response']['text'] = "Не поняла ответа! Так да или нет?"
    elif len(sessionStorage[user_id]['cities']):
        if sessionStorage[user_id]['city_now'] is not None:
            if sessionStorage[user_id]['city_now'] == req['request']['original_utterance'].lower():
                s = sessionStorage[user_id]['cities'].index(sessionStorage[user_id]['city_now'])
                sessionStorage[user_id]['cities'].pop(s)
                if len(sessionStorage[user_id]['cities']):
                    res['response']['text'] = 'Правильно. Сыграем ещё?'
                sessionStorage[user_id]['?'] = None
                sessionStorage[user_id]['city_now'] = None
            elif len(sessionStorage[user_id]['cities'][sessionStorage[user_id]['city_now']]):
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'А так?'
                res['response']['card']['image_id'] = sessionStorage[user_id]['cities'][
                    sessionStorage[user_id]['city_now']].pop(0)
                res['response']['text'] = ''
            else:
                res['response']['text'] = 'Вы пытались. Это' + sessionStorage[user_id][
                    'city_now'].capitalize() + "Сыграем ещё?"
                sessionStorage[user_id]['?'] = None
    if sessionStorage[user_id]['cities'] is not None and len(sessionStorage[user_id]['cities']) and len(sessionStorage[user_id]['cities'][sessionStorage[user_id]['city_now']]) and sessionStorage[user_id]['?'] == True:
        print(sessionStorage[user_id]['cities'])
        if sessionStorage[user_id]['city_now'] is None:
            city = random.choice(list(sessionStorage[user_id]['cities'].keys()))
            print("CITY", city)
            sessionStorage[user_id]['city_now'] = city
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = sessionStorage[user_id]['cities'][sessionStorage[user_id]['city_now']].pop(0)
        res['response']['text'] = ''
    elif sessionStorage[user_id]['cities'] is not None and not len(sessionStorage[user_id]['cities']):
        res['response']['text'] = 'Молодец, ты всё отгадал. Пока'
        res['response']['end_session'] = True


def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO то пытаемся получить город(city),
        # если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    if 'HEROKU' in os.environ:
        port = int(os.environ.get("PORT", 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        app.run(port=8000)
