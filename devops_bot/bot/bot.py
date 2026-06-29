import logging
import os
import datetime
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


BOT_TOKEN = os.getenv("BOT_TOKEN", "8795566881:AAHbjAAfJAodCHpb6AehKODuOKM5tKuHU8w")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Показать данные из test", callback_data='show_data')],
        [InlineKeyboardButton("Показать логи о репликации", callback_data='show_logs')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Привет! Я ботяра для этой практики.\n"
        "Выбери действие:",
        reply_markup=reply_markup
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'show_data':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'test')")
            if not cur.fetchone()[0]:
                await query.edit_message_text("Таблица 'test' не найдена")
                cur.close()
                conn.close()
                return

            cur.execute("SELECT id, name, value, created_at FROM test ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
            cur.close()
            conn.close()

            if not rows:
                await query.edit_message_text("Таблица test пуста")
                return

            msg = "Данные из test:\n\n"
            for row in rows:
                msg += f"ID: {row[0]}, Name: {row[1]}, Value: {row[2]}, Created: {row[3]}\n"
            
            await query.edit_message_text(msg)

        except Exception as e:
            logger.error(f"show_data error: {e}")
            await query.edit_message_text(f"Ошибка: {e}")

    elif query.data == 'show_logs':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT pg_is_in_recovery()")
            is_replica = cur.fetchone()[0]

            msg = "Репликация PostgreSQL\n\n"

            if is_replica:
                msg += "Режим: SLAVE (реплика)\n"
                msg += "Только чтение\n"
            else:
                msg += "Режим: MASTER (основная БД)\n"
                msg += "Чтение и запись\n\n"

                cur.execute("SELECT slot_name, active FROM pg_replication_slots")
                slots = cur.fetchall()
                
                if slots:
                    msg += "Слоты репликации:\n"
                    for slot in slots:
                        status = "активен" if slot[1] else "неактивен"
                        msg += f"  - {slot[0]}: {status}\n"
                else:
                    msg += "Слотов репликации нет\n"

                cur.execute("""
                    SELECT application_name, state, sync_state, 
                           pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) as lag
                    FROM pg_stat_replication
                """)
                replicas = cur.fetchall()
                
                if replicas:
                    msg += "\nПодключенные реплики:\n"
                    for rep in replicas:
                        name = rep[0] or "без имени"
                        msg += f"  - {name}: {rep[1]}, синхронизация: {rep[2]}"
                        if rep[3] and rep[3] > 0:
                            msg += f", отставание: {rep[3]} байт"
                        msg += "\n"
                else:
                    msg += "\nНет подключенных реплик"

            cur.execute("SELECT pg_current_wal_lsn()")
            msg += f"\nТекущий LSN: {cur.fetchone()[0]}"

            cur.close()
            conn.close()

            msg += f"\n\nОбновлено: {datetime.datetime.now().strftime('%H:%M:%S')}"
            await query.edit_message_text(msg)

        except Exception as e:
            logger.error(f"show_logs error: {e}")
            await query.edit_message_text(f"Ошибка: {e}")


def main():
    logger.info("Запуск бота")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    logger.info("Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
