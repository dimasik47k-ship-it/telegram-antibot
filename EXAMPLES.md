# 📚 Примеры использования

## Базовое использование

### Запуск бота

```bash
# Windows
python bot.py

# Linux/macOS
python3 bot.py
```

### Первый запуск

1. Запусти бота
2. Открой Telegram
3. Найди своего бота
4. Отправь `/start`
5. Добавь в группу

## Примеры команд

### Для пользователей

```
# Начать работу с ботом
/start

# Получить помощь
/help

# Пройти проверку вручную
/verify

# Проверить свой статус
/status

# Посмотреть статистику
/stats
```

### Для администраторов

```
# Забанить пользователя
/ban @username

# Разбанить пользователя
/unban @username

# Кикнуть пользователя
/kick @username

# Замутить на 30 минут
/mute @username 30

# Размутить пользователя
/unmute @username

# Предупредить пользователя
/warn @username Нарушение правил

# Добавить в белый список
/whitelist @username

# Добавить в чёрный список
/blacklist @username

# Настройки группы
/settings
```

## Сценарии использования

### Сценарий 1: Защита от спам-ботов

**Проблема:** В группу постоянно заходят спам-боты

**Решение:**
1. Добавь бота в группу
2. Дай права администратора
3. Бот автоматически проверит всех новых участников
4. Боты не смогут пройти проверку и будут кикнуты

**Результат:** Группа защищена от спам-ботов

### Сценарий 2: Модерация большой группы

**Проблема:** Сложно модерировать большую группу

**Решение:**
1. Используй команды модерации:
   - `/ban` для постоянного бана
   - `/mute` для временного мута
   - `/warn` для предупреждений
2. Добавь проблемных пользователей в чёрный список
3. Добавь доверенных в белый список

**Результат:** Упрощённая модерация

### Сценарий 3: Приватная группа

**Проблема:** Нужна закрытая группа только для людей

**Решение:**
1. Включи все типы проверок
2. Установи сложность `hard`
3. Уменьши количество попыток до 3
4. Уменьши время на проверку до 3 минут

**Настройки в config.py:**
```python
VERIFICATION_SETTINGS = {
    'max_attempts': 3,
    'timeout': 180,
    'auto_kick': True
}

CHALLENGE_SETTINGS = {
    'difficulty': 'hard'
}
```

**Результат:** Только люди смогут войти

### Сценарий 4: Публичная группа

**Проблема:** Нужна открытая группа, но без ботов

**Решение:**
1. Используй лёгкие проверки
2. Дай больше попыток (7-10)
3. Увеличь время на проверку (10 минут)

**Настройки в config.py:**
```python
VERIFICATION_SETTINGS = {
    'max_attempts': 10,
    'timeout': 600,
    'auto_kick': False
}

CHALLENGE_SETTINGS = {
    'difficulty': 'easy'
}
```

**Результат:** Лёгкий вход для людей, защита от ботов

### Сценарий 5: Анти-спам

**Проблема:** Пользователи спамят в группе

**Решение:**
1. Включи анти-спам
2. Настрой лимиты

**Настройки в config.py:**
```python
ANTISPAM_SETTINGS = {
    'enabled': True,
    'max_messages': 5,
    'time_window': 10,
    'auto_mute': True,
    'mute_duration': 300
}
```

**Результат:** Спамеры автоматически мутятся

## Примеры настройки

### Пример 1: Строгая проверка

```python
# config.py

VERIFICATION_SETTINGS = {
    'max_attempts': 3,
    'timeout': 180,
    'auto_kick': True,
    'send_dm': True,
    'delete_messages': True
}

CHALLENGE_SETTINGS = {
    'enabled_types': [
        'math',
        'sequence',
        'logic',
        'comparison'
    ],
    'difficulty': 'hard',
    'random_order': True
}
```

### Пример 2: Мягкая проверка

```python
# config.py

VERIFICATION_SETTINGS = {
    'max_attempts': 10,
    'timeout': 600,
    'auto_kick': False,
    'send_dm': True,
    'delete_messages': False
}

CHALLENGE_SETTINGS = {
    'enabled_types': [
        'emoji',
        'color',
        'pattern'
    ],
    'difficulty': 'easy',
    'random_order': True
}
```

### Пример 3: Только математика

```python
# config.py

CHALLENGE_SETTINGS = {
    'enabled_types': [
        'math'
    ],
    'difficulty': 'medium',
    'random_order': False
}
```

