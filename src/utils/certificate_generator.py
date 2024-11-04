import requests
import json
from typing import Dict, Any, Union, Optional
import sys
import io
import logging
from config.config import load_config


config = load_config()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
    logging.info("Входные данные: %s", json.dumps(data, ensure_ascii=False, indent=2))
    data = stringify_values(data)
    result = {}
    result.update(process_registry_data(data))
    result.update(process_certification_body(data))
    result.update(process_applicant(data))
    result.update(process_manufacturer(data))
    result.update(process_product_info(data))
    result.update(process_test_reports(data))
    result.update(process_dates_and_personnel(data))
    return result


def process_registry_data(data: Dict[str, Any]) -> Dict[str, str]:
    return {
        'certificate_number': get_nested_value(data, 'RegistryData.number'),
        'batch_number': get_nested_value(data, 'RegistryData.blankNumber'),
    }


def process_certification_body(data: Dict[str, Any]) -> Dict[str, str]:
    cert_auth = get_nested_value(data, 'RegistryData.certificationAuthority', {})
    if isinstance(cert_auth, dict):
        return {
            'certification_body': (
                f"Название: {cert_auth.get('fullName', '')}\n"
                f"Адрес: {get_nested_value(cert_auth, 'addresses[0].fullAddress')}\n"
                f"Телефон: {filter_contacts(cert_auth.get('contacts', []), '1')}\n"
                f"Email: {filter_contacts(cert_auth.get('contacts', []), '4')}\n"
                f"Аттестат аккредитации: {cert_auth.get('attestatRegNumber', '')}\n"
                f"Дата регистрации: {cert_auth.get('attestatRegDate', '')}"
            )
        }
    return {'certification_body': str(cert_auth)}


def process_applicant(data: Dict[str, Any]) -> Dict[str, str]:
    applicant = get_nested_value(data, 'RegistryData.applicant', {})
    if isinstance(applicant, dict):
        return {
            'applicant': (
                f"Название: {applicant.get('fullName', '')}\n"
                f"Адрес: {get_nested_value(applicant, 'addresses[0].fullAddress')}\n"
                f"ОГРН: {applicant.get('ogrn', '')}\n"
                f"Телефон: {filter_contacts(applicant.get('contacts', []), '1')}\n"
                f"Email: {filter_contacts(applicant.get('contacts', []), '4')}"
            )
        }
    return {'applicant': str(applicant)}


def process_manufacturer(data: Dict[str, Any]) -> Dict[str, str]:
    manufacturer = get_nested_value(data, 'RegistryData.manufacturer', {})
    if isinstance(manufacturer, dict):
        return {
            'manufacturer': (
                f"Название: {manufacturer.get('fullName', '')}\n"
                f"Адрес: {get_nested_value(manufacturer, 'addresses[0].fullAddress')}"
            )
        }
    return {'manufacturer': str(manufacturer)}


def process_product_info(data: Dict[str, Any]) -> Dict[str, str]:
    tn_ved_codes = get_nested_value(data, 'RegistryData.product.identifications[0].idTnveds')
    return {
        'product_description': get_nested_value(data, 'RegistryData.product.fullName'),
        'tn_ved_codes': ', '.join(tn_ved_codes) if isinstance(tn_ved_codes, list) else str(tn_ved_codes),
        'technical_regulation': ', '.join(get_nested_value(data, 'RegistryData.idTechnicalReglaments', [])),
        'standards_and_conditions': get_nested_value(data, 'RegistryData.product.storageCondition'),
    }


def process_test_reports(data: Dict[str, Any]) -> Dict[str, str]:
    test_reports = get_nested_value(data, 'RegistryData.documents.applicantOtherDocuments', [])
    if isinstance(test_reports, list):
        return {
            'test_reports': '\n'.join(
                [f"{report.get('number', '')}: {report.get('name', '')}" for report in test_reports])
        }
    return {'test_reports': str(test_reports)}


