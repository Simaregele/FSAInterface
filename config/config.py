import json
import os


def load_config():
    # Получаем абсолютный путь к директории, где находится текущий файл (config.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Перемещаемся на уровень выше, чтобы достичь корневой директории проекта
    project_root = os.path.dirname(current_dir)
    # Формируем путь к файлу config.json
    config_path = os.path.join(project_root, 'config.json')

    try:
        with open(config_path) as config_file:
            config = json.load(config_file)

        # Проверяем наличие необходимых полей
        required_fields = ['api_base_url', 'auth_url', 'search_endpoint', 'document_endpoints', 'sync_endpoints']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"{field} отсутствует в файле config.json")

        # Проверяем наличие подполей в document_endpoints и sync_endpoints
        for endpoint_type in ['document_endpoints', 'sync_endpoints']:
            if 'declaration' not in config[endpoint_type] or 'certificate' not in config[endpoint_type]:
                raise ValueError(f"В {endpoint_type} отсутствуют поля 'declaration' или 'certificate'")

        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл конфигурации не найден по пути: {config_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Ошибка при разборе JSON в файле: {config_path}")
