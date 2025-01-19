import streamlit as st
import requests
from config.config import Config

config = Config.get_instance()

def display_document_download_button(doc, doc_id):
    """
    Отображает кнопку скачивания для документа и обрабатывает процесс скачивания
    
    Args:
        doc (dict): Информация о документе (name, url, format, type)
        doc_id (str): ID документа
    """
    # Формируем полный URL для скачивания
    download_url = f"{config['LOCAL_CERTIFICATE_API_URL']}{doc['url']}"
    
    # Определяем MIME type на основе формата
    mime_types = {
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'pdf': 'application/pdf'
    }
    mime_type = mime_types.get(doc['format'], 'application/octet-stream')
    
    # Получаем содержимое файла
    file_response = requests.get(download_url)
    if file_response.status_code == 200:
        # Создаем кнопку скачивания с именем из ответа
        button_label = f"Скачать {doc['name']}"
        if st.download_button(
            label=button_label,
            data=file_response.content,
            file_name=f"{doc['name']}.{doc['format']}",
            mime=mime_type,
            key=f"{doc_id}_{doc['type']}"
        ):
            st.session_state.downloaded_documents.setdefault(doc_id, {})
            st.session_state.downloaded_documents[doc_id][doc['type']] = True
            st.rerun()
    
    # Показываем статус скачивания
    if st.session_state.downloaded_documents.get(doc_id, {}).get(doc['type']):
        st.write(f"{doc['name']} скачан") 