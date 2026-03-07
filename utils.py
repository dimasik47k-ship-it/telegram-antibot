#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Дополнительные утилиты для бота
"""

import json
import hashlib
import time
from typing import Dict, List, Optional
from datetime import datetime


class DataStorage:
    """Класс для хранения данных без внешних зависимостей"""
    
    def __init__(self, filename: str = "bot_data.json"):
        self.filename = filename
        self.data = self.load()
    
    def load(self) -> dict:
        """Загрузка данных из файла"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'verified_users': [],
                'banned_users': [],
                'stats': {},
                'settings': {}
            }
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return {}
    
    def save(self):
        """Сохранение данных в файл"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения данных: {e}")
    
    def add_verified_user(self, user_id: int):
        """Добавить верифицированного пользователя"""
        if user_id not in self.data['verified_users']:
            self.data['verified_users'].append(user_id)
            self.save()
    
    def add_banned_user(self, user_id: int):
        """Добавить забаненного пользователя"""
        if user_id not in self.data['banned_users']:
            self.data['banned_users'].append(user_id)
            self.save()
    
    def remove_banned_user(self, user_id: int):
        """Удалить из забаненных"""
        if user_id in self.data['banned_users']:
            self.data['banned_users'].remove(user_id)
            self.save()
    
    def is_verified(self, user_id: int) -> bool:
        """Проверить, верифицирован ли пользователь"""
        return user_id in self.data['verified_users']
    
    def is_banned(self, user_id: int) -> bool:
        """Проверить, забанен ли пользователь"""
        return user_id in self.data['banned_users']
    
    def update_stats(self, key: str, value: int = 1):
        """Обновить статистику"""
        if key not in self.data['stats']:
            self.data['stats'][key] = 0
        self.data['stats'][key] += value
        self.save()
    
    def get_stats(self) -> dict:
        """Получить статистику"""
        return self.data['stats']


class AntiSpam:
    """Защита от спама"""
    
    def __init__(self, max_messages: int = 5, time_window: int = 10):
        self.max_messages = max_messages
        self.time_window = time_window
        self.user_messages: Dict[int, List[float]] = {}
    
    def check_spam(self, user_id: int) -> bool:
        """Проверить, спамит ли пользователь"""
        current_time = time.time()
        
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        # Удаляем старые сообщения
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if current_time - msg_time < self.time_window
        ]
        
        # Добавляем текущее сообщение
        self.user_messages[user_id].append(current_time)
        
        # Проверяем лимит
        return len(self.user_messages[user_id]) > self.max_messages
    
    def reset_user(self, user_id: int):
        """Сбросить счётчик для пользователя"""
        if user_id in self.user_messages:
            del self.user_messages[user_id]


class UserAnalyzer:
    """Анализ поведения пользователей"""
    
    def __init__(self):
        self.user_data: Dict[int, dict] = {}
    
    def analyze_username(self, username: str) -> dict:
        """Анализ имени пользователя"""
        score = 0
        flags = []
        
        if not username:
            flags.append("no_username")
            score += 10
        
        # Проверка на подозрительные паттерны
        if username and len(username) < 3:
            flags.append("short_username")
            score += 5
        
        if username and username.isdigit():
            flags.append("numeric_username")
            score += 15
        
        if username and any(char in username for char in ['bot', 'spam', 'fake']):
            flags.append("suspicious_keywords")
            score += 20
        
        # Проверка на случайные символы
        if username and len(set(username)) < len(username) * 0.3:
            flags.append("repetitive_chars")
            score += 10
        
        return {
            'score': score,
            'flags': flags,
            'is_suspicious': score > 20
        }
    
    def analyze_join_pattern(self, user_id: int, chat_id: int) -> dict:
        """Анализ паттерна входа"""
        current_time = time.time()
        
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                'joins': [],
                'chats': set()
            }
        
        self.user_data[user_id]['joins'].append(current_time)
        self.user_data[user_id]['chats'].add(chat_id)
        
        # Проверка на массовый вход
        recent_joins = [
            join_time for join_time in self.user_data[user_id]['joins']
            if current_time - join_time < 3600  # последний час
        ]
        
        score = 0
        flags = []
        
        if len(recent_joins) > 5:
            flags.append("mass_joining")
            score += 30
        
        if len(self.user_data[user_id]['chats']) > 10:
            flags.append("many_chats")
            score += 20
        
        return {
            'score': score,
            'flags': flags,
            'is_suspicious': score > 25
        }


class Logger:
    """Простой логгер"""
    
    def __init__(self, filename: str = "bot.log"):
        self.filename = filename
    
    def log(self, level: str, message: str):
        """Записать лог"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"
        
        try:
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(log_message)
        except Exception as e:
            print(f"Ошибка записи лога: {e}")
    
    def info(self, message: str):
        """Информационное сообщение"""
        self.log("INFO", message)
    
    def warning(self, message: str):
        """Предупреждение"""
        self.log("WARNING", message)
    
    def error(self, message: str):
        """Ошибка"""
        self.log("ERROR", message)
    
    def debug(self, message: str):
        """Отладка"""
        self.log("DEBUG", message)


class RateLimiter:
    """Ограничитель частоты запросов"""
    
    def __init__(self, max_requests: int = 30, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[int, List[float]] = {}
    
    def check_limit(self, user_id: int) -> bool:
        """Проверить лимит запросов"""
        current_time = time.time()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Удаляем старые запросы
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if current_time - req_time < self.time_window
        ]
        
        # Проверяем лимит
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Добавляем текущий запрос
        self.requests[user_id].append(current_time)
        return True


class MessageFilter:
    """Фильтр сообщений"""
    
    def __init__(self):
        self.banned_words = [
            'спам', 'реклама', 'казино', 'ставки',
            'заработок', 'халява', 'бесплатно'
        ]
        self.banned_links = [
            't.me/', 'telegram.me/', 'http://', 'https://'
        ]
    
    def check_message(self, text: str) -> dict:
        """Проверить сообщение"""
        if not text:
            return {'is_spam': False, 'reasons': []}
        
        text_lower = text.lower()
        reasons = []
        
        # Проверка на запрещённые слова
        for word in self.banned_words:
            if word in text_lower:
                reasons.append(f"banned_word: {word}")
        
        # Проверка на ссылки
        for link in self.banned_links:
            if link in text_lower:
                reasons.append(f"link: {link}")
        
        # Проверка на капс
        if text.isupper() and len(text) > 10:
            reasons.append("all_caps")
        
        # Проверка на повторяющиеся символы
        if any(text.count(char) > len(text) * 0.3 for char in set(text)):
            reasons.append("repetitive_chars")
        
        return {
            'is_spam': len(reasons) > 0,
            'reasons': reasons
        }


def generate_user_hash(user_id: int, username: str) -> str:
    """Генерация хеша пользователя"""
    data = f"{user_id}:{username}:{time.time()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def format_time(seconds: int) -> str:
    """Форматирование времени"""
    if seconds < 60:
        return f"{seconds}с"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}м {secs}с"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}ч {minutes}м"


def format_number(number: int) -> str:
    """Форматирование числа"""
    if number < 1000:
        return str(number)
    elif number < 1000000:
        return f"{number / 1000:.1f}K"
    else:
        return f"{number / 1000000:.1f}M"