### Пример 4: Без эмодзи

```python
# config.py

CHALLENGE_SETTINGS = {
    'enabled_types': [
        'math',
        'sequence',
        'logic',
        'comparison',
        'word'
    ],
    'difficulty': 'medium',
    'random_order': True
}
```

## Примеры кастомизации

### Пример 1: Свои сообщения

```python
# config.py

MESSAGES = {
    'welcome': """
🎉 Привет! Добро пожаловать в нашу группу!

Пожалуйста, пройди быструю проверку:

{question}

У тебя {timeout} минут и {attempts} попыток.
Удачи! 🍀
""",
    
    'verification_success': """
✅ Отлично! Ты прошёл проверку!

Добро пожаловать в нашу группу, {username}!
Теперь можешь свободно общаться.

Не забудь прочитать правила! 📋
""",
    
    'verification_failed': """
😢 К сожалению, ты не прошёл проверку.

Попытки исчерпаны: {attempts}/{max_attempts}

Если хочешь вернуться, попробуй снова позже.
"""
}
```

### Пример 2: Свои эмодзи

```python
# config.py

EMOJI_CATEGORIES = {
    'fruits': ['🍎', '🍊', '🍋', '🍌', '🍉'],
    'vehicles': ['🚗', '🚕', '🚙', '🚌', '🚎'],
    'sports': ['⚽', '🏀', '🏈', '⚾', '🎾']
}
```

### Пример 3: Свои вопросы

```python
# config.py

LOGIC_QUESTIONS = [
    ("Столица России?", "Москва", ["Москва", "Питер", "Киев", "Минск", "Варшава"]),
    ("2+2=?", "4", ["3", "4", "5", "6", "7"]),
    ("Цвет неба?", "Синий", ["Красный", "Синий", "Зелёный", "Жёлтый", "Чёрный"])
]
```

## Примеры интеграции

### Пример 1: Логирование в файл

```python
# bot.py

import logging

logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Пример 2: Сохранение статистики

```python
# bot.py

import json

def save_stats(self):
    with open('stats.json', 'w') as f:
        json.dump(self.stats, f, indent=2)

def load_stats(self):
    try:
        with open('stats.json', 'r') as f:
            return json.load(f)
    except:
        return {}
```

### Пример 3: Уведомления админам

```python
# bot.py

async def notify_admins(self, message: str):
    admin_ids = [123456789, 987654321]  # ID админов
    
    for admin_id in admin_ids:
        try:
            await self.bot.send_message(admin_id, message)
        except:
            pass
```

## Примеры автоматизации

### Пример 1: Автоочистка каждый час

```python
# bot.py

application.job_queue.run_repeating(
    self.cleanup_task,
    interval=3600,  # 1 час
    first=3600
)
```

### Пример 2: Ежедневная статистика

```python
# bot.py

async def daily_stats(self, context):
    stats_text = self.generate_stats()
    await context.bot.send_message(ADMIN_CHAT_ID, stats_text)

application.job_queue.run_daily(
    self.daily_stats,
    time=datetime.time(hour=9, minute=0)  # 9:00 каждый день
)
```

### Пример 3: Автобэкап

```python
# bot.py

async def backup_data(self, context):
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy('bot_data.json', f'backup_{timestamp}.json')

application.job_queue.run_repeating(
    self.backup_data,
    interval=86400,  # 1 день
    first=86400
)
```

## Советы и трюки

### Совет 1: Тестирование

Создай тестовую группу для проверки настроек перед использованием в основной группе.

### Совет 2: Мониторинг

Регулярно проверяй логи и статистику для выявления проблем.

### Совет 3: Бэкапы

Делай регулярные бэкапы файлов `bot_data.json` и `stats.json`.

### Совет 4: Обновления

Следи за обновлениями библиотеки `python-telegram-bot`.

### Совет 5: Безопасность

Не публикуй токен бота в открытом доступе.

## Частые ошибки

### Ошибка 1: Бот не кикает

**Причина:** Нет прав администратора

**Решение:** Дай боту права в настройках группы

### Ошибка 2: Проверка не приходит

**Причина:** Бот не может писать в группу

**Решение:** Проверь настройки группы

### Ошибка 3: Все кикаются

**Причина:** Слишком сложные проверки

**Решение:** Упрости проверки или дай больше попыток

---

Больше примеров в документации!
