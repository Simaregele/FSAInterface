from typing import Dict, List, Any, Optional
import requests
import streamlit as st
from config.config import Config
from datetime import datetime

config = Config.get_instance()

class DocumentConstructor:
    def __init__(self):
        self.base_url = config.get('LOCAL_CERTIFICATE_API_URL')
        self.headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        self.request_history_key = "doc_constructor_request_history"
        self.max_history_size = 100

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
        
        # Ограничение размера истории
        if len(history) > self.max_history_size:
            history.pop(0)

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
            self._add_to_request_history(doc_id, 'generate', 'processing')
            
            response = requests.post(
                f"{self.base_url}/generate_documents",
                json={"data": data},
                headers=self.headers
            )
            response.raise_for_status()
            
            documents_list = response.json()
            result = {
                'documents': documents_list,
                'merged_data': data
            }
            
            self._add_to_request_history(doc_id, 'generate', 'success')
            return result
            
        except requests.RequestException as e:
            self._add_to_request_history(doc_id, 'generate', 'error')
            st.error(f"Ошибка при генерации документов: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                st.error(f"Статус код: {e.response.status_code}")
                st.error(f"Ответ сервера: {e.response.text}")
            return None

    def download_document(self, url: str, doc_id: str) -> Optional[bytes]:
        """Скачивание сгенерированного документа"""
        try:
            self._add_to_request_history(doc_id, 'download', 'processing')
            
            download_url = f"{self.base_url}{url}"
            response = requests.get(download_url)
            response.raise_for_status()
            
            self._add_to_request_history(doc_id, 'download', 'success')
            return response.content
            
        except requests.RequestException as e:
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