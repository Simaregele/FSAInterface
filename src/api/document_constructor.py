from typing import Dict, List, Any, Optional
import requests
import streamlit as st
from config.config import Config
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

config = Config.get_instance()

class DocumentConstructor:
    def __init__(self):
        self.base_url = config.get('CERTIFICATE_API_URL')
        self.headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        self.request_history_key = "doc_constructor_request_history"
        self.downloaded_docs_key = "downloaded_documents_cache"
        self.max_history_size = 100
        logger.info("DocumentConstructor initialized with base_url: %s", self.base_url)

    def _add_to_request_history(self, doc_id: str, request_type: str, status: str):
        """Добавление записи в историю запросов"""
        if self.request_history_key not in st.session_state:
            st.session_state[self.request_history_key] = []
        
        history = st.session_state[self.request_history_key]
        history.append({
            'doc_id': doc_id,
            'request_type': request_type,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
        # Логирование события
        logger.info(
            "Request history updated - Doc ID: %s, Type: %s, Status: %s",
            doc_id, request_type, status
        )
        
        # Ограничение размера истории
        if len(history) > self.max_history_size:
            history.pop(0)
            logger.debug("Request history trimmed to max size: %d", self.max_history_size)

    def get_request_status(self, doc_id: str) -> Dict[str, str]:
        """Получение статуса запросов для документа"""
        if self.request_history_key not in st.session_state:
            return {}
        
        history = st.session_state[self.request_history_key]
        status = {}
        for record in reversed(history):
            if record['doc_id'] == doc_id:
                status[record['request_type']] = record['status']
        return status

    def generate_documents(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Генерация документов через API конструктора"""
        doc_id = str(data.get('ID', 'unknown'))
        try:
            logger.info("Starting document generation for Doc ID: %s", doc_id)
            logger.debug("Generation request data: %s", data)
            
            self._add_to_request_history(doc_id, 'generate', 'processing')
            
            url = f"{self.base_url}/generate_documents"
            logger.info("Sending POST request to: %s", url)
            
            response = requests.post(
                url,
                json={"data": data},
                headers=self.headers
            )
            response.raise_for_status()
            
            documents_list = response.json()
            logger.info("Documents generated successfully for Doc ID: %s", doc_id)
            logger.debug("Generated documents: %s", documents_list)
            
            result = {
                'documents': documents_list,
                'merged_data': data
            }
            
            self._add_to_request_history(doc_id, 'generate', 'success')
            return result
            
        except requests.RequestException as e:
            logger.error(
                "Error generating documents for Doc ID: %s - %s", 
                doc_id, str(e)
            )
            if hasattr(e, 'response') and e.response is not None:
                logger.error(
                    "API Response - Status: %s, Content: %s",
                    e.response.status_code, e.response.text
                )
            
            self._add_to_request_history(doc_id, 'generate', 'error')
            st.error(f"Ошибка при генерации документов: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                st.error(f"Статус код: {e.response.status_code}")
                st.error(f"Ответ сервера: {e.response.text}")
            return None

    def _get_cache_key(self, doc_id: str, url: str) -> str:
        """Создание уникального ключа для кэширования"""
        return f"{doc_id}_{url}"

    def download_document(self, url: str, doc_id: str) -> Optional[bytes]:
        """Скачивание сгенерированного документа с кэшированием"""
        cache_key = self._get_cache_key(doc_id, url)
        
        # Проверяем наличие документа в кэше
        if self.downloaded_docs_key in st.session_state:
            cached_doc = st.session_state[self.downloaded_docs_key].get(cache_key)
            if cached_doc is not None:
                logger.info("Document found in cache for Doc ID: %s", doc_id)
                return cached_doc

        try:
            logger.info("Document not in cache, downloading for Doc ID: %s", doc_id)
            self._add_to_request_history(doc_id, 'download', 'processing')
            
            download_url = f"{self.base_url}{url}"
            logger.info("Sending GET request to: %s", download_url)
            
            response = requests.get(download_url)
            response.raise_for_status()
            
            # Сохраняем в кэш
            if self.downloaded_docs_key not in st.session_state:
                st.session_state[self.downloaded_docs_key] = {}
            
            st.session_state[self.downloaded_docs_key][cache_key] = response.content
            
            logger.info("Document downloaded and cached for Doc ID: %s", doc_id)
            logger.debug("Response size: %d bytes", len(response.content))
            
            self._add_to_request_history(doc_id, 'download', 'success')
            return response.content
            
        except requests.RequestException as e:
            logger.error(
                "Error downloading document for Doc ID: %s - %s",
                doc_id, str(e)
            )
            if hasattr(e, 'response') and e.response is not None:
                logger.error(
                    "API Response - Status: %s, Content: %s",
                    e.response.status_code, e.response.text
                )
            
            self._add_to_request_history(doc_id, 'download', 'error')
            st.error(f"Ошибка при скачивании документа: {str(e)}")
            return None

    @staticmethod
    def get_mime_type(format: str) -> str:
        """Получение MIME-типа для формата файла"""
        mime_types = {
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'pdf': 'application/pdf'
        }
        return mime_types.get(format, 'application/octet-stream') 