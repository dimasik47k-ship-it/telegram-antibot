# 📦 Инструкция по установке

## Требования

- Python 3.8 или выше
- pip (менеджер пакетов Python)
- Telegram аккаунт
- Токен бота от @BotFather

## Шаг 1: Установка Python

### Windows

1. Скачай Python с официального сайта: https://www.python.org/downloads/
2. Запусти установщик
3. Обязательно отметь "Add Python to PATH"
4. Нажми "Install Now"

Проверь установку:
```bash
python --version
```

### Linux

```bash
sudo apt update
sudo apt install python3 python3-pip
```

Проверь установку:
```bash
python3 --version
```

### macOS

```bash
brew install python3
```

Проверь установку:
```bash
python3 --version
```

## Шаг 2: Скачивание бота

### Вариант 1: Git

```bash
git clone <repository-url>
cd telegram-antibot
```

### Вариант 2: Скачать ZIP

1. Скачай ZIP архив
2. Распакуй в любую папку
3. Открой папку в терминале

## Шаг 3: Установка зависимостей

### Windows

```bash
pip install -r requirements.txt
```

### Linux/macOS

```bash
pip3 install -r requirements.txt
```

Или установи вручную:
```bash
pip install python-telegram-bot==20.7
```

## Шаг 4: Настройка токена

Токен уже прописан в коде:
```python
BOT_TOKEN = "7681253398:AAGAr7kug1Vd0o1yNsk6yJj6B8R3Xfnf8Hk"
```

Если нужен свой токен:

1. Открой Telegram
2. Найди @BotFather
3. Отправь команду `/newbot`
4. Следуй инструкциям
5. Скопируй полученный токен
6. Замени токен в файле `bot.py` или `config.py`

## Шаг 5: Запуск бота

### Windows

Вариант 1 - Двойной клик:
```
Запусти start.bat
```

Вариант 2 - Командная строка:
```bash
python bot.py
```

### Linux/macOS

Вариант 1 - Скрипт:
```bash
chmod +x start.sh
./start.sh
```

Вариант 2 - Терминал:
```bash
python3 bot.py
```

## Шаг 6: Добавление в группу

1. Найди своего бота в Telegram
2. Добавь его в группу
3. Дай права администратора:
   - ✅ Удаление сообщений
   - ✅ Бан пользователей
   - ✅ Ограничение пользователей
   - ✅ Закрепление сообщений
   - ✅ Приглашение пользователей

## Шаг 7: Проверка работы

1. Отправь команду `/start` боту в личку
2. Отправь команду `/help` в группе
3. Попробуй добавить тестового пользователя

## Возможные проблемы

### Ошибка: "No module named 'telegram'"

Решение:
```bash
pip install python-telegram-bot
```

### Ошибка: "Invalid token"

Решение:
1. Проверь токен в файле `bot.py`
2. Убедись, что токен скопирован полностью
3. Проверь, что нет лишних пробелов

### Ошибка: "Permission denied"

Решение (Linux/macOS):
```bash
chmod +x start.sh
chmod +x bot.py
```

### Бот не отвечает

Решение:
1. Проверь, что бот запущен
2. Проверь интернет-соединение
3. Проверь логи в файле `bot.log`
4. Перезапусти бота

### Бот не может кикать пользователей

Решение:
1. Убедись, что бот - администратор
2. Проверь права бота в настройках группы
3. Дай боту все необходимые права

## Автозапуск

### Windows (Task Scheduler)

1. Открой "Планировщик заданий"
2. Создай новое задание
3. Триггер: При входе в систему
4. Действие: Запустить программу
5. Программа: `python`
6. Аргументы: `C:\path\to\bot.py`

### Linux (systemd)

Создай файл `/etc/systemd/system/antibot.service`:

```ini
[Unit]
Description=Telegram Anti-Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 /path/to/bot/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Запусти:
```bash
sudo systemctl enable antibot
sudo systemctl start antibot
```

### macOS (launchd)

Создай файл `~/Library/LaunchAgents/com.antibot.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.antibot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/bot/bot.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Запусти:
```bash
launchctl load ~/Library/LaunchAgents/com.antibot.plist
```

## Обновление

### Обновление зависимостей

```bash
pip install --upgrade python-telegram-bot
```

### Обновление бота

1. Скачай новую версию
2. Замени файлы
3. Перезапусти бота

## Резервное копирование

Важные файлы для бэкапа:
- `bot_data.json` - данные пользователей
- `stats.json` - статистика
- `bot.log` - логи
- `config.py` - настройки

Создай бэкап:
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz bot_data.json stats.json bot.log config.py
```

## Поддержка

При возникновении проблем:

1. Проверь логи: `bot.log`
2. Проверь версию Python: `python --version`
3. Проверь зависимости: `pip list`
4. Перезапусти бота
5. Проверь права бота в группе

## Полезные команды

Проверка статуса:
```bash
ps aux | grep bot.py
```

Остановка бота:
```bash
pkill -f bot.py
```

Просмотр логов:
```bash
tail -f bot.log
```

Очистка логов:
```bash
> bot.log
```

## Готово!

Бот установлен и готов к работе! 🎉
