import json

import requests


BASE_URL = "http://127.0.0.1:5000"


def ask_format() -> str:
    """Запрашивает желаемый формат ответа и возвращает json или wsdl."""
    raw = input("Формат ответа (json/wsdl) [json]: ").strip().lower()
    return raw if raw in {"json", "wsdl"} else "json"


def print_response(resp: requests.Response) -> None:
    """Печатает HTTP-статус и тело ответа в JSON или сыром виде."""
    print(f"\nHTTP {resp.status_code}")
    try:
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except ValueError:
        print(resp.text)


def input_payload() -> dict:
    """Собирает поля объекта из консоли и возвращает payload для POST/PUT."""
    print("Оставьте поле пустым, если не хотите его передавать")
    payload = {}

    lat = input("lat: ").strip()
    if lat:
        payload["lat"] = float(lat)

    lng = input("lng: ").strip()
    if lng:
        payload["lng"] = float(lng)

    title = input("title: ").strip()
    if title:
        payload["title"] = title

    timestamp = input("timeStamp (YYYY-MM-DD HH:MM:SS): ").strip()
    if timestamp:
        payload["timeStamp"] = timestamp

    town = input("town: ").strip()
    if town:
        payload["town"] = town

    hour = input("hour (0-23): ").strip()
    if hour:
        payload["hour"] = int(hour)

    return payload


def list_calls() -> None:
    """Запрашивает и выводит пагинированный список объектов calls."""
    page = input("page [1]: ").strip() or "1"
    per_page = input("per_page [20]: ").strip() or "20"
    fmt = ask_format()

    resp = requests.get(
        f"{BASE_URL}/api/calls",
        params={"page": page, "per_page": per_page, "format": fmt},
        timeout=30,
    )
    print_response(resp)


def get_call() -> None:
    """Запрашивает и выводит один объект calls по ID."""
    call_id = input("ID объекта: ").strip()
    fmt = ask_format()
    resp = requests.get(
        f"{BASE_URL}/api/calls/{call_id}", params={"format": fmt}, timeout=30
    )
    print_response(resp)


def create_call() -> None:
    """Создает новый объект calls из введенных пользователем данных."""
    payload = input_payload()
    fmt = ask_format()
    resp = requests.post(
        f"{BASE_URL}/api/calls", params={"format": fmt}, json=payload, timeout=30
    )
    print_response(resp)


def update_call() -> None:
    """Обновляет существующий объект calls по ID введенными полями."""
    call_id = input("ID объекта: ").strip()
    payload = input_payload()
    fmt = ask_format()
    resp = requests.put(
        f"{BASE_URL}/api/calls/{call_id}",
        params={"format": fmt},
        json=payload,
        timeout=30,
    )
    print_response(resp)


def delete_call() -> None:
    """Удаляет объект calls по ID и выводит результат операции."""
    call_id = input("ID объекта: ").strip()
    fmt = ask_format()
    resp = requests.delete(
        f"{BASE_URL}/api/calls/{call_id}", params={"format": fmt}, timeout=30
    )
    print_response(resp)


def stats_by_hour() -> None:
    """Запрашивает статистику количества обращений по выбранному часу."""
    hour = input("Час (0-23): ").strip()
    fmt = ask_format()
    resp = requests.get(
        f"{BASE_URL}/api/stats/hour/{hour}", params={"format": fmt}, timeout=30
    )
    print_response(resp)


def show_wsdl() -> None:
    """Получает и выводит WSDL-описание API."""
    resp = requests.get(f"{BASE_URL}/api/wsdl", timeout=30)
    print_response(resp)


def menu() -> None:
    """Запускает интерактивное меню CLI и обрабатывает выбор пользователя."""
    actions = {
        "1": ("Список объектов", list_calls),
        "2": ("Один объект по ID", get_call),
        "3": ("Добавить объект", create_call),
        "4": ("Изменить объект", update_call),
        "5": ("Удалить объект", delete_call),
        "6": ("Общее число обращений в час", stats_by_hour),
        "7": ("Показать WSDL", show_wsdl),
        "0": ("Выход", None),
    }

    while True:
        print("\n=== CLI для API LR3 ===")
        for key, (name, _) in actions.items():
            print(f"{key}. {name}")

        choice = input("Выберите метод: ").strip()
        action = actions.get(choice)

        if not action:
            print("Неизвестный пункт меню")
            continue

        if choice == "0":
            print("Завершение работы")
            break

        try:
            action[1]()
        except requests.RequestException as exc:
            print(f"Ошибка запроса: {exc}")
        except ValueError as exc:
            print(f"Ошибка ввода: {exc}")


if __name__ == "__main__":
    menu()
