#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot для защиты группы от ботов и ИИ
Автономный бот без зависимостей от внешних сервисов
"""

import asyncio
import logging
import random
import time
import json
import hashlib
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
from aiohttp import web

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Импорт новых функций
from features import (
    AntiSpam, ReputationSystem, GroupStats, WelcomeRules,
    feedback_command, reputation_command, top_command,
    rules_command, setrules_command, support_command,
    SUPPORT_BOT
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "7681253398:AAGAr7kug1Vd0o1yNsk6yJj6B8R3Xfnf8Hk"

# Константы
MAX_ATTEMPTS = 5
VERIFICATION_TIMEOUT = 300  # 5 минут
CLEANUP_INTERVAL = 600  # 10 минут


@dataclass
class UserVerification:
    """Данные верификации пользователя"""
    user_id: int
    chat_id: int
    username: Optional[str]
    attempts: int
    challenge_type: str
    correct_answer: str
    start_time: float
    message_id: Optional[int] = None


class ChallengeGenerator:
    """Генератор различных типов проверок"""
    
    def __init__(self):
        self.emojis = {
            'animals': ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵'],
            'food': ['🍎', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍒', '🍑', '🥝', '🍅', '🥑', '🍆', '🥔', '🥕'],
            'nature': ['🌸', '🌺', '🌻', '🌷', '🌹', '🌲', '🌳', '🌴', '🌵', '🌾', '🍀', '🍁', '🍂', '🍃', '🌿'],
            'objects': ['⚽', '🏀', '🏈', '⚾', '🎾', '🏐', '🏉', '🎱', '🏓', '🏸', '🏒', '🏑', '🥊', '🥋', '⛳'],
            'symbols': ['❤️', '💙', '💚', '💛', '🧡', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗'],
            'faces': ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '😉', '😊', '😇', '🥰', '😍'],
            'weather': ['☀️', '🌤️', '⛅', '🌥️', '☁️', '🌦️', '🌧️', '⛈️', '🌩️', '🌨️', '❄️', '☃️', '⛄', '🌬️', '💨'],
            'transport': ['🚗', '🚕', '🚙', '🚌', '🚎', '🏎️', '🚓', '🚑', '🚒', '🚐', '🚚', '🚛', '🚜', '🛵', '🏍️']
        }
        
        self.numbers = list(range(0, 100))
        self.colors_ru = ['красный', 'синий', 'зелёный', 'жёлтый', 'оранжевый', 'фиолетовый', 'розовый', 'чёрный', 'белый', 'серый']
        self.animals_ru = ['собака', 'кошка', 'мышь', 'лиса', 'медведь', 'панда', 'тигр', 'лев', 'корова', 'свинья']
        
    def generate_emoji_challenge(self) -> tuple:
        """Тип 1: Найди эмодзи"""
        category = random.choice(list(self.emojis.keys()))
        emojis = random.sample(self.emojis[category], 5)
        correct = random.choice(emojis)
        
        question = f"🤖 Нажми на эмодзи: {correct}"
        return question, correct, emojis
    
    def generate_math_challenge(self) -> tuple:
        """Тип 2: Математическая задача"""
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        operation = random.choice(['+', '-', '*'])
        
        if operation == '+':
            answer = a + b
        elif operation == '-':
            answer = a - b
        else:
            answer = a * b
        
        question = f"🧮 Реши: {a} {operation} {b} = ?"
        options = [answer]
        while len(options) < 5:
            wrong = answer + random.randint(-10, 10)
            if wrong not in options and wrong >= 0:
                options.append(wrong)
        random.shuffle(options)
        
        return question, str(answer), [str(x) for x in options]

    def generate_sequence_challenge(self) -> tuple:
        """Тип 3: Продолжи последовательность"""
        start = random.randint(1, 10)
        step = random.randint(2, 5)
        sequence = [start + i * step for i in range(4)]
        answer = start + 4 * step
        
        question = f"🔢 Продолжи: {', '.join(map(str, sequence))}, ?"
        options = [answer]
        while len(options) < 5:
            wrong = answer + random.randint(-10, 10)
            if wrong not in options and wrong > 0:
                options.append(wrong)
        random.shuffle(options)
        
        return question, str(answer), [str(x) for x in options]
    
    def generate_color_challenge(self) -> tuple:
        """Тип 4: Выбери цвет"""
        color = random.choice(self.colors_ru)
        question = f"🎨 Выбери цвет: {color}"
        
        options = [color]
        while len(options) < 5:
            wrong = random.choice(self.colors_ru)
            if wrong not in options:
                options.append(wrong)
        random.shuffle(options)
        
        return question, color, options
    
    def generate_pattern_challenge(self) -> tuple:
        """Тип 5: Найди паттерн"""
        emoji_set = random.choice(list(self.emojis.values()))
        pattern_emoji = random.choice(emoji_set[:5])
        pattern = [pattern_emoji, pattern_emoji, pattern_emoji]
        
        question = f"🔍 Найди повторяющийся: {' '.join(pattern)}"
        options = random.sample(emoji_set, 5)
        if pattern_emoji not in options:
            options[0] = pattern_emoji
        random.shuffle(options)
        
        return question, pattern_emoji, options
    
    def generate_logic_challenge(self) -> tuple:
        """Тип 6: Логическая задача"""
        challenges = [
            ("Сколько дней в неделе?", "7", ["5", "6", "7", "8", "9"]),
            ("Сколько месяцев в году?", "12", ["10", "11", "12", "13", "14"]),
            ("Сколько часов в сутках?", "24", ["20", "22", "24", "26", "28"]),
            ("Сколько минут в часе?", "60", ["50", "55", "60", "65", "70"]),
            ("Сколько секунд в минуте?", "60", ["50", "55", "60", "65", "70"]),
        ]
        
        challenge = random.choice(challenges)
        question = f"🧠 {challenge[0]}"
        return question, challenge[1], challenge[2]
    
    def generate_comparison_challenge(self) -> tuple:
        """Тип 7: Сравнение чисел"""
        a = random.randint(10, 99)
        b = random.randint(10, 99)
        
        if a > b:
            answer = ">"
            question = f"🔢 Что больше: {a} или {b}?"
        elif a < b:
            answer = "<"
            question = f"🔢 Что меньше: {a} или {b}?"
        else:
            a += 1
            answer = ">"
            question = f"🔢 Что больше: {a} или {b}?"
        
        options = [">", "<", "=", "не знаю", "оба равны"]
        random.shuffle(options)
        
        return question, answer, options
    
    def generate_word_challenge(self) -> tuple:
        """Тип 8: Найди животное"""
        animal = random.choice(self.animals_ru)
        question = f"🐾 Выбери животное: {animal}"
        
        options = [animal]
        while len(options) < 5:
            wrong = random.choice(self.animals_ru)
            if wrong not in options:
                options.append(wrong)
        random.shuffle(options)
        
        return question, animal, options
    
    def generate_count_challenge(self) -> tuple:
        """Тип 9: Посчитай эмодзи"""
        emoji = random.choice(self.emojis['animals'])
        count = random.randint(3, 7)
        emojis_str = emoji * count
        
        question = f"🔢 Сколько {emoji}? {emojis_str}"
        options = [str(count)]
        for i in range(1, 5):
            wrong = count + random.choice([-2, -1, 1, 2])
            if str(wrong) not in options and wrong > 0:
                options.append(str(wrong))
        random.shuffle(options)
        
        return question, str(count), options
    
    def generate_odd_one_out_challenge(self) -> tuple:
        """Тип 10: Найди лишнее"""
        category1 = random.choice(['animals', 'food', 'nature'])
        category2 = random.choice([c for c in ['animals', 'food', 'nature'] if c != category1])
        
        main_emojis = random.sample(self.emojis[category1], 4)
        odd_emoji = random.choice(self.emojis[category2])
        
        all_emojis = main_emojis + [odd_emoji]
        random.shuffle(all_emojis)
        
        question = f"🎯 Найди лишнее: {' '.join(all_emojis)}"
        return question, odd_emoji, all_emojis
    
    def generate_challenge(self) -> tuple:
        """Генерация случайной проверки"""
        challenge_types = [
            self.generate_emoji_challenge,
            self.generate_math_challenge,
            self.generate_sequence_challenge,
            self.generate_color_challenge,
            self.generate_pattern_challenge,
            self.generate_logic_challenge,
            self.generate_comparison_challenge,
            self.generate_word_challenge,
            self.generate_count_challenge,
            self.generate_odd_one_out_challenge
        ]
        
        challenge_func = random.choice(challenge_types)
        question, answer, options = challenge_func()
        challenge_type = challenge_func.__name__
        
        return question, answer, options, challenge_type


class AntiBot:
    """Основной класс бота"""
    
    def __init__(self):
        self.verifications: Dict[int, UserVerification] = {}
        self.verified_users: Set[int] = set()
        self.banned_users: Set[int] = set()
        self.challenge_generator = ChallengeGenerator()
        self.stats = defaultdict(int)
        self.group_settings: Dict[int, dict] = {}
        
        # Новые системы
        self.anti_spam = AntiSpam()
        self.reputation_system = ReputationSystem()
        self.group_stats = GroupStats()
        self.welcome_rules = WelcomeRules()
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        self.stats['start_commands'] += 1
        
        welcome_text = """
