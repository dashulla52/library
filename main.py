import telebot
import sqlite3
from datetime import datetime


API_TOKEN = "7553308695:AAFAk6K4e2V2dkSijx1Ihu_jyYFLrdbyHG0"
bot = telebot.TeleBot(API_TOKEN)


conn = sqlite3.connect('library.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS books
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER,
                   title TEXT,
                   author TEXT,
                   status TEXT,
                   added_at TEXT)''')
conn.commit()


@bot.message_handler(commands=['start'])
def add_book(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, "Введите название книги:")
    bot.register_next_step_handler(message, lambda msg: get_author(msg, user_id))

def get_author(message, user_id):
    title = message.text
    bot.send_message(message.chat.id, "Введите автора книги:")
    bot.register_next_step_handler(message, lambda msg: get_status(msg, title, user_id))

def get_status(message, title, user_id):
    author = message.text
    bot.send_message(message.chat.id, "Введите статус книги (прочитана/в процессе/в планах):")
    bot.register_next_step_handler(message, lambda msg: save_book(msg, title, author, user_id))

def save_book(message, title, author, user_id):
    status = message.text
    added_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO books (user_id, title, author, status, added_at) VALUES (?, ?, ?, ?, ?)",
                   (user_id, title, author, status, added_at))
    conn.commit()
    bot.send_message(message.chat.id, "Книга добавлена!")


@bot.message_handler(commands=['list'])
def list_books(message):
    user_id = message.from_user.id
    cursor.execute("SELECT title, author, status FROM books WHERE user_id=?", (user_id,))
    books = cursor.fetchall()
    if books:
        response = "\n".join([f"{title} - {author} ({status})" for title, author, status in books])
    else:
        response = "Книги не найдены."
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['search'])
def search_book(message):
    bot.send_message(message.chat.id, "Введите название или автора для поиска:")
    bot.register_next_step_handler(message, find_book)

def find_book(message):
    query = message.text
    cursor.execute("SELECT title, author, status FROM books WHERE title LIKE ? OR author LIKE ?", 
                   ('%' + query + '%', '%' + query + '%'))
    books = cursor.fetchall()
    if books:
        response = "\n".join([f"{title} - {author} ({status})" for title, author, status in books])
    else:
        response = "Книги не найдены."
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['edit'])
def edit_book(message):
    bot.send_message(message.chat.id, "Введите ID книги для редактирования:")
    bot.register_next_step_handler(message, get_new_info)

def get_new_info(message):
    book_id = message.text
    cursor.execute("SELECT title, author, status FROM books WHERE id=?", (book_id,))
    book = cursor.fetchone()
    if book:
        bot.send_message(message.chat.id, f"Текущая информация: {book}. Введите новое название (или оставьте пустым):")
        bot.register_next_step_handler(message, lambda msg: update_book_info(msg, book, book_id))
    else:
        bot.send_message(message.chat.id, "Книга не найдена.")

def update_book_info(message, book, book_id):
    new_title = message.text or book[0]
    bot.send_message(message.chat.id, "Введите нового автора (или оставьте пустым):")
    bot.register_next_step_handler(message, lambda msg: update_status(msg, new_title, book, book_id))

def update_status(message, new_title, book, book_id):
    new_author = message.text or book[1]
    bot.send_message(message.chat.id, "Введите новый статус (или оставьте пустым):")
    
    bot.register_next_step_handler(message, lambda msg: finalize_edit(msg, new_title, new_author, book, book_id))

def finalize_edit(message, new_title, new_author, book, book_id):
    new_status = message.text or book[2]
    cursor.execute("UPDATE books SET title=?, author=?, status=? WHERE id=?",
                   (new_title, new_author, new_status, book_id))
    conn.commit()
    bot.send_message(message.chat.id, "Книга обновлена!")


bot.polling(none_stop=True)
