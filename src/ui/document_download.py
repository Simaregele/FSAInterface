import streamlit as st
import requests
from config.config import Config

config = Config.get_instance()

def get_document_content(download_url: str, doc_id: str, doc_type: str) -> bytes:
    """
    Получает содержимое документа с кэшированием
    """
    # Ключ для хранения содержимого файла в session_state
    cache_key = f"doc_content_{doc_id}_{doc_type}"
    
    # Проверяем наличие документа в кэше
    if cache_key in st.session_state:
        return st.session_state[cache_key]
        
    # Если нет в кэше - скачиваем
    file_response = requests.get(download_url)
    if file_response.status_code == 200:
        # Сохраняем в кэш
        st.session_state[cache_key] = file_response.content
        return file_response.content
    return None

def display_document_download_button(doc, doc_id):
    """
    Отображает кнопку скачивания для документа и обрабатывает процесс скачивания
    
    Args:
        doc (dict): Информация о документе (name, url, format, type)
        doc_id (str): ID документа
    """
    download_url = f"{config['LOCAL_CERTIFICATE_API_URL']}{doc['url']}"
    
    mime_types = {
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'pdf': 'application/pdf'
    }
    mime_type = mime_types.get(doc['format'], 'application/octet-stream')
    
    # Получаем содержимое файла из кэша или скачиваем
    content = get_document_content(download_url, doc_id, doc['type'])
    
    if content:
        button_label = f"Скачать {doc['name']}"
        if st.download_button(
            label=button_label,
            data=content,
            file_name=f"{doc['name']}.{doc['format']}",
            mime=mime_type,
            key=f"{doc_id}_{doc['type']}"
        ):
            # Просто отмечаем что файл скачан, без перезагрузки
            if 'downloaded_documents' not in st.session_state:
                st.session_state.downloaded_documents = {}
            if doc_id not in st.session_state.downloaded_documents:
                st.session_state.downloaded_documents[doc_id] = {}
            st.session_state.downloaded_documents[doc_id][doc['type']] = True
            
        # Показываем статус скачивания
        if st.session_state.downloaded_documents.get(doc_id, {}).get(doc['type']):
            st.write(f"{doc['name']} скачан") 