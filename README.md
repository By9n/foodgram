[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com)
[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru)

# Foodgram «Блог рецептов»
## Описание:

Веб-приложение Foodgram, «Блог рецептов». Пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

## Стек технологий:
* Python
* React
* Django
* Django REST Framework
* Linux
* Docker
* Docker-compose
* Postgres
* Gunicorn
* Nginx
* Workflow

## Server IP:

https://foodgdrama.webhop.me

Адрес админки:
https://foodgdrama.webhop.me/admin

Данные для входа:
```
email - food@mail.ru
password - 123
```

## Запуск проекта локально:

1. Клонируйте репозиторий проекта с GitHub:
```
git clone git@github.com:By9n/foodgram.git
```

2. В терминале, перейдите в каталог: 
```
cd .../foodgram/infra
```

и создайте там файл .evn для хранения ключей:
```
DEBUG_STATUS = False, еcли планируете использовать проект для разработки укажите  True
SECRET_KEY = 'секретный ключ Django проекта'
DB_ENGINE=django.db.backends.postgresql # указываем, что используем postgresql
DB_NAME=postgres # указываем имя созданной базы данных
POSTGRES_USER=postgres # указываем имя своего пользователя для подключения к БД
POSTGRES_PASSWORD=postgres # устанавливаем свой пароль для подключения к БД
DB_HOST=db # указываем название сервиса (контейнера)
DB_PORT=5432 # указываем порт для подключения к БД 
```

3. Запустите окружение:

* Запустите docker-compose, развёртывание контейнеров выполниться в «фоновом режиме»
```
docker-compose up
```

* выполните миграции:
```
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

*  соберите статику:
```
docker-compose exec backend python manage.py collectstatic --no-input
```

* cоздайте суперпользователя, введите - почту, логин, пароль:
```
docker-compose exec backend python manage.py createsuperuser
```

### Проект готов к работе


Проект выполнил студент 84 когорты Яндекс Практикума
Буйный Александр
https://github.com/By9n
https://t.me/by9n4ik
