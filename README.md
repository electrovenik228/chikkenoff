# Chikkenoff Cloud POS

Стартовый monorepo для облачной системы управления сетью ресторанов быстрого питания.

## Что входит

- `backend/` - Django + Django REST Framework API.
- `frontend/` - React + TypeScript + Material UI интерфейс для POS, KDS и управления.
- `docker-compose.yml` - PostgreSQL, Redis, backend, Celery и frontend.
- `.github/workflows/ci.yml` - базовая проверка backend и frontend.

## Реализованный MVP-срез

- POS: категории, поиск, избранное, быстрые кнопки, корзина, модификаторы, методы оплаты, печать.
- KDS: активные заказы, таймеры, цветовые статусы задержки.
- CRM: карточки клиентов, сегменты, история в агрегированном виде.
- Филиалы: сравнение выручки, прибыли, среднего чека и заказов.
- Персонал: роли, профили сотрудников, смены, закрытие смены.
- Склад: ингредиенты, рецептуры, остатки, движения и низкие остатки.
- Финансы и аналитика: платежи, dashboard, топ товаров, загрузка филиалов.
- Безопасность: основа RBAC через роли, admin, audit log.
- AI-модуль: место в UI и API-архитектуре под аналитические выводы и прогнозы.

## Запуск через Docker

```bash
docker compose up --build
```

После запуска:

- Backend API: `http://localhost:8000/api/`
- Django Admin: `http://localhost:8000/admin/`
- Frontend: `http://localhost:5173/`

## Production на VPS

Для сервера `147.45.185.185` с SSH-портом `6767` смотри [DEPLOY.md](/home/aman/chikkenoff/DEPLOY.md).

Короткий запуск на сервере:

```bash
cp backend/.env.production.example backend/.env
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

Для первого пользователя:

```bash
docker compose exec backend python manage.py createsuperuser
```

## Локальный запуск backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Локальный запуск frontend

```bash
cd frontend
npm install
npm run dev
```

## Основные API

- `GET /api/products/` - меню, поиск и фильтры.
- `POST /api/orders/` - создание заказа с позициями и модификаторами.
- `POST /api/orders/{id}/pay/` - добавление оплаты.
- `POST /api/orders/{id}/transition/` - смена статуса заказа.
- `GET /api/orders/kds/` - активные заказы для кухни.
- `GET /api/dashboard/` - управленческие метрики.
- `GET /api/stock-balances/?low=1` - низкие остатки.

## Следующие инженерные шаги

1. Добавить миграции и seed-команду с тестовым меню.
2. Подключить JWT/2FA и детальные permissions для каждой роли.
3. Добавить списание ингредиентов транзакцией при оплате или выдаче заказа.
4. Подключить WebSocket/SSE для KDS и dashboard real-time обновлений.
5. Вынести AI-аналитику в отдельный сервис с доступом к агрегированным витринам данных.
