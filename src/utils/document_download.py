import streamlit as st
import requests
from config.config import Config
from datetime import datetime, timedelta

config = Config.get_instance()

def clear_document_cache():
    """Очистка кэша документов"""
    keys_to_remove = [key for key in st.session_state.keys() 
                     if key.startswith('doc_content_') or 
                        key.startswith('doc_timestamp_')]
    for key in keys_to_remove:
        del st.session_state[key]

def get_document_content(download_url: str, doc_id: str, doc_type: str) -> bytes:
    """
    Получает содержимое документа с кэшированием и проверкой актуальности
    """
    content_key = f"doc_content_{doc_id}_{doc_type}"
    timestamp_key = f"doc_timestamp_{doc_id}_{doc_type}"
    cache_lifetime = timedelta(hours=1)  # Время жизни кэша
    
    current_time = datetime.now()
    
    # Проверяем актуальность кэша
    if (content_key in st.session_state and 
        timestamp_key in st.session_state and 
        current_time - st.session_state[timestamp_key] < cache_lifetime):
        return st.session_state[content_key]
        
    # Если кэш неактуален или отсутствует - скачиваем
    file_response = requests.get(download_url)
    if file_response.status_code == 200:
        st.session_state[content_key] = file_response.content
        st.session_state[timestamp_key] = current_time
        return file_response.content
    return None

def display_document_download_button(doc, doc_id):
    """Отображает кнопку скачивания для документа"""
    download_url = f"{config['LOCAL_CERTIFICATE_API_URL']}{doc['url']}"
    
    mime_types = {
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'pdf': 'application/pdf'
    }
    mime_type = mime_types.get(doc['format'], 'application/octet-stream')
    
    # Добавляем кнопку обновления кэша
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄", key=f"refresh_{doc_id}_{doc['type']}"):
            content_key = f"doc_content_{doc_id}_{doc['type']}"
            timestamp_key = f"doc_timestamp_{doc_id}_{doc['type']}"
            if content_key in st.session_state:
                del st.session_state[content_key]
            if timestamp_key in st.session_state:
                del st.session_state[timestamp_key]
    
    with col1:
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
                if 'downloaded_documents' not in st.session_state:
                    st.session_state.downloaded_documents = {}
                if doc_id not in st.session_state.downloaded_documents:
                    st.session_state.downloaded_documents[doc_id] = {}
                st.session_state.downloaded_documents[doc_id][doc['type']] = True
            
            # Показываем статус скачивания
            if st.session_state.downloaded_documents.get(doc_id, {}).get(doc['type']):
                st.write(f"{doc['name']} скачан") 