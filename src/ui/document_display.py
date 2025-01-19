import streamlit as st
from src.ui.document_download import display_document_download_button
from src.api.document_file_creator import create_document_file

def display_generated_documents_section(generated_documents, selected_details, selected_search_data):
    """
    Отображает секцию с сгенерированными документами и кнопкой создания файлов
    
    Args:
        generated_documents (dict): Словарь с сгенерированными документами
        selected_details (dict): Детали выбранных документов
        selected_search_data (dict): Данные поиска для выбранных документов
    """
    # Отображение сгенерированных документов
    if generated_documents:
        for doc_id, documents in generated_documents.items():
            st.write(f"Документы для заявки {doc_id}:")
            cols = st.columns(len(documents['documents']))
            for col, doc in zip(cols, documents['documents']):
                with col:
                    display_document_download_button(doc, doc_id)

        # Кнопка создания файлов
        if st.button("Создать файлы документов"):
            for doc_id, details in selected_details.items():
                # Объединяем данные для создания файлов
                search_data = selected_search_data.get(doc_id, {})
                merged_details = details.copy()
                merged_details.update({f'search_{k}': v for k, v in search_data.items()})

                result = create_document_file(merged_details)
                if result:
                    st.success(f"Файл документа {doc_id} успешно создан.")
                else:
                    st.error(f"Не удалось создать файл документа {doc_id}.") 