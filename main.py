
import telebot
import requests, json

import openai
from my_api import api_key


openai.api_key = api_key



class Messages:
  def __init__(self):
    self.msg = [{"role": "system", "content": "Ты - ассистент-помощник"}]
    self.image_flag = False
    self.text_flag = False

  def add_msg_user(self, text):
    self.msg.append({"role": "user", "content": text})
    print(self.msg)

  def add_msg_bot(self, text):
    self.msg.append({"role": "assistant", "content": text})
    print(self.msg)


  def restart(self):
    self.msg = [{"role": "system", "content": "Ты - ассистент-помощник"}]
    self.image_flag = False
    self.text_flag = False

messages = Messages()


def find_info(msg):
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=msg
    )
    generated_message = response["choices"][0]["message"]["content"]
    return generated_message
#

def generate_image(text):
  response = openai.Image.create(
    prompt=text,
    n=1,
    size="1024x1024"
  )
  image_url = response['data'][0]['url']
  return image_url



def main():
  try:
      bot = telebot.TeleBot("6617010441:AAG9TjtXPgFuDEsCkucla2Uu5jNcNXJgArY")

      @bot.message_handler(commands=['start', 'help'])
      def start(new_message):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        text = telebot.types.KeyboardButton("Задать вопросы")
        image = telebot.types.KeyboardButton("Сгенерировать изображение")
        help = telebot.types.KeyboardButton("Помощь")
        markup.add(text, image, help)

        messages.restart()
        bot.send_message(new_message.chat.id,f"Здравствуйте, <b>{new_message.from_user.first_name}</b>, я бот-помощник, можете задавать мне вопросы, и я буду подбирать для вас ответ с помощью нейросети.\n<b>Команды</b>:\n\t/text - задать вопрос боту (режим общения),\n\t/end - выйти из решима общения,\n\t/image - сгенерировать картинку по запросу,\n\t/help - узнать больше о боте.\n\t<b>Также для удобства созданы кнопки.</b>", parse_mode="html", reply_markup=markup)


      @bot.message_handler(commands=['text'])
      def ask(new_message):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        end = telebot.types.KeyboardButton("Завершить")
        image = telebot.types.KeyboardButton("Сгенерировать изображение")
        help = telebot.types.KeyboardButton("Помощь")
        markup.add(end, image, help)
        messages.restart()
        messages.text_flag = True
        bot.send_message(new_message.chat.id, "Можете задавать вопросы, но учтите, что нужно формулировать понятные вопросы, чтобы нейросеть могла понять, что вы от неё хотите. (Для завершения общения напишите /end)", parse_mode="html", reply_markup=markup)

      @bot.message_handler(commands=['image'])
      def img_ask(new_message):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        end = telebot.types.KeyboardButton("Задать вопросы")
        image = telebot.types.KeyboardButton("Завершить")
        help = telebot.types.KeyboardButton("Помощь")
        markup.add(end, image, help)
        messages.restart()
        messages.image_flag = True
        bot.send_message(new_message.chat.id,
                         "Можете задавать название для генерации картинки. (Для завершения функции напишите /end или кнопку 'Завершить')",
                         parse_mode="html", reply_markup=markup)

      @bot.message_handler(commands=['end'])
      def end(new_message):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        text = telebot.types.KeyboardButton("Задать вопросы")
        image = telebot.types.KeyboardButton("Сгенерировать изображение")
        help = telebot.types.KeyboardButton("Помощь")
        markup.add(text, image, help)
        messages.restart()
        bot.send_message(new_message.chat.id, "Спасибо за общениe, можете написать /start для начала нового сеанса. Либо   выбрать нужную функцию из данных кнопок.", parse_mode="html", reply_markup=markup)


      try:
        @bot.message_handler()
        def any_msg(new_message):
          markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
          markup_image = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
          ending = telebot.types.KeyboardButton("Завершить")
          image = telebot.types.KeyboardButton("Сгенерировать изображение")
          help = telebot.types.KeyboardButton("Помощь")
          text = telebot.types.KeyboardButton("Задать вопросы")
          markup.add(ending, image, help)
          markup_image.add(ending, text, help)
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
            bot.send_message(new_message.chat.id,
                             "Можете задавать название для генерации картинки. (Для завершения функции напишите /end или нажмите кнопку 'Завершить')",
                             parse_mode="html", reply_markup=markup_image)
          else:
            start(new_message)
      except Exception:
        main()


      bot.polling(non_stop=True)

  except requests.exceptions.ReadTimeout:
    main()


main()
