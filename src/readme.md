# TODO: проверить все туду и двойные кавычки (лучше май-пай настроить)
# TODO: обновить req.txt

### Немного о коде проекта
1. сделано в ActiveRecord подходе: каждая энтити/модель связана с своей таблицей и способа делать CRUD-вызовы (User.save(), User.get() и т.п.).

### Осознанные упрощения:
1. В тестах нет моков констант, хотя код самой бизнес логики рассчитан на их изменение;
2. В коде 4х стратегий и входящих/исходящих событий встречается копипаст кода. Имхо, в рамках тестового задания, чтобы было легко проверить и ревьюер не махнул руков на всю эту "микро-оптимизацию" лучше умеренный копипаст код, нежели крошечные методы/классы в несколько строк;
3. Весь код синхронный, т.к. нет работы с сетью или диском (вместо БД - dict);
4. Очень хотелось настроить mypy, но руки не дошли, поэтому могут быть какие-то нестыковки в типизации или импортах, НО на логику это не должно повлиять;
5. В тестах на бизнес-логику стратегий активно используется вызов крон-скрипта. Хотя это некоторая денормализация, так существенно проще.
6. В create-ручке явно вызывается крон-скрипт, чтобы не ждать 1 минуту, когда он правда отработает.

# Как запустить
1. Установить зависимости: `pip install -r req.txt`
2. Запустить сервер: `uvicorn src.main:app --reload`
3. curl для добавления ивента `signup_completed`:
```bash
curl -X POST "http://localhost:8000/api/external/event_in/create"   -H "Content-Type: application/json"   -d '{
        "user_id": "u_12345",
        "event_type": "signup_completed",
        "event_timestamp": "2025-10-31T19:22:11Z",
        "user_traits": {
            "email": "maria@example.com",
            "country": "PT",
            "marketing_opt_in": true,
            "risk_segment": "MEDIUM"
        }
      }'
```
4. curl для проверки, что был создан входящий и исходящий ивент:
```bash
curl -X GET "http://localhost:8000/api/admin/user/audit/u_12345"      -H "Accept: application/json"
```
5. curl для добавления ивента `payment_failed` (можно отправить 2ой раз, чтобы убедиться, что идемпотентность работает):
```bash
curl -X POST "http://localhost:8000/api/external/event_in/create"   -H "Content-Type: application/json"   -d '{
        "user_id": "u_12345",
        "event_type": "payment_failed",
        "event_timestamp": "2025-10-31T19:24:11Z",
        "properties": {
            "amount": 1425.00,
            "attempt_number": 2,
            "failure_reason": "INSUFFICIENT_FUNDS"
        },
        "user_traits": {
            "email": "maria@example.com",
            "country": "PT",
            "marketing_opt_in": true,
            "risk_segment": "MEDIUM"
        }
      }'
```
#  Есть тесты, рекомендую посмотреть!