import sqlite3
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from flask import Flask, Response, jsonify, request

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "calls.db"

app = Flask(__name__)


ALLOWED_FIELDS = ("lat", "lng", "title", "timeStamp", "town", "hour")


def parse_positive_int(raw_value: str, field_name: str) -> tuple[int | None, str | None]:
    """Преобразует строку в положительное целое число или возвращает текст ошибки."""
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None, f"{field_name} должен быть целым числом"

    if value <= 0:
        return None, f"{field_name} должен быть положительным целым числом"

    return value, None


def get_db_connection() -> sqlite3.Connection:
    """Создает и возвращает подключение к SQLite с доступом к колонкам по имени."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def wants_wsdl() -> bool:
    """Проверяет, запросил ли клиент XML/WSDL-формат через query-параметр format."""
    return request.args.get("format", "json").lower() == "wsdl"


def dict_to_xml(payload: dict) -> bytes:
    """Преобразует словарь (включая вложенные dict/list) в XML-документ."""
    root = Element("response")

    for key, value in payload.items():
        if isinstance(value, dict):
            obj_node = SubElement(root, str(key))
            for child_key, child_value in value.items():
                child = SubElement(obj_node, str(child_key))
                child.text = "" if child_value is None else str(child_value)
            continue

        if isinstance(value, list):
            list_node = SubElement(root, str(key))
            for item in value:
                item_node = SubElement(list_node, "item")
                if isinstance(item, dict):
                    for item_key, item_value in item.items():
                        child = SubElement(item_node, str(item_key))
                        child.text = "" if item_value is None else str(item_value)
                else:
                    item_node.text = "" if item is None else str(item)
            continue

        node = SubElement(root, str(key))
        node.text = "" if value is None else str(value)

    return tostring(root, encoding="utf-8", xml_declaration=True)


def format_response(payload: dict, status: int = 200) -> Response:
    """Формирует ответ API: XML при format=wsdl, иначе JSON."""
    if wants_wsdl():
        xml_payload = dict_to_xml(payload)
        return Response(xml_payload, status=status, mimetype="application/wsdl+xml")
    resp = jsonify(payload)
    resp.status_code = status
    return resp


def fetch_call_by_id(conn: sqlite3.Connection, call_id: int):
    """Возвращает запись calls по rowid или None, если запись не найдена."""
    query = """
		SELECT rowid AS id, lat, lng, title, timeStamp, town, hour
		FROM calls
		WHERE rowid = ?
	"""
    return conn.execute(query, (call_id,)).fetchone()


def parse_payload() -> tuple[dict, str | None]:
    """Читает JSON-тело запроса, валидирует и оставляет только разрешенные поля."""
    if not request.is_json:
        return {}, "Body должен быть в формате JSON"

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {}, "Некорректный JSON-объект"

    filtered = {k: payload[k] for k in ALLOWED_FIELDS if k in payload}
    if not filtered:
        return {}, "Не переданы поля для записи"

    return filtered, None


@app.get("/api/calls")
def list_calls() -> Response:
    """Возвращает пагинированный список объектов calls."""
    page = max(request.args.get("page", default=1, type=int), 1)
    per_page = min(max(request.args.get("per_page", default=20, type=int), 1), 100)
    offset = (page - 1) * per_page

    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) AS total FROM calls").fetchone()["total"]
    rows = conn.execute(
        """
		SELECT rowid AS id, lat, lng, title, timeStamp, town, hour
		FROM calls
		ORDER BY rowid
		LIMIT ? OFFSET ?
		""",
        (per_page, offset),
    ).fetchall()
    conn.close()

    payload = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": [dict(row) for row in rows],
    }
    return format_response(payload)


@app.get("/api/calls/<int:call_id>")
def get_call(call_id: int) -> Response:
    """Возвращает один объект calls по его идентификатору."""
    if call_id <= 0:
        return format_response({"error": "id должен быть положительным целым числом"}, status=400)

    conn = get_db_connection()
    row = fetch_call_by_id(conn, call_id)
    conn.close()

    if row is None:
        return format_response({"error": "Объект не найден"}, status=404)

    return format_response({"item": dict(row)})


@app.post("/api/calls")
def create_call() -> Response:
    """Создает новый объект calls из данных JSON-тела запроса."""
    payload, error = parse_payload()
    if error:
        return format_response({"error": error}, status=400)

    columns = ", ".join(payload.keys())
    placeholders = ", ".join(["?"] * len(payload))

    conn = get_db_connection()
    cur = conn.execute(
        f"INSERT INTO calls ({columns}) VALUES ({placeholders})",
        tuple(payload.values()),
    )
    conn.commit()
    created_id = cur.lastrowid
    if created_id is None:
        conn.close()
        return format_response({"error": "Не удалось создать объект"}, status=500)

    created_row = fetch_call_by_id(conn, int(created_id))
    conn.close()
    if created_row is None:
        return format_response(
            {"error": "Не удалось получить созданный объект"}, status=500
        )

    return format_response({"item": dict(created_row)}, status=201)


@app.put("/api/calls/<int:call_id>")
def update_call(call_id: int) -> Response:
    """Обновляет существующий объект calls по id частичным набором полей."""
    if call_id <= 0:
        return format_response({"error": "id должен быть положительным целым числом"}, status=400)

    payload, error = parse_payload()
    if error:
        return format_response({"error": error}, status=400)

    assignments = ", ".join([f"{key} = ?" for key in payload.keys()])
    values = tuple(payload.values()) + (call_id,)

    conn = get_db_connection()
    exists = fetch_call_by_id(conn, call_id)
    if exists is None:
        conn.close()
        return format_response({"error": "Объект не найден"}, status=404)

    conn.execute(f"UPDATE calls SET {assignments} WHERE rowid = ?", values)
    conn.commit()
    updated_row = fetch_call_by_id(conn, call_id)
    conn.close()
    if updated_row is None:
        return format_response(
            {"error": "Не удалось получить обновленный объект"}, status=500
        )

    return format_response({"item": dict(updated_row)})


@app.delete("/api/calls/<int:call_id>")
def delete_call(call_id: int) -> Response:
    """Удаляет объект calls по id и возвращает статус операции."""
    if call_id <= 0:
        return format_response({"error": "id должен быть положительным целым числом"}, status=400)

    conn = get_db_connection()
    exists = fetch_call_by_id(conn, call_id)
    if exists is None:
        conn.close()
        return format_response({"error": "Объект не найден"}, status=404)

    conn.execute("DELETE FROM calls WHERE rowid = ?", (call_id,))
    conn.commit()
    conn.close()

    return format_response({"message": f"Объект {call_id} удален"})


@app.get("/api/stats/hour/<int:hour>")
def stats_by_hour(hour: int) -> Response:
    """Возвращает количество обращений в таблице calls для заданного часа (0-23)."""
    if hour < 0 or hour > 23:
        return format_response({"error": "Час должен быть от 0 до 23"}, status=400)

    conn = get_db_connection()
    total = conn.execute(
        "SELECT COUNT(*) AS total FROM calls WHERE hour = ?", (hour,)
    ).fetchone()["total"]
    conn.close()

    payload = {
        "hour": hour,
        "total_calls": total,
    }
    return format_response(payload)


@app.route("/api/calls/<call_id>", methods=["GET", "PUT", "DELETE"])
def invalid_call_id(call_id: str) -> Response:
    """Возвращает понятную ошибку, если id в URL не является корректным числом."""
    _, error = parse_positive_int(call_id, "id")
    if error:
        return format_response({"error": error}, status=400)
    return format_response({"error": "Некорректный запрос"}, status=400)


@app.get("/api/stats/hour/<hour>")
def invalid_hour(hour: str) -> Response:
    """Возвращает понятную ошибку, если hour в URL задан некорректно."""
    try:
        parsed_hour = int(hour)
    except (TypeError, ValueError):
        return format_response({"error": "Час должен быть целым числом"}, status=400)

    if parsed_hour < 0 or parsed_hour > 23:
        return format_response({"error": "Час должен быть от 0 до 23"}, status=400)

    return format_response({"error": "Некорректный запрос"}, status=400)


@app.get("/api/wsdl")
def wsdl_description() -> Response:
    """Отдает статическое WSDL-описание доступных операций сервиса."""
    wsdl = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<definitions name=\"CallsService\"
                         targetNamespace=\"http://localhost:5000/wsdl/calls\"
                         xmlns:tns=\"http://localhost:5000/wsdl/calls\"
                         xmlns:http=\"http://schemas.xmlsoap.org/wsdl/http/\"
                         xmlns=\"http://schemas.xmlsoap.org/wsdl/\">
    <documentation>
        Краткое описание REST API для calls. По умолчанию ответ JSON,
        при format=wsdl возвращается XML.
    </documentation>

    <portType name=\"CallsPortType\">
        <operation name=\"ListCalls\">
            <documentation>GET /api/calls?page=&amp;per_page=&amp;format=wsdl</documentation>
        </operation>
        <operation name=\"GetCall\">
            <documentation>GET /api/calls/{call_id}?format=wsdl</documentation>
        </operation>
        <operation name=\"CreateCall\">
            <documentation>POST /api/calls?format=wsdl</documentation>
        </operation>
        <operation name=\"UpdateCall\">
            <documentation>PUT /api/calls/{call_id}?format=wsdl</documentation>
        </operation>
        <operation name=\"DeleteCall\">
            <documentation>DELETE /api/calls/{call_id}?format=wsdl</documentation>
        </operation>
        <operation name=\"StatsByHour\">
            <documentation>GET /api/stats/hour/{hour}?format=wsdl</documentation>
        </operation>
    </portType>

    <binding name=\"CallsHttpGetBinding\" type=\"tns:CallsPortType\">
        <http:binding verb=\"GET\" />
        <operation name=\"ListCalls\">
            <http:operation location=\"/api/calls\" />
        </operation>
        <operation name=\"GetCall\">
            <http:operation location=\"/api/calls/{call_id}\" />
        </operation>
        <operation name=\"StatsByHour\">
            <http:operation location=\"/api/stats/hour/{hour}\" />
        </operation>
    </binding>

    <binding name=\"CallsHttpPostBinding\" type=\"tns:CallsPortType\">
        <http:binding verb=\"POST\" />
        <operation name=\"CreateCall\">
            <http:operation location=\"/api/calls\" />
        </operation>
    </binding>

    <binding name=\"CallsHttpPutBinding\" type=\"tns:CallsPortType\">
        <http:binding verb=\"PUT\" />
        <operation name=\"UpdateCall\">
            <http:operation location=\"/api/calls/{call_id}\" />
        </operation>
    </binding>

    <binding name=\"CallsHttpDeleteBinding\" type=\"tns:CallsPortType\">
        <http:binding verb=\"DELETE\" />
        <operation name=\"DeleteCall\">
            <http:operation location=\"/api/calls/{call_id}\" />
        </operation>
    </binding>

    <service name=\"CallsService\">
        <documentation>REST API для сущности calls из LR2.</documentation>
        <port name=\"CallsGetPort\" binding=\"tns:CallsHttpGetBinding\">
            <http:address location=\"http://localhost:5000\" />
        </port>
        <port name=\"CallsPostPort\" binding=\"tns:CallsHttpPostBinding\">
            <http:address location=\"http://localhost:5000\" />
        </port>
        <port name=\"CallsPutPort\" binding=\"tns:CallsHttpPutBinding\">
            <http:address location=\"http://localhost:5000\" />
        </port>
        <port name=\"CallsDeletePort\" binding=\"tns:CallsHttpDeleteBinding\">
            <http:address location=\"http://localhost:5000\" />
        </port>
    </service>
</definitions>
"""
    return Response(wsdl, mimetype="application/wsdl+xml")


if __name__ == "__main__":
    app.run(debug=True)
