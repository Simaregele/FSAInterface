import json


def load_config():
    with open('config.json') as config_file:
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