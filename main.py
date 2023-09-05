
import telebot
import openai
import requests, json
from my_api import api_key, telebot_api
# Библиотеки: pyTelegramBotApi - (telebot) для работы с ботом телеграмм,
#             openai - для работы с Api ChatGPT
#             requests - для post и get запросов
#             json - для работы с json ответами
#             my_api - отдельный файл с токенами для api (скрыт для github)


# Записываем api ключ в переменную.
openai.api_key = api_key


class Messages:
    """
    Класс для добавления новых сообщений в сессию.(она нужна для того чтобы бот мог исходить из предыдущих вопросов и ответов, например можно задавать вопрос, ссылаясь на предыдущий)
    Имеет флаги, которые показывают на каком этапе находится пользователь
    Может очищать сессию, например если пользователь закончил разговор, нужно также для экономии памяти

    args:
        msg - list список со словарями внутри, в нём хранятся сообщений в текущей сессии
        image_flag - booling показывает, если пользователь на этапе генерирования изображений
        text_flag - booling показывает, если пользовательно на этапе общения с нейросетью.
    """
    def __init__(self):
        self.msg = [{"role": "system", "content": "Ты - ассистент-помощник"}]
        self.image_flag = False
        self.text_flag = False


    def add_msg_user(self, text:str) -> None:
        """
        Функция для добавления новых сообщений пользователя в сессию:
        :param text: Текст вопроса пользователя
        """
        self.msg.append({"role": "user", "content": text})


    def add_msg_bot(self, text:str) -> None:
        """
        Функция для добавления новых ответов нейросети в сессию:
        :param text: Ответ нейросети на вопрос пользователя
        """
        self.msg.append({"role": "assistant", "content": text})



    def restart(self) -> None:
        """
        Функция для обнуления всех параметров, при завершении сессии общения или генерации изображений
        """
        self.msg = [{"role": "system", "content": "Ты - ассистент-помощник"}]
        self.image_flag = False
        self.text_flag = False

# Создаём прототип класса, который будем использовать в дальнейшем
messages = Messages()


def find_info(msg:str) -> str:
    """
    Функция для поиска ответа на вопрос с помощью нейросети.
    :param msg: Вопрос пользователя
    :return: Ответ нейросети
    """
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=msg
    )
    generated_message = response["choices"][0]["message"]["content"]
    return generated_message
#

def generate_image(text:str) -> str:
    """
    Функция для генерации изображений по текстовому запросу пользователя
    :param text: Вопрос пользователя
    :return: Ссылку в строчном формате на сгенерированное изображение
    """
    response = openai.Image.create(
    prompt=text,
    n=1,
    size="1024x1024"
    )
    image_url = response['data'][0]['url']
    return image_url

def button_generate(texts:str):
    """
    Функция где собраны все коды для кнопок (чтобы не засорять основной код)
    :param texts: Название кнопки, которую нужно создать
    :return: Собранная кнопка
    """
    text = telebot.types.KeyboardButton("Задать вопросы")
    image = telebot.types.KeyboardButton("Сгенерировать изображение")
    help = telebot.types.KeyboardButton("Помощь")
    end = telebot.types.KeyboardButton("Завершить")
    buttons = {"text": text, "image":image, "help": help, "end": end}
    return buttons[texts]


def main():
    try:
        # Подключаем бота с помощью токена
        bot = telebot.TeleBot(telebot_api)

        # Перед каждой функцией стоит встроенный декоратор, которые отлавливает сообщение
        @bot.message_handler(commands=['start', 'help'])
        def start(new_message:dict) -> None:
            """
            Функция для команд Start и Help
            :param new_message: Отловленное сообщение
            """
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(button_generate("text"), button_generate("image"), button_generate("help"))
            messages.restart()
            bot.send_message(new_message.chat.id,f"Здравствуйте, <b>{new_message.from_user.first_name}</b>, я бот-помощник, можете задавать мне вопросы, и я буду подбирать для вас ответ с помощью нейросети.\n<b>Команды</b>:\n\t/text - задать вопрос боту (режим общения),\n\t/end - выйти из решима общения,\n\t/image - сгенерировать картинку по запросу,\n\t/help - узнать больше о боте.\n\t<b>Также для удобства созданы кнопки.</b>", parse_mode="html", reply_markup=markup)


        @bot.message_handler(commands=['text'])
        def ask(new_message:dict) -> None:
            """
            Функция для команды text
            :param new_message: Отловленное сообщение
            """
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(button_generate("end"), button_generate("image"), button_generate("help"))
            messages.restart()
            messages.text_flag = True
            bot.send_message(new_message.chat.id, "Можете задавать вопросы, но учтите, что нужно формулировать понятные вопросы, чтобы нейросеть могла понять, что вы от неё хотите. (Для завершения общения напишите /end)", parse_mode="html", reply_markup=markup)


        @bot.message_handler(commands=['image'])
        def img_ask(new_message: dict) -> None:
            """
            Функция для команды image
            :param new_message: Отловленное сообщение
            """
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(button_generate("text"), button_generate("image"), button_generate("help"))
            messages.restart()
            messages.image_flag = True
            bot.send_message(new_message.chat.id,
                         "Можете задавать название для генерации картинки. (Для завершения функции напишите /end или кнопку 'Завершить')",
                         parse_mode="html", reply_markup=markup)


        @bot.message_handler(commands=['end'])
        def end(new_message):
            """
            Функция для команды end
            :param new_message: Отловленное сообщение
            """
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(button_generate("text"), button_generate("image"), button_generate("help"))
            messages.restart()
            bot.send_message(new_message.chat.id, "Спасибо за общениe, можете написать /start для начала нового сеанса. Либо выбрать нужную функцию из данных кнопок.", parse_mode="html", reply_markup=markup)


        @bot.message_handler()
        def any_msg(new_message):
            """
            Функция для остальных отловленных сообщений
            :param new_message: Отловленное сообщение
            """
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup_image = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(button_generate("end"), button_generate("image"), button_generate("help"))
            markup_image.add(button_generate("end"), button_generate("text"), button_generate("help"))

            if new_message.text == "Задать вопросы":
                ask(new_message)

            elif new_message.text == "Сгенерировать изображение":
                img_ask(new_message)

            elif new_message.text == "Завершить":
                end(new_message)

            elif new_message.text == "Помощь":
                start(new_message)

            elif messages.text_flag:
                messages.add_msg_user(new_message.text)
                bot.send_message(new_message.chat.id, "Нейросеть генерирует ответ. Пожалуйста, подождите... (Время ожидания - менее 30 сек.)", parse_mode="html", reply_markup=markup)
                bot_answer = find_info(messages.msg)
                messages.add_msg_bot(bot_answer)
                bot.send_message(new_message.chat.id, bot_answer, parse_mode="html", reply_markup=markup)

            elif messages.image_flag:

                bot.send_message(new_message.chat.id, "Нейросеть генерирует изображение. Пожалуйста, подождите... (Время ожидания - менее 1 мин.)", parse_mode="html", reply_markup=markup)
                img_link = generate_image(new_message.text)
                bot.send_photo(new_message.chat.id, img_link, reply_markup=markup_image)
                bot.send_message(new_message.chat.id,"Можете задавать название для генерации картинки. (Для завершения функции напишите /end или нажмите кнопку 'Завершить')", parse_mode="html", reply_markup=markup_image)
            else:
                start(new_message)

        # Запускаем бота в режиме non_stop
        bot.polling(non_stop=True)

    except Exception: # Так делать нельзя! Отлавливать все ошибки, но ошибки выскакивают разные, в основном requests.exceptions... Но я не знаю какие именно.
        main()


main()