def process_dates_and_personnel(data: Dict[str, Any]) -> Dict[str, str]:
    result = {
        'issue_date': get_nested_value(data, 'RegistryData.certRegDate'),
        'expiry_date': get_nested_value(data, 'RegistryData.certEndDate'),
    }

    expert = get_nested_value(data, 'RegistryData.experts[0]', {})
    if isinstance(expert, dict):
        result[
            'expert_name'] = f"{expert.get('surname', '')} {expert.get('firstName', '')} {expert.get('patronimyc', '')}"
    else:
        result['expert_name'] = str(expert)

    head = get_nested_value(data, 'RegistryData', {})
    if isinstance(head, dict):
        result[
            'head_of_certification_body'] = f"{head.get('surname', '')} {head.get('firstName', '')} {head.get('patronymic', '')}"
    else:
        result['head_of_certification_body'] = str(head)

    return result


def generate_documents(details: Dict[str, Any], search_data: Optional[Dict[str, Any]] = None) -> Dict[
    str, Union[bytes, str]]:
    """
    Генерирует документы с учетом данных как из деталей документа, так и из результатов поиска

    Args:
        details: детальная информация о документе
        search_data: дополнительные данные из результатов поиска FSA
    """
    try:
        # Эндпоинт для генерации документов
        GENERATE_DOCUMENTS_ENDPOINT = "/generate_documents"

        # Создаем копию деталей для объединения данных
        merged_data = details.copy()

        # Если есть данные из поиска, добавляем их с префиксом 'search_'
        if search_data:
            for key, value in search_data.items():
                if key not in merged_data:
                    # Добавляем оригинальные данные с префиксом
                    merged_data[f'search_{key}'] = value
                    # Отдельно сохраняем TNVED коды
                    if key == 'TNVED':
                        merged_data['tnved_codes'] = value

        # Преобразуем все строковые значения в UTF-8
        utf8_data = utf8_encode_dict(merged_data)
        payload = {"data": utf8_data}

        # Логируем отправляемые данные
        payload_json = json.dumps(payload, ensure_ascii=False, indent=2)
        logging.info("Отправляемые данные: %s", payload_json)

        # Формируем полный URL для запроса генерации документов
        generate_url = f"{config['LOCAL_CERTIFICATE_API_URL']}{GENERATE_DOCUMENTS_ENDPOINT}"

        # Отправляем запрос на генерацию документов
        response = requests.post(
            generate_url,
            json=payload,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        response.raise_for_status()
        logging.info("Ответ сервера: %s", response.text)

        # Разбираем JSON-ответ
        response_data = response.json()

        # Получаем URL'ы документов из ответа
        certificate_url = response_data['certificate_url']
        attorney_url = response_data['attorney_url']

        # Формируем полные URL'ы для скачивания документов
        certificate_full_url = f"{config['LOCAL_CERTIFICATE_API_URL']}{certificate_url}"
        attorney_full_url = f"{config['LOCAL_CERTIFICATE_API_URL']}{attorney_url}"

        # Скачиваем сертификат
        certificate_response = requests.get(certificate_full_url)
        certificate_response.raise_for_status()

        # Скачиваем доверенность
        attorney_response = requests.get(attorney_full_url)
        attorney_response.raise_for_status()

        result = {
            'certificate_content': certificate_response.content,
            'certificate_filename': certificate_url.split('/')[-1],
            'attorney_content': attorney_response.content,
            'attorney_filename': attorney_url.split('/')[-1],
            'merged_data': merged_data  # Сохраняем объединенные данные для reference
        }

        # Логируем успешную генерацию
        logging.info("Документы успешно сгенерированы для данных: %s",
                     merged_data.get('ID', '') or merged_data.get('search_ID', 'Unknown ID'))

        return result

    except requests.RequestException as e:
        logging.error("Ошибка при генерации сертификата и доверенности: %s", str(e))
        logging.error("Полная информация об ошибке: %s", str(e))
        if hasattr(e, 'response') and e.response is not None:
            logging.error("Статус код: %s", e.response.status_code)
            logging.error("Содержимое ответа: %s", e.response.text)
        return {}
