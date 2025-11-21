# SANAS - Модульные компрессорные станции

Django веб-сайт для компании SANAS, специализирующейся на модульных компрессорных станциях.

## Установка и запуск

### 1. Установите зависимости

```bash
pip install -r requirements.txt
```

### 2. Выполните миграции базы данных

```bash
python manage.py migrate
```

### 3. Создайте суперпользователя (опционально)

```bash
python manage.py createsuperuser
```

### 4. Запустите сервер разработки

```bash
python manage.py runserver
```

Сайт будет доступен по адресу: http://127.0.0.1:8000/

## Структура проекта

```
SANAS/
├── sanas_project/          # Основная конфигурация Django проекта
│   ├── settings.py         # Настройки проекта
│   ├── urls.py             # Главный URL конфигуратор
│   └── wsgi.py
├── website/                # Django приложение сайта
│   ├── static/             # Статические файлы
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── script.js
│   ├── templates/          # HTML шаблоны
│   │   └── index.html
│   ├── views.py            # Представления (views)
│   └── urls.py             # URL маршруты приложения
├── manage.py               # Утилита управления Django
└── requirements.txt        # Зависимости проекта
```

## Функционал

- **Главная страница**: Информация о компании и продукции
- **Каталог продукции**: МКС-10, МКС-20, МКС-40
- **Преимущества**: Модульная конструкция, надежность, энергоэффективность
- **Контактная форма**: Форма для отправки заявок
- **Адаптивный дизайн**: Поддержка мобильных устройств

## Дизайн

Сайт выполнен в стиле промышленного оборудования с использованием:
- Желто-черная цветовая схема (#fab915)
- Шрифт Montserrat
- Адаптивная верстка
- Плавные анимации

## Настройки

### Язык и часовой пояс

Проект настроен на русский язык (`ru-ru`) и часовой пояс Алматы (`Asia/Almaty`).

### Email (опционально)

Для настройки отправки email через контактную форму, раскомментируйте код в `website/views.py` и настройте параметры email в `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_password'
DEFAULT_FROM_EMAIL = 'your_email@gmail.com'
```

## Разработка

Для разработки используйте:

```bash
python manage.py runserver 0.0.0.0:8000
```

## Производство

Перед развертыванием на продакшен:

1. Измените `DEBUG = False` в `settings.py`
2. Добавьте домен в `ALLOWED_HOSTS`
3. Настройте правильную базу данных (PostgreSQL рекомендуется)
4. Соберите статические файлы: `python manage.py collectstatic`
5. Настройте веб-сервер (nginx + gunicorn)

## Лицензия

© 2025 SANAS. Все права защищены.