👋 Добро пожаловать!

🤖 Я бот для защиты группы от ботов и ИИ.

📋 Основные команды:
/help - Помощь
/stats - Статистика
/settings - Настройки группы (только админы)
/verify - Пройти проверку вручную
/status - Статус верификации

🛡️ Функции:
✅ Автоматическая проверка новых участников
✅ 10 типов проверок с генерацией
✅ 5 попыток на прохождение
✅ Уведомления в личку
✅ Защита от спама
✅ Статистика и аналитика
✅ Гибкие настройки

Добавь меня в группу и дай права администратора!
"""
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        self.stats['help_commands'] += 1
        
        help_text = f"""
📚 Помощь по боту

🔧 Команды для всех:
/start - Начать работу с ботом
/help - Показать эту справку
/verify - Пройти проверку вручную
/status - Проверить статус верификации
/stats - Статистика бота
/reputation - Твоя репутация
/top - Топ активных пользователей
/rules - Правила группы
/feedback - Отправить отзыв
/support - Связь с поддержкой

👑 Команды для администраторов:
/settings - Настройки группы
/ban - Забанить (reply или ID)
/unban - Разбанить (reply или ID)
/kick - Кикнуть (reply или ID)
/mute - Замутить пользователя
/unmute - Размутить пользователя
/warn - Предупредить пользователя
/whitelist - Добавить в белый список
/blacklist - Добавить в чёрный список
/setrules - Установить правила группы

📊 Типы проверок:
1️⃣ Эмодзи - найди правильный эмодзи
2️⃣ Математика - реши пример
3️⃣ Последовательность - продолжи ряд
4️⃣ Цвета - выбери цвет
5️⃣ Паттерн - найди повторяющийся
6️⃣ Логика - ответь на вопрос
7️⃣ Сравнение - сравни числа
8️⃣ Слова - найди животное
9️⃣ Счёт - посчитай эмодзи
🔟 Лишнее - найди лишний элемент

🛡️ Защита:
• Анти-спам и анти-флуд
• Автоудаление ссылок и рекламы
• Система репутации
• Автобан за 3 предупреждения

💬 Поддержка: {SUPPORT_BOT}
"""
        await update.message.reply_text(help_text)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats"""
        self.stats['stats_commands'] += 1
        
        total_verifications = self.stats['verifications_started']
        successful = self.stats['verifications_passed']
        failed = self.stats['verifications_failed']
        success_rate = (successful / total_verifications * 100) if total_verifications > 0 else 0
        
        stats_text = f"""
📊 Статистика бота

👥 Пользователи:
• Верифицировано: {len(self.verified_users)}
• Забанено: {len(self.banned_users)}
• На проверке: {len(self.verifications)}

✅ Проверки:
• Всего начато: {total_verifications}
• Успешно: {successful}
• Провалено: {failed}
• Процент успеха: {success_rate:.1f}%

📈 Команды:
• /start: {self.stats['start_commands']}
• /help: {self.stats['help_commands']}
• /stats: {self.stats['stats_commands']}

🔧 Действия:
• Новых участников: {self.stats['new_members']}
• Кикнуто: {self.stats['kicks']}
• Забанено: {self.stats['bans']}
• Предупреждений: {self.stats['warnings']}

⏱️ Время работы: {self._get_uptime()}
"""
        await update.message.reply_text(stats_text)
    
    def _get_uptime(self) -> str:
        """Получить время работы бота"""
        if not hasattr(self, 'start_time'):
            self.start_time = time.time()
        
        uptime_seconds = int(time.time() - self.start_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        
        return f"{hours}ч {minutes}м"
    
    async def new_member_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик новых участников"""
        self.stats['new_members'] += 1
        
        message = update.message
        chat_id = message.chat_id
        
        for member in message.new_chat_members:
            user_id = member.id
            username = member.username or member.first_name
            
            # Пропускаем ботов (кроме проверки)
            if member.is_bot and user_id != context.bot.id:
                continue
            
            # Проверяем, не забанен ли пользователь
            if user_id in self.banned_users:
                try:
                    await context.bot.ban_chat_member(chat_id, user_id)
                    self.stats['bans'] += 1
                    await message.reply_text(f"❌ {username} в чёрном списке!")
                except Exception as e:
                    logger.error(f"Ошибка бана: {e}")
                continue
            
            # Проверяем, не верифицирован ли уже
            if user_id in self.verified_users:
                await message.reply_text(f"✅ {username} уже верифицирован!")
                continue
            
            # Ограничиваем права до прохождения проверки
            try:
                await context.bot.restrict_chat_member(
                    chat_id,
                    user_id,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                        can_send_polls=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False
                    )
                )
                logger.info(f"Права ограничены для пользователя {user_id}")
            except Exception as e:
                logger.error(f"Ошибка ограничения прав: {e}")
                # Пытаемся альтернативный способ
                try:
                    await context.bot.restrict_chat_member(
                        chat_id,
                        user_id,
                        permissions=ChatPermissions()
                    )
                    logger.info(f"Права ограничены альтернативным способом для {user_id}")
                except Exception as e2:
                    logger.error(f"Альтернативный способ тоже не сработал: {e2}")
            
            # Запускаем проверку
            await self._start_verification(update, context, user_id, username, chat_id)
    
    async def _start_verification(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 user_id: int, username: str, chat_id: int):
        """Запуск проверки пользователя"""
        self.stats['verifications_started'] += 1
        
        # Генерируем проверку
        question, answer, options, challenge_type = self.challenge_generator.generate_challenge()
        
        # Создаём клавиатуру
        keyboard = []
        for i in range(0, len(options), 2):
            row = []
            for j in range(i, min(i + 2, len(options))):
                callback_data = f"verify_{user_id}_{options[j]}"
                row.append(InlineKeyboardButton(options[j], callback_data=callback_data))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем сообщение с проверкой
        welcome_msg = f"""
👋 Добро пожаловать!

🔒 ВАЖНО: Ты не можешь писать в группе до прохождения проверки!

Для начала пройди быструю проверку:

{question}

⏱️ У тебя 5 минут
🔄 Попыток: 5

После успешной проверки ты сможешь свободно писать в чате! ✅
"""
        
        try:
            sent_message = await update.message.reply_text(
                welcome_msg,
                reply_markup=reply_markup
            )
            
            # Сохраняем данные верификации
            verification = UserVerification(
                user_id=user_id,
                chat_id=chat_id,
                username=username,
                attempts=0,
                challenge_type=challenge_type,
                correct_answer=answer,
                start_time=time.time(),
                message_id=sent_message.message_id
            )
            
            self.verifications[user_id] = verification
            
            # Устанавливаем таймер на удаление
            context.job_queue.run_once(
                self._verification_timeout,
                VERIFICATION_TIMEOUT,
                data={'user_id': user_id, 'chat_id': chat_id},
                name=f"timeout_{user_id}"
            )
            
        except Exception as e:
            logger.error(f"Ошибка отправки проверки: {e}")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        # Парсим callback_data
        parts = query.data.split('_')
        if len(parts) < 3 or parts[0] != 'verify':
            return
        
        user_id = int(parts[1])
        user_answer = '_'.join(parts[2:])
        
        # Проверяем, что нажал правильный пользователь
        if query.from_user.id != user_id:
            await query.answer("❌ Это не твоя проверка!", show_alert=True)
            return
        
        # Получаем данные верификации
        verification = self.verifications.get(user_id)
        if not verification:
            await query.answer("⚠️ Проверка не найдена", show_alert=True)
            return
        
        # Проверяем ответ
        verification.attempts += 1
        
        if user_answer == verification.correct_answer:
            # Правильный ответ
            await self._verification_success(query, context, verification)
        else:
            # Неправильный ответ
            await self._verification_failed(query, context, verification)
    
    async def _verification_success(self, query, context: ContextTypes.DEFAULT_TYPE, 
                                   verification: UserVerification):
        """Успешная верификация"""
        self.stats['verifications_passed'] += 1
        
        user_id = verification.user_id
        chat_id = verification.chat_id
        username = verification.username
        
        # Добавляем в верифицированные
        self.verified_users.add(user_id)
        
        # Удаляем из проверяемых
        if user_id in self.verifications:
            del self.verifications[user_id]
        
        # Снимаем ограничения - ПОЛНОСТЬЮ восстанавливаем права
        try:
            # Способ 1: Промоутим пользователя (снимаем все ограничения)
            await context.bot.promote_chat_member(
                chat_id,
                user_id,
                can_change_info=False,
                can_post_messages=False,
                can_edit_messages=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False
            )
            logger.info(f"Права восстановлены через promote для {user_id}")
        except Exception as e:
            logger.warning(f"Promote не сработал: {e}, пробуем restrict")
            # Способ 2: Используем restrict с полными правами
            try:
                await context.bot.restrict_chat_member(
                    chat_id,
                    user_id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                        can_change_info=False,
                        can_invite_users=True,
                        can_pin_messages=False
                    )
                )
                logger.info(f"Права восстановлены через restrict для {user_id}")
            except Exception as e2:
                logger.error(f"Ошибка снятия ограничений: {e2}")
                # Способ 3: Пытаемся разбанить (это снимает все ограничения)
                try:
                    await context.bot.unban_chat_member(chat_id, user_id, only_if_banned=False)
                    logger.info(f"Права восстановлены через unban для {user_id}")
                except Exception as e3:
                    logger.error(f"Все способы не сработали: {e3}")
        
        # Обновляем сообщение
        success_text = f"""
✅ Проверка пройдена!

👤 {username}
🎉 Теперь можешь писать в чате!
⏱️ Попыток использовано: {verification.attempts}/{MAX_ATTEMPTS}
"""
        
        try:
            await query.edit_message_text(success_text)
        except Exception as e:
            logger.error(f"Ошибка обновления сообщения: {e}")
        
        # Отправляем в личку
        try:
            await context.bot.send_message(
                user_id,
                f"✅ Поздравляем! Ты прошёл проверку в группе.\n\n"
                f"Теперь можешь свободно общаться!"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки в личку: {e}")
        
        # Отменяем таймер
        current_jobs = context.job_queue.get_jobs_by_name(f"timeout_{user_id}")
        for job in current_jobs:
            job.schedule_removal()
    
    async def _verification_failed(self, query, context: ContextTypes.DEFAULT_TYPE, 
                                  verification: UserVerification):
        """Неудачная попытка верификации"""
        user_id = verification.user_id
        chat_id = verification.chat_id
        username = verification.username
        attempts_left = MAX_ATTEMPTS - verification.attempts
        
        if attempts_left > 0:
            # Ещё есть попытки
            await query.answer(f"❌ Неправильно! Осталось попыток: {attempts_left}", show_alert=True)
            
            # Генерируем новую проверку
            question, answer, options, challenge_type = self.challenge_generator.generate_challenge()
            
            verification.correct_answer = answer
            verification.challenge_type = challenge_type
            
            # Создаём новую клавиатуру
            keyboard = []
            for i in range(0, len(options), 2):
                row = []
                for j in range(i, min(i + 2, len(options))):
                    callback_data = f"verify_{user_id}_{options[j]}"
                    row.append(InlineKeyboardButton(options[j], callback_data=callback_data))
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Обновляем сообщение
            new_text = f"""
❌ Неправильно! Попробуй ещё раз.

{question}

⏱️ Время истекает
🔄 Попыток осталось: {attempts_left}
"""
            
            try:
                await query.edit_message_text(new_text, reply_markup=reply_markup)
            except Exception as e:
                logger.error(f"Ошибка обновления сообщения: {e}")
        
        else:
            # Попытки закончились
            await self._verification_final_fail(query, context, verification)
    
    async def _verification_final_fail(self, query, context: ContextTypes.DEFAULT_TYPE, 
                                      verification: UserVerification):
        """Окончательный провал верификации"""
        self.stats['verifications_failed'] += 1
        self.stats['kicks'] += 1
        
        user_id = verification.user_id
        chat_id = verification.chat_id
        username = verification.username
        
        # Удаляем из проверяемых
        if user_id in self.verifications:
            del self.verifications[user_id]
        
        # Обновляем сообщение
        fail_text = f"""
❌ Проверка не пройдена!

👤 {username}
🚫 Попытки исчерпаны ({MAX_ATTEMPTS}/{MAX_ATTEMPTS})
⏱️ Результат отправлен в личку
"""
        
        try:
            await query.edit_message_text(fail_text)
        except Exception as e:
            logger.error(f"Ошибка обновления сообщения: {e}")
        
        # Отправляем в личку
        try:
            await context.bot.send_message(
                user_id,
                f"❌ К сожалению, ты не прошёл проверку.\n\n"
                f"Попытки исчерпаны: {MAX_ATTEMPTS}/{MAX_ATTEMPTS}\n"
                f"Ты был удалён из группы.\n\n"
                f"Если считаешь это ошибкой, обратись к администраторам."
            )
        except Exception as e:
            logger.error(f"Ошибка отправки в личку: {e}")
        
        # Кикаем пользователя
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.unban_chat_member(chat_id, user_id)
        except Exception as e:
            logger.error(f"Ошибка кика: {e}")
        
        # Отменяем таймер
        current_jobs = context.job_queue.get_jobs_by_name(f"timeout_{user_id}")
        for job in current_jobs:
            job.schedule_removal()

    async def _verification_timeout(self, context: ContextTypes.DEFAULT_TYPE):
        """Таймаут верификации"""
        job_data = context.job.data
        user_id = job_data['user_id']
        chat_id = job_data['chat_id']
        
        verification = self.verifications.get(user_id)
        if not verification:
            return
        
        username = verification.username
        
        # Удаляем из проверяемых
        if user_id in self.verifications:
            del self.verifications[user_id]
        
        self.stats['verifications_failed'] += 1
        self.stats['kicks'] += 1
        
        # Отправляем сообщение о таймауте
        timeout_text = f"""
⏱️ Время вышло!

👤 {username}
❌ Не успел пройти проверку
🚫 Удалён из группы
"""
        
        try:
            await context.bot.send_message(chat_id, timeout_text)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения о таймауте: {e}")
        
        # Отправляем в личку
        try:
            await context.bot.send_message(
                user_id,
                f"⏱️ Время на прохождение проверки истекло.\n\n"
                f"Ты был удалён из группы.\n\n"
                f"Если хочешь вернуться, попробуй снова."
            )
        except Exception as e:
            logger.error(f"Ошибка отправки в личку: {e}")
        
        # Кикаем пользователя
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.unban_chat_member(chat_id, user_id)
        except Exception as e:
            logger.error(f"Ошибка кика: {e}")
    
    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /verify - ручная верификация"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        username = update.effective_user.username or update.effective_user.first_name
        
        # Проверяем, не верифицирован ли уже
        if user_id in self.verified_users:
            await update.message.reply_text("✅ Ты уже верифицирован!")
            return
        
        # Проверяем, не на проверке ли уже
        if user_id in self.verifications:
            await update.message.reply_text("⚠️ У тебя уже есть активная проверка!")
            return
        
        # Запускаем проверку
        await self._start_verification(update, context, user_id, username, chat_id)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status - статус верификации"""
        user_id = update.effective_user.id
        
        if user_id in self.verified_users:
            status_text = "✅ Статус: Верифицирован\n\nТы можешь свободно писать в чате!"
        elif user_id in self.verifications:
            verification = self.verifications[user_id]
            time_left = int(VERIFICATION_TIMEOUT - (time.time() - verification.start_time))
            attempts_left = MAX_ATTEMPTS - verification.attempts
            
            status_text = f"""
⏳ Статус: На проверке

🔄 Попыток осталось: {attempts_left}/{MAX_ATTEMPTS}
⏱️ Времени осталось: {time_left // 60}м {time_left % 60}с
📝 Тип проверки: {verification.challenge_type}

Пройди проверку, чтобы писать в чате!
"""
        elif user_id in self.banned_users:
            status_text = "🚫 Статус: Забанен\n\nОбратись к администраторам."
        else:
            status_text = "❓ Статус: Неизвестен\n\nИспользуй /verify для прохождения проверки."
        
        await update.message.reply_text(status_text)
    
    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /ban - забанить пользователя (только админы)"""
        if not await self._check_admin(update, context):
            return
        
        chat_id = update.effective_chat.id
        
        # Проверяем, есть ли reply на сообщение
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            target_user_id = target_user.id
            target_username = target_user.username or target_user.first_name
        elif context.args:
            # Пробуем получить ID из аргумента
            try:
                target_user_id = int(context.args[0])
                target_username = f"ID {target_user_id}"
            except ValueError:
                await update.message.reply_text(
                    "❌ Использование:\n"
                    "• /ban (ответом на сообщение)\n"
                    "• /ban [user_id]"
                )
                return
        else:
            await update.message.reply_text(
                "❌ Использование:\n"
                "• /ban (ответом на сообщение)\n"
                "• /ban [user_id]"
            )
            return
        
        try:
            # Баним
            await context.bot.ban_chat_member(chat_id, target_user_id)
            self.banned_users.add(target_user_id)
            self.stats['bans'] += 1
            
            await update.message.reply_text(f"✅ {target_username} забанен!")
        except Exception as e:
            logger.error(f"Ошибка бана: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    async def unban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /unban - разбанить пользователя (только админы)"""
        if not await self._check_admin(update, context):
            return
        
        chat_id = update.effective_chat.id
        
        # Проверяем, есть ли reply на сообщение
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            target_user_id = target_user.id
            target_username = target_user.username or target_user.first_name
        elif context.args:
            # Пробуем получить ID из аргумента
            try:
                target_user_id = int(context.args[0])
                target_username = f"ID {target_user_id}"
            except ValueError:
                await update.message.reply_text(
                    "❌ Использование:\n"
                    "• /unban (ответом на сообщение)\n"
                    "• /unban [user_id]"
                )
                return
        else:
            await update.message.reply_text(
                "❌ Использование:\n"
                "• /unban (ответом на сообщение)\n"
                "• /unban [user_id]"
            )
            return
        
        try:
            await context.bot.unban_chat_member(chat_id, target_user_id)
            if target_user_id in self.banned_users:
                self.banned_users.remove(target_user_id)
            
            await update.message.reply_text(f"✅ {target_username} разбанен!")
        except Exception as e:
            logger.error(f"Ошибка разбана: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    async def kick_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /kick - кикнуть пользователя (только админы)"""
        if not await self._check_admin(update, context):
            return
        
        chat_id = update.effective_chat.id
        
        # Проверяем, есть ли reply на сообщение
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            target_user_id = target_user.id
            target_username = target_user.username or target_user.first_name
        elif context.args:
            # Пробуем получить ID из аргумента
            try:
                target_user_id = int(context.args[0])
                target_username = f"ID {target_user_id}"
            except ValueError:
                await update.message.reply_text(
                    "❌ Использование:\n"
                    "• /kick (ответом на сообщение)\n"
                    "• /kick [user_id]"
                )
                return
        else:
            await update.message.reply_text(
                "❌ Использование:\n"
                "• /kick (ответом на сообщение)\n"
                "• /kick [user_id]"
            )
            return
        
        try:
            await context.bot.ban_chat_member(chat_id, target_user_id)
            await context.bot.unban_chat_member(chat_id, target_user_id)
            self.stats['kicks'] += 1
            
            await update.message.reply_text(f"✅ {target_username} кикнут!")
        except Exception as e:
            logger.error(f"Ошибка кика: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")

    async def mute_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /mute - замутить пользователя (только админы)"""
        if not await self._check_admin(update, context):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /mute @username [минуты]")
            return
        
        target_username = context.args[0].lstrip('@')
        duration = int(context.args[1]) if len(context.args) > 1 else 60
        chat_id = update.effective_chat.id
        
        try:
            chat_member = await context.bot.get_chat_member(chat_id, target_username)
            target_user_id = chat_member.user.id
            
            until_date = datetime.now() + timedelta(minutes=duration)
            
            await context.bot.restrict_chat_member(
                chat_id,
                target_user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            
            await update.message.reply_text(
                f"🔇 @{target_username} замучен на {duration} минут!"
            )
        except Exception as e:
            logger.error(f"Ошибка мута: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    async def unmute_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /unmute - размутить пользователя (только админы)"""
        if not await self._check_admin(update, context):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /unmute @username")
            return
        
        target_username = context.args[0].lstrip('@')
        chat_id = update.effective_chat.id
        
        try:
            chat_member = await context.bot.get_chat_member(chat_id, target_username)
            target_user_id = chat_member.user.id
            
            await context.bot.restrict_chat_member(
                chat_id,
                target_user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            
            await update.message.reply_text(f"🔊 @{target_username} размучен!")
        except Exception as e:
            logger.error(f"Ошибка размута: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    async def warn_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /warn - предупредить пользователя (только админы)"""
        if not await self._check_admin(update, context):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /warn @username [причина]")
            return
        
        target_username = context.args[0].lstrip('@')
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Нарушение правил"
        
        self.stats['warnings'] += 1
        
        await update.message.reply_text(
            f"⚠️ @{target_username} получил предупреждение!\n\n"
            f"Причина: {reason}"
        )
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /settings - настройки группы (только админы)"""
        if not await self._check_admin(update, context):
            return
        
        chat_id = update.effective_chat.id
        
        settings_text = """
⚙️ Настройки группы

Текущие настройки:
• Автопроверка новых участников: ✅
• Время на проверку: 5 минут
• Количество попыток: 5
• Автоудаление сообщений: ✅
• Уведомления в личку: ✅
• Типов проверок: 10

Для изменения настроек используй команды:
/toggle_autocheck - Вкл/выкл автопроверку
/set_timeout [минуты] - Время на проверку
/set_attempts [число] - Количество попыток
/toggle_autodelete - Вкл/выкл автоудаление
/toggle_dm - Вкл/выкл уведомления в ЛС

📊 Статистика группы:
• Участников верифицировано: {len(self.verified_users)}
• Забанено: {len(self.banned_users)}
• На проверке: {len(self.verifications)}
"""
        
        await update.message.reply_text(settings_text)
    
    async def whitelist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /whitelist - добавить в белый список (только админы)"""
        if not await self._check_admin(update, context):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /whitelist @username")
            return
        
        target_username = context.args[0].lstrip('@')
        chat_id = update.effective_chat.id
        
        try:
            chat_member = await context.bot.get_chat_member(chat_id, target_username)
            target_user_id = chat_member.user.id
            
            self.verified_users.add(target_user_id)
            
            await update.message.reply_text(
                f"✅ @{target_username} добавлен в белый список!"
            )
        except Exception as e:
            logger.error(f"Ошибка добавления в белый список: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    async def blacklist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /blacklist - добавить в чёрный список (только админы)"""
        if not await self._check_admin(update, context):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /blacklist @username")
            return
        
        target_username = context.args[0].lstrip('@')
        chat_id = update.effective_chat.id
        
        try:
            chat_member = await context.bot.get_chat_member(chat_id, target_username)
            target_user_id = chat_member.user.id
            
            self.banned_users.add(target_user_id)
            await context.bot.ban_chat_member(chat_id, target_user_id)
            
            await update.message.reply_text(
                f"🚫 @{target_username} добавлен в чёрный список!"
            )
        except Exception as e:
            logger.error(f"Ошибка добавления в чёрный список: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    async def _check_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Проверка прав администратора"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status in ['creator', 'administrator']:
                return True
            else:
                await update.message.reply_text("❌ Эта команда только для администраторов!")
                return False
        except Exception as e:
            logger.error(f"Ошибка проверки прав: {e}")
            return False
    
    async def cleanup_task(self, context: ContextTypes.DEFAULT_TYPE):
        """Периодическая очистка устаревших данных"""
        current_time = time.time()
        expired_users = []
        
        for user_id, verification in self.verifications.items():
            if current_time - verification.start_time > VERIFICATION_TIMEOUT:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            if user_id in self.verifications:
                del self.verifications[user_id]
        
        if expired_users:
            logger.info(f"Очищено {len(expired_users)} устаревших верификаций")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Ошибка: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Произошла ошибка. Попробуй позже."
            )
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик сообщений от непроверенных пользователей"""
        if not update.message or not update.message.from_user:
            return
        
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
        text = update.message.text or ""
        
        # Проверяем, находится ли пользователь на проверке
        if user_id in self.verifications:
            verification = self.verifications[user_id]
            attempts_left = MAX_ATTEMPTS - verification.attempts
            
            try:
                # Удаляем сообщение пользователя
                await update.message.delete()
                
                # Отправляем напоминание
                reminder = await update.message.reply_text(
                    f"🔒 {update.message.from_user.first_name}, ты не можешь писать в группе!\n\n"
                    f"Сначала пройди проверку выше ⬆️\n"
                    f"⏱️ Попыток осталось: {attempts_left}"
                )
                
                # Удаляем напоминание через 5 секунд
                await asyncio.sleep(5)
                await reminder.delete()
            except Exception as e:
                logger.error(f"Ошибка обработки сообщения от непроверенного: {e}")
            return
        
        # Если пользователь верифицирован, проверяем на спам и собираем статистику
        if user_id in self.verified_users:
            # Статистика
            self.group_stats.add_message(user_id)
            
            # Проверка на спам
            if self.anti_spam.check_spam(user_id, text):
                try:
                    # Удаляем спам
                    await update.message.delete()
                    
                    # Предупреждение
                    self.reputation_system.add_warning(user_id)
                    warnings = self.reputation_system.get_warnings(user_id)
                    
                    if warnings >= 3:
                        # Бан за 3 предупреждения
                        await context.bot.ban_chat_member(chat_id, user_id)
                        self.banned_users.add(user_id)
                        await update.message.reply_text(
                            f"🚫 Пользователь забанен за спам (3 предупреждения)"
                        )
                    else:
                        # Просто предупреждение
                        warning_msg = await update.message.reply_text(
                            f"⚠️ Предупреждение за спам/флуд!\n"
                            f"Предупреждений: {warnings}/3"
                        )
                        await asyncio.sleep(10)
                        await warning_msg.delete()
                except Exception as e:
                    logger.error(f"Ошибка обработки спама: {e}")
    
    async def run_async(self):
        """Асинхронный запуск бота"""
        logger.info("Запуск бота...")
        
        # Создаём приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CommandHandler("verify", self.verify_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("ban", self.ban_command))
        application.add_handler(CommandHandler("unban", self.unban_command))
        application.add_handler(CommandHandler("kick", self.kick_command))
        application.add_handler(CommandHandler("mute", self.mute_command))
        application.add_handler(CommandHandler("unmute", self.unmute_command))
        application.add_handler(CommandHandler("warn", self.warn_command))
        application.add_handler(CommandHandler("settings", self.settings_command))
        application.add_handler(CommandHandler("whitelist", self.whitelist_command))
        application.add_handler(CommandHandler("blacklist", self.blacklist_command))
        
        # Новые команды
        application.add_handler(CommandHandler("feedback", feedback_command))
        application.add_handler(CommandHandler("reputation", reputation_command))
        application.add_handler(CommandHandler("top", top_command))
        application.add_handler(CommandHandler("rules", rules_command))
        application.add_handler(CommandHandler("setrules", setrules_command))
        application.add_handler(CommandHandler("support", support_command))
        
        # Обработчик новых участников
        application.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            self.new_member_handler
        ))
        
        # Обработчик кнопок
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Обработчик сообщений от непроверенных пользователей
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.message_handler
        ))
        
        # Периодическая очистка
        application.job_queue.run_repeating(
            self.cleanup_task,
            interval=CLEANUP_INTERVAL,
            first=CLEANUP_INTERVAL
        )
        
        # Обработчик ошибок
        application.add_error_handler(self.error_handler)
        
        # Сохраняем время старта
        self.start_time = time.time()
        
        # Сохраняем системы в bot_data для доступа из команд
        application.bot_data['reputation_system'] = self.reputation_system
        application.bot_data['group_stats'] = self.group_stats
        application.bot_data['welcome_rules'] = self.welcome_rules
        
        logger.info("Бот запущен!")
        
        # Инициализируем и запускаем
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)


async def health_check(request):
    """HTTP endpoint для Render"""
    uptime = int(time.time() - start_time) if 'start_time' in globals() else 0
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Telegram Anti-Bot</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .container {{
                text-align: center;
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }}
            h1 {{ font-size: 48px; margin: 0; }}
            p {{ font-size: 20px; margin: 10px 0; }}
            .status {{ color: #4ade80; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Telegram Anti-Bot</h1>
            <p class="status">✅ Работает</p>
            <p>⏱️ Время работы: {hours}ч {minutes}м</p>
            <p>🛡️ Защита группы активна</p>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html', charset='utf-8')


async def start_web_server():
    """Запуск веб-сервера для Render"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    port = int(os.environ.get('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"🌐 HTTP сервер запущен на порту {port}")
    
    return runner


async def main():
    """Главная функция"""
    global start_time
    start_time = time.time()
    
    # Запускаем веб-сервер
    runner = await start_web_server()
    
    # Запускаем бота
    bot = AntiBot()
    await bot.run_async()
    
    # Держим программу запущенной
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
        await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
