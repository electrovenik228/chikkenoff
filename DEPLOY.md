# Деплой на сервер 147.45.185.185:6767

Production compose публикует сайт на `http://147.45.185.185:6767/`.

Если `6767` одновременно используется как SSH-порт, Docker не сможет занять этот порт для сайта. В таком случае поменяй внешний порт в `docker-compose.prod.yml`, например на `8080:80`.

## 1. Подключиться к серверу

```bash
ssh root@147.45.185.185
```

Если SSH у тебя действительно на порту `6767`, подключайся так:

```bash
ssh -p 6767 root@147.45.185.185
```

Если пользователь не `root`, замени `root` на своего пользователя.

## 2. Установить Docker

```bash
sudo apt update
sudo apt install -y ca-certificates curl git docker.io docker-compose-plugin
sudo systemctl enable --now docker
```

Если работаешь не под `root`, добавь пользователя в группу Docker:

```bash
sudo usermod -aG docker $USER
```

После этого нужно выйти из SSH и зайти снова.

## 3. Загрузить проект

Вариант через Git:

```bash
git clone <repo-url> /opt/chikkenoff
cd /opt/chikkenoff
```

Если хочешь именно пушить на сервер как в Git remote, на сервере нужно заранее создать bare-репозиторий и deploy hook. Для первого деплоя проще использовать `git clone`, а потом обновлять через `git pull`.

## 4. Создать production env

```bash
cp backend/.env.production.example backend/.env
nano backend/.env
```

Обязательно замени:

- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`

Для запуска по IP оставь:

```env
DJANGO_ALLOWED_HOSTS=147.45.185.185,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://147.45.185.185:6767
CSRF_TRUSTED_ORIGINS=http://147.45.185.185:6767
```

## 5. Запустить production compose

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Создать администратора:

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

## 6. Проверить

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

Открыть:

- `http://147.45.185.185:6767/`
- `http://147.45.185.185:6767/api/`
- `http://147.45.185.185:6767/admin/`

## 7. Настроить доступ сотрудников по филиалам

В админке создай филиалы, пользователей и `EmployeeProfile` для каждого пользователя.

- `owner`, `director` и `superuser` видят всю сеть.
- `manager`, `shift_lead`, `cashier`, `cook`, `courier` видят только свой `primary_branch`.
- Пользователь без активного `EmployeeProfile.primary_branch` будет получать пустые списки в API.

## 8. Обновление после изменений

```bash
cd /opt/chikkenoff
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Когда появится домен

После привязки домена нужно заменить IP в `backend/.env`:

```env
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
CORS_ALLOWED_ORIGINS=https://example.com
CSRF_TRUSTED_ORIGINS=https://example.com
```

Потом можно поставить Nginx/Certbot на хосте или добавить SSL-терминацию отдельным контейнером.
