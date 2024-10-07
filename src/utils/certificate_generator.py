import requests
import json
from typing import Dict, Any
import sys
import io


# URL для локального API генерации сертификатов
# CERTIFICATE_API_URL = "http://localhost:8000/generate_certificate"
CERTIFICATE_API_URL = "http://91.92.136.247:8001/generate_certificate"

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def utf8_encode_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Рекурсивно кодирует все строковые значения в словаре в UTF-8."""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = value.encode('utf-8').decode('utf-8')
        elif isinstance(value, dict):
            result[key] = utf8_encode_dict(value)
        elif isinstance(value, list):
            result[key] = [
                utf8_encode_dict(item) if isinstance(item, dict)
                else item.encode('utf-8').decode('utf-8') if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def get_nested_value(data: Dict[str, Any], path: str, default: Any = '') -> Any:
    keys = path.split('.')
    value = data
    for key in keys:
        if key.endswith(']'):
            key, index = key[:-1].split('[')
            try:
                value = value.get(key, [])[int(index)]
            except (IndexError, TypeError):
                return default
        else:
            value = value.get(key, {})
        if value == {}:
            return default
    return value if value != {} else default


def filter_contacts(contacts: list, id_type: int) -> str:
    filtered = [c['value'] for c in contacts if c.get('idContactType') == id_type]
    return filtered[0] if filtered else ''


def stringify_values(obj):
    if isinstance(obj, dict):
        return {k: stringify_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [stringify_values(i) for i in obj]
    elif obj is None:
        return ''
    else:
        return str(obj)


def process_complex_json(data: Dict[str, Any]) -> Dict[str, str]:
    print("Входные данные:", json.dumps(data, ensure_ascii=False, indent=2))
    data = stringify_values(data)
    result = {}
    result['certificate_number'] = get_nested_value(data, 'RegistryData.number')
    result['batch_number'] = get_nested_value(data, 'RegistryData.blankNumber')

    # Certification body
    cert_auth = get_nested_value(data, 'RegistryData.certificationAuthority', {})
    if isinstance(cert_auth, dict):
        result['certification_body'] = (
            f"Название: {cert_auth.get('fullName', '')}\n"
            f"Адрес: {get_nested_value(cert_auth, 'addresses[0].fullAddress')}\n"
            f"Телефон: {filter_contacts(cert_auth.get('contacts', []), '1')}\n"
            f"Email: {filter_contacts(cert_auth.get('contacts', []), '4')}\n"
            f"Аттестат аккредитации: {cert_auth.get('attestatRegNumber', '')}\n"
            f"Дата регистрации: {cert_auth.get('attestatRegDate', '')}"
        )
    else:
        result['certification_body'] = str(cert_auth)

    # Applicant
    applicant = get_nested_value(data, 'RegistryData.applicant', {})
    if isinstance(applicant, dict):
        result['applicant'] = (
            f"Название: {applicant.get('fullName', '')}\n"
            f"Адрес: {get_nested_value(applicant, 'addresses[0].fullAddress')}\n"
            f"ОГРН: {applicant.get('ogrn', '')}\n"
            f"Телефон: {filter_contacts(applicant.get('contacts', []), '1')}\n"
            f"Email: {filter_contacts(applicant.get('contacts', []), '4')}"
        )
    else:
        result['applicant'] = str(applicant)

    # Manufacturer
    manufacturer = get_nested_value(data, 'RegistryData.manufacturer', {})
    if isinstance(manufacturer, dict):
        result['manufacturer'] = (
            f"Название: {manufacturer.get('fullName', '')}\n"
            f"Адрес: {get_nested_value(manufacturer, 'addresses[0].fullAddress')}"
        )
    else:
        result['manufacturer'] = str(manufacturer)

    result['product_description'] = get_nested_value(data, 'RegistryData.product.fullName')
    tn_ved_codes = get_nested_value(data, 'RegistryData.product.identifications[0].idTnveds')
    result['tn_ved_codes'] = ', '.join(tn_ved_codes) if isinstance(tn_ved_codes, list) else str(tn_ved_codes)
    result['technical_regulation'] = ', '.join(get_nested_value(data, 'RegistryData.idTechnicalReglaments', []))

    # Test reports
    test_reports = get_nested_value(data, 'RegistryData.documents.applicantOtherDocuments', [])
    if isinstance(test_reports, list):
        result['test_reports'] = '\n'.join([f"{report.get('number', '')}: {report.get('name', '')}" for report in test_reports])
    else:
        result['test_reports'] = str(test_reports)

    # Standards and conditions
    result['standards_and_conditions'] = get_nested_value(data, 'RegistryData.product.storageCondition')

    result['issue_date'] = get_nested_value(data, 'RegistryData.certRegDate')
    result['expiry_date'] = get_nested_value(data, 'RegistryData.certEndDate')

    # Expert name
    expert = get_nested_value(data, 'RegistryData.experts[0]', {})
    if isinstance(expert, dict):
        result['expert_name'] = f"{expert.get('surname', '')} {expert.get('firstName', '')} {expert.get('patronimyc', '')}"
    else:
        result['expert_name'] = str(expert)

    # Head of certification body
    head = get_nested_value(data, 'RegistryData', {})
    if isinstance(head, dict):
        result['head_of_certification_body'] = f"{head.get('surname', '')} {head.get('firstName', '')} {head.get('patronymic', '')}"
    else:
        result['head_of_certification_body'] = str(head)

    return result


def generate_certificate(data: Dict[str, Any]) -> bytes:
    try:
        # Обрабатываем данные перед отправкой
        # processed_data = process_complex_json(data)

        # Преобразуем все строковые значения в UTF-8
        utf8_data = utf8_encode_dict(data)

        # Оборачиваем обработанные данные в словарь с ключом 'data'
        payload = {"data": utf8_data}

        # Преобразуем payload в JSON
        payload_json = json.dumps(payload, ensure_ascii=False, indent=2)

        # Выводим отправляемые данные для отладки
        print("Отправляемые данные:", payload_json)

        # Отправляем запрос
        response = requests.post(
            CERTIFICATE_API_URL,
            json=payload,  # requests автоматически сериализует dict в JSON
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        response.raise_for_status()

        # Добавим вывод ответа сервера для отладки
        print("Ответ сервера:", response.text)

        return response.content
    except requests.RequestException as e:
        print(f"Ошибка при генерации сертификата: {str(e)}")
        # Добавим вывод полной информации об ошибке
        print(f"Полная информация об ошибке: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Статус код: {e.response.status_code}")
            print(f"Содержимое ответа: {e.response.text}")
        return None
