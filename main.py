import telebot
from telebot.types import InlineKeyboardMarkup,  ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from secret import API_BOT
from connection import *
from random import random, choice, shuffle

bot = telebot.TeleBot(API_BOT,parse_mode=None)

main_comand = None

games = {}

game_start = None

bals = {}

@bot.message_handler(commands=["start"])
def start(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton("Add_question")
    btn2 = KeyboardButton("Update_question")
    btn3 = KeyboardButton("Show_all")
    btn4 = KeyboardButton("Show_by_id")
    btn5 = KeyboardButton("Delete")
    btn6 = KeyboardButton("/new_question")
    if message.chat.id == 5976137781:
        markup.add(btn1,btn2,btn3)
        markup.add(btn4,btn5,btn6)
        bot.send_message(message.chat.id, "Добро пожаловать в мой бот Poly Chudes",reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Добро пожаловать в мой бот Poly Chudes")
    is_user_exist = get_user(message.chat.id)
    if not is_user_exist:
        if message.chat.username is not None:
            add_user(message)
        else:
            bot.send_message(message.chat.id, "У вас нету username пожайлусто вводите его: ")
            bot.register_next_step_handler(message, new_username)

@bot.message_handler(commands=["new_question"])
def new_question(message):
    global game_start
    conn = open_conection()
    cur = conn.cursor()
    cur.execute("""SELECT * FROM question""")
    list_question = cur.fetchall()

    if not list_question:
        bot.send_message(message.chat.id, "Нет доступных вопросов. Пожалуйста, добавьте их в базу данных.")
        close_conection(conn, cur)
        return
    
    random_question = choice(list_question)
    answer = random_question[2]
    current_state = '*' * len(answer) 
    guessed_letters = [] 

    games[message.chat.id] = {
        "question": random_question[1],
        "answer": answer,
        "current_state": current_state,
        "guessed_letters": guessed_letters
    }
    game_start = True
    bot.send_message(message.chat.id, f"{random_question[1]}\nОтвет: {current_state}")
    close_conection(conn, cur)

@bot.message_handler()
def handle_message(message):
    game = games.get(message.chat.id)
    if message.chat.id == 5976137781:
        if message.text == "Add_question":
            ask_question(message)
            return None
        elif message.text == "Update_question":
            id_for_update(message)
            return None
        elif message.text == "Show_all":
            show_all(message)
            return None
        elif message.text == "Show_by_id":
            id_for_show(message)
            return None
        elif message.text == "Delete":
            id_for_delete_question(message)
            return None
    if message.text == "/ansswer":
        answeer(message)
    elif message.text == "/score":
        show_score(message)
    elif message.text == "/exit_game":
        exit_game(message)
    elif message.text == "/show_top":
        show_top(message)
    elif game:
        guess_letter(message)
    else:
        bot.send_message(message.chat.id, "Сначала начните новую игру командой /new_question.")

@bot.message_handler(commands=["ansswer"])
def answeer(message):
    game = games.get(message.chat.id)
    if game:
        answer = game["answer"]
        bot.send_message(message.chat.id, "Введите полный ответ:")
        bot.register_next_step_handler(message, lambda msg: correct_answer(msg, answer))
    else:
        bot.send_message(message.chat.id, "Игра не найдена.")


def correct_answer(message, answer):
    global bals
    bals[message.chat.id]={
        'bals': 0
    }
    if answer.lower() == message.text.lower(): 
        bot.send_message(message.chat.id, f"Поздравляем! Вы угадали ответ: {answer}")
        bals[message.chat.id]["bals"] += 10
        update_bals(message.chat.id, bals[message.chat.id])
        del games[message.chat.id] 
        bals[message.chat.id]["bals"] = 0
    else:
        bot.send_message(message.chat.id, "Неправильный ответ. Попробуйте еще раз.")


@bot.message_handler(commands=["exit_game"])
def exit_game(message):
    if games:
        del games[message.chat.id] 
        bot.send_message(message.chat.id, "Вы вышли из игры!!")
    else:
        bot.send_message(message.chat.id, "Вы не в ходили в вигру для началов ввойдите в него через команду /new_question.")


def guess_letter(message):
    global bals
    bals[message.chat.id]={
        'bals': 0
    }
    game = games.get(message.chat.id)

    if not game:
        bot.send_message(message.chat.id, "Сначала начните новую игру командой /new_question.")
        return

    letter = message.text.lower()
    answer = game["answer"]
    current_state = game["current_state"]
    guessed_letters = game["guessed_letters"]

    if letter in guessed_letters:
        bot.send_message(message.chat.id, "Эта буква уже была угадана. Попробуйте другую.")
        return

    guessed_letters.append(letter)

    if letter in answer.lower():
        current_state = ''.join([letter if answer[i].lower() == letter else current_state[i] for i in range(len(answer))])
        bot.send_message(message.chat.id, f"Верно! Ответ: {current_state}")
        bals[message.chat.id]["bals"] += 2
    elif message.text == "/ansswer":
        bot.register_next_step_handler(message, answeer)
    else:
        bot.send_message(message.chat.id, "Неверно! Попробуйте снова.")
        if bals[message.chat.id]["bals"]  > 0:
            bals[message.chat.id]["bals"]  -= 1

    game["current_state"] = current_state

    if '*' not in current_state:
        bot.send_message(message.chat.id, f"Поздравляем! Вы угадали ответ: {answer}")
        del games[message.chat.id] 
        update_bals(message.chat.id, bals[message.chat.id])
        gamee_start = None

@bot.message_handler(commands=["show_top"])
def show_top(message):
    conn = open_conection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM users
        order by score desc
        limit 5
    """, (message.chat.id,))
    userses = cur.fetchall()
    if userses is None:
        bot.send_message(message.chat.id, "Вы не зарегистрированы в системе.")
    else:
        print(userses)
        n = ""
        for top in userses:
            n += f"Username: {top[2]}; Score: {top[5]}\n"
        bot.send_message(message.chat.id, n)
    close_conection(conn, cur)


@bot.message_handler(commands=["score"])
def show_score(message):
    conn = open_conection()
    cur = conn.cursor()
    cur.execute("""
        SELECT score FROM users
        WHERE telgram_id = '%s'
    """, (message.chat.id,))
    question = cur.fetchone()
    if question is None:
        bot.send_message(message.chat.id, "Вы не зарегистрированы в системе.")
    else:
        bot.send_message(message.chat.id, f"""Ваш счет: {question[0]}""")
    close_conection(conn, cur)

@bot.message_handler()
def ask_question(message):
    bot.send_message(message.chat.id, "Введите ваш вопрос:")
    bot.register_next_step_handler(message, process_question)

def process_question(message):
    question_text = message.text
    bot.send_message(message.chat.id, "Введите ответ на вопрос:")
    bot.register_next_step_handler(message, lambda msg: save_question(msg, question_text))

def save_question(message, question_text):
    answer_text = message.text
    conn = open_conection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO question (question_text, correct_answer)
        VALUES (%s, %s)
    """, (question_text, answer_text,))
    conn.commit()
    close_conection(conn, cur)
    bot.send_message(message.chat.id, "Вопрос успешно добавлен!")

def update_bals(user_id, bals):
    conn= open_conection()
    cur = conn.cursor()
    cur.execute(f"""
        update users 
        set score = score + {bals["bals"]}
        where telgram_id = '{user_id}'
    """)
    conn.commit()
    close_conection(conn, cur)

def show_all(message):
    conn = open_conection()
    cur = conn.cursor()
    cur.execute("""
        select * from question
    """)
    all_dates = cur.fetchall()
    for question in all_dates:
        bot.send_message(message.chat.id, f"""id: {question[0]}\nquestion: {question[1]}\nanswer: {question[2]}\ndate: {question[3]}""")
    close_conection(conn, cur)

def id_for_show(message):
    bot.send_message(message.chat.id, "Введите id для просмотра вопроса:")
    bot.register_next_step_handler(message, show_by_id)

def show_by_id(message):
    id = message.text
    conn = open_conection()
    cur = conn.cursor()
    cur.execute(f"""
        select * from question
        where id = {id}
    """)
    question = cur.fetchone()
    bot.send_message(message.chat.id, f"""id: {question[0]}\nquestion: {question[1]}\nanswer: {question[2]}\ndate: {question[3]}""")
    close_conection(conn, cur)

def id_for_update(message):
    bot.send_message(message.chat.id, "Введите id вопроса для изменения:")
    bot.register_next_step_handler(message, start_update_question)

def start_update_question(message):
    upid = message.text
    bot.send_message(message.chat.id, "Введите новый текст вопроса:")
    bot.register_next_step_handler(message, lambda msg: update_question(msg, upid))

def update_question(message, upid):
    question_text = message.text
    bot.send_message(message.chat.id, "Введите новый ответ на вопрос:")
    bot.register_next_step_handler(message, lambda msg: update_answer_question(msg, upid, question_text))

def update_answer_question(message, upid, question_text):
    answer_text = message.text
    conn = open_conection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE question 
        SET question_text = %s, correct_answer = %s
        WHERE id = %s
    """, (question_text, answer_text, upid,))
    conn.commit()
    close_conection(conn, cur)
    bot.send_message(message.chat.id, "Вопрос успешно изменен!")

def id_for_delete_question(message):
    bot.send_message(message.chat.id, "Введите id вопроса для удаления: ")
    bot.register_next_step_handler(message, delete_by_id_question)
def delete_by_id_question(message):
    try:
        id = message.text
        conn= open_conection()
        cur = conn.cursor()
        cur.execute(f"""
            delete from question
            where id = {id}
        """)
        conn.commit()
        close_conection(conn,cur)
        bot.send_message(message.chat.id, "Вопрос успешно удален!")
    except:
        bot.send_message(message.chat.id, "Вопрос с таким id не существует!")

def new_username(message):
    username = message.text
    add_user2(message, username) 
    bot.send_message(message.chat.id, "Спасибо теперь вы можете использовать бот )") 


bot.infinity_polling()