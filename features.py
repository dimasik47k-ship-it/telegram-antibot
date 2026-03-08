#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Дополнительные функции бота
"""

import re
import time
from collections import defaultdict
from typing import Dict, List, Set
from telegram import Update
from telegram.ext import ContextTypes

# ID бота поддержки
SUPPORT_BOT = "@HelloFridge_bot"

class AntiSpam:
    """Система анти-спама"""
    
    def __init__(self):
        self.user_messages: Dict[int, List[float]] = defaultdict(list)
        self.spam_patterns = [
            r'https?://\S+',  # Ссылки
            r't\.me/\S+',  # Telegram ссылки
            r'@\w+bot',  # Упоминания ботов
            r'💰|💵|💴|💶|💷',  # Деньги
            r'🎁|🎉|🎊',  # Подарки
            r'БЕСПЛАТНО|FREE|ХАЛЯВА',  # Спам слова
        ]
    
    def check_spam(self, user_id: int, text: str) -> bool:
        """Проверка на спам"""
        current_time = time.time()
        
        # Очищаем старые сообщения
        self.user_messages[user_id] = [
            t for t in self.user_messages[user_id]
            if current_time - t < 10
        ]
        
        # Добавляем текущее
        self.user_messages[user_id].append(current_time)
        
        # Проверка на флуд (больше 5 сообщений за 10 секунд)
        if len(self.user_messages[user_id]) > 5:
            return True
        
        # Проверка на спам-паттерны
        for pattern in self.spam_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False


class ReputationSystem:
    """Система репутации пользователей"""
    
    def __init__(self):
        self.reputation: Dict[int, int] = defaultdict(int)
        self.warnings: Dict[int, int] = defaultdict(int)
    
    def add_reputation(self, user_id: int, points: int = 1):
        """Добавить репутацию"""
        self.reputation[user_id] += points
    
    def remove_reputation(self, user_id: int, points: int = 1):
        """Убрать репутацию"""
        self.reputation[user_id] -= points
    
    def get_reputation(self, user_id: int) -> int:
        """Получить репутацию"""
        return self.reputation[user_id]
    
    def add_warning(self, user_id: int):
        """Добавить предупреждение"""
        self.warnings[user_id] += 1
        self.remove_reputation(user_id, 5)
    
    def get_warnings(self, user_id: int) -> int:
        """Получить количество предупреждений"""
        return self.warnings[user_id]
    
    def reset_warnings(self, user_id: int):
        """Сбросить предупреждения"""
        self.warnings[user_id] = 0
        self.add_reputation(user_id, 5)


class GroupStats:
    """Статистика активности группы"""
    
    def __init__(self):
        self.messages_count: Dict[int, int] = defaultdict(int)
        self.active_users: Set[int] = set()
        self.daily_messages = 0
        self.last_reset = time.time()
    
    def add_message(self, user_id: int):
        """Добавить сообщение"""
        self.messages_count[user_id] += 1
        self.active_users.add(user_id)
        self.daily_messages += 1
        
        # Сброс ежедневной статистики
        if time.time() - self.last_reset > 86400:  # 24 часа
            self.daily_messages = 0
            self.last_reset = time.time()
    
    def get_top_users(self, limit: int = 10) -> List[tuple]:
        """Получить топ активных пользователей"""
        sorted_users = sorted(
            self.messages_count.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_users[:limit]
    
    def get_stats(self) -> dict:
        """Получить общую статистику"""
        return {
            'total_messages': sum(self.messages_count.values()),
            'active_users': len(self.active_users),
            'daily_messages': self.daily_messages,
            'top_users': self.get_top_users(5)
        }


class WelcomeRules:
    """Приветственные сообщения с правилами"""
    
    def __init__(self):
        self.rules = {}
        self.welcome_messages = {}
    
    def set_rules(self, chat_id: int, rules: str):
        """Установить правила группы"""
        self.rules[chat_id] = rules
    
    def get_rules(self, chat_id: int) -> str:
        """Получить правила группы"""
        return self.rules.get(chat_id, "Правила не установлены")
    
    def set_welcome(self, chat_id: int, message: str):
        """Установить приветственное сообщение"""
        self.welcome_messages[chat_id] = message
    
    def get_welcome(self, chat_id: int, username: str) -> str:
        """Получить приветственное сообщение"""
        default = f"👋 Добро пожаловать, {username}!"
        message = self.welcome_messages.get(chat_id, default)
        return message.replace("{username}", username)


# Команды для новых функций

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /feedback - отправить отзыв"""
    if not context.args:
        await update.message.reply_text(
            f"📝 Отправить отзыв:\n\n"
            f"/feedback [ваш отзыв]\n\n"
            f"Или напишите напрямую: {SUPPORT_BOT}"
        )
        return
    
    feedback_text = ' '.join(context.args)
    user = update.effective_user
    
    # Здесь можно отправить отзыв в канал или админу
    await update.message.reply_text(
        f"✅ Спасибо за отзыв!\n\n"
        f"Ваше сообщение получено. Мы обязательно его рассмотрим.\n\n"
        f"Для прямой связи: {SUPPORT_BOT}"
    )


async def reputation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /reputation - показать репутацию"""
    user_id = update.effective_user.id
    
    # Получаем репутацию из контекста бота
    if hasattr(context.bot_data, 'reputation_system'):
        rep_system = context.bot_data['reputation_system']
        reputation = rep_system.get_reputation(user_id)
        warnings = rep_system.get_warnings(user_id)
        
        await update.message.reply_text(
            f"📊 Твоя репутация:\n\n"
            f"⭐ Репутация: {reputation}\n"
            f"⚠️ Предупреждений: {warnings}/3\n\n"
            f"Будь активным и соблюдай правила!"
        )
    else:
        await update.message.reply_text("⚠️ Система репутации не активна")


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /top - топ активных пользователей"""
    if hasattr(context.bot_data, 'group_stats'):
        stats = context.bot_data['group_stats']
        top_users = stats.get_top_users(10)
        
        if not top_users:
            await update.message.reply_text("📊 Пока нет статистики")
            return
        
        text = "🏆 Топ активных пользователей:\n\n"
        for i, (user_id, count) in enumerate(top_users, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{emoji} ID {user_id}: {count} сообщений\n"
        
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("⚠️ Статистика не активна")


async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /rules - показать правила"""
    chat_id = update.effective_chat.id
    
    if hasattr(context.bot_data, 'welcome_rules'):
        rules_system = context.bot_data['welcome_rules']
        rules = rules_system.get_rules(chat_id)
        
        await update.message.reply_text(
            f"📜 Правила группы:\n\n{rules}\n\n"
            f"Соблюдай правила и будь вежлив!"
        )
    else:
        await update.message.reply_text(
            "📜 Правила группы:\n\n"
            "1. Будь вежлив и уважай других\n"
            "2. Не спамь и не флуди\n"
            "3. Не размещай рекламу без разрешения\n"
            "4. Не используй мат и оскорбления\n"
            "5. Соблюдай тему группы"
        )


async def setrules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /setrules - установить правила (только админы)"""
    # Проверка прав админа
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ['creator', 'administrator']:
            await update.message.reply_text("❌ Только для администраторов!")
            return
    except:
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Использование: /setrules [текст правил]"
        )
        return
    
    rules_text = ' '.join(context.args)
    
    if not hasattr(context.bot_data, 'welcome_rules'):
        context.bot_data['welcome_rules'] = WelcomeRules()
    
    context.bot_data['welcome_rules'].set_rules(chat_id, rules_text)
    
    await update.message.reply_text("✅ Правила обновлены!")


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /support - связь с поддержкой"""
    await update.message.reply_text(
        f"💬 Поддержка бота:\n\n"
        f"Напиши нам: {SUPPORT_BOT}\n\n"
        f"Или используй /feedback для отправки отзыва"
    )
