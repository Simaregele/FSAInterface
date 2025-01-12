import streamlit as st
from src.api.api import search_fsa, get_document_details, search_one_fsa
from src.api.document_file_creator import create_document_file
from src.auth import authenticator
from src.utils.certificate_generator import generate_documents
from src.ui.ui_components import display_search_form, display_results_table
from config.config import load_config
import requests

st.set_page_config(layout="wide")

# Загружаем конфигурацию
config = load_config()

def clear_generated_documents():
    st.session_state.generated_documents = {}
    st.session_state.downloaded_documents = {}

def initialize_session_state():
    """Инициализация состояний сессии"""
    default_states = {
        'current_page': 0,
        'total_pages': 1,
        'search_params': {},
        'generated_documents': {},
        'downloaded_documents': {}
    }
    
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def handle_search_one_document(search_params):
    """Обработка поиска одного документа"""
    result = search_one_fsa(search_params)
    if result:
        st.subheader("Наиболее релевантный документ:")
        st.json(result)
    else:
        st.warning("Не найдено подходящих документов.")

def process_search_results(results):
    """Обработка результатов поиска"""
    if isinstance(results, dict):
        st.session_state.total_pages = results.get('totalPages', 1)
        total_results = results.get('total', 0)
        items = results.get('items', [])
    elif isinstance(results, list):
        st.session_state.total_pages = 1
        total_results = len(results)
        items = results
    else:
        st.error(f"Неожиданный формат результатов: {type(results)}")
        return None, None
    
    return total_results, items

def display_document_details(selected_items, items):
    """Отображение подробной информации о выбранных документах"""
    selected_details = {}
    selected_search_data = {}

    for index in selected_items:
        item = items[index]
        doc_type = "declaration" if item["Type"] == "D" else "certificate"
        details = get_document_details(item["ID"], doc_type)

        if details:
            selected_details[item["ID"]] = details
            selected_search_data[item["ID"]] = item

            st.write(f"Документ {item['ID']}:")
            with st.expander("Данные из поиска"):
                st.json(item)
            with st.expander("Детальные данные"):
                st.json(details)

    return selected_details, selected_search_data

def handle_document_generation(selected_details, selected_search_data):
    """Обработка генерации документов"""
    clear_generated_documents()
    for doc_id, details in selected_details.items():
        search_data = selected_search_data.get(doc_id, {})
        documents = generate_documents(details, search_data=search_data)

        if documents:
            st.session_state.generated_documents[doc_id] = documents
            st.success(f"Документы для заявки {doc_id} успешно сгенерированы!")
            with st.expander(f"Данные, использованные для генерации {doc_id}"):
                st.json(documents.get('merged_data', {}))
        else:
            st.error(f"Не удалось сгенерировать документы для заявки {doc_id}")
    st.rerun()

def display_generated_documents():
    """Отображение сгенерированных документов"""
    for doc_id, documents in st.session_state.generated_documents.items():
        st.write(f"Документы для заявки {doc_id}:")
        cols = st.columns(len(documents['documents']))
        
        for col, doc in zip(cols, documents['documents']):
            with col:
                download_url = f"{config['LOCAL_CERTIFICATE_API_URL']}{doc['url']}"
                mime_types = {
                    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'pdf': 'application/pdf'
                }
                mime_type = mime_types.get(doc['format'], 'application/octet-stream')
                
                file_response = requests.get(download_url)
                if file_response.status_code == 200:
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
                
                if st.session_state.downloaded_documents.get(doc_id, {}).get(doc['type']):
                    st.write(f"{doc['name']} скачан")

def handle_document_creation(selected_details, selected_search_data):
    """Обработка создания файлов документов"""
    for doc_id, details in selected_details.items():
        search_data = selected_search_data.get(doc_id, {})
        merged_details = details.copy()
        merged_details.update({f'search_{k}': v for k, v in search_data.items()})

        result = create_document_file(merged_details)
        if result:
            st.success(f"Файл документа {doc_id} успешно создан.")
        else:
            st.error(f"Не удалось создать файл документа {doc_id}.")

def show_search_interface():
    """Основная функция интерфейса поиска"""
    col1, col2 = st.columns([3, 1])
    with col2:
        authenticator.logout()

    search_params = display_search_form()
    initialize_session_state()

    if st.button("Поиск"):
        st.session_state.search_params = {k: v for k, v in search_params.items() if v}
        st.session_state.current_page = 0

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Поиск одного наиболее релевантного документа"):
            handle_search_one_document(st.session_state.search_params)

    if st.session_state.search_params:
        results = search_fsa(st.session_state.search_params, st.session_state.current_page)

        if results is not None:
            total_results, items = process_search_results(results)
            
            if not items:
                st.warning("По вашему запросу ничего не найдено.")
            else:
                st.subheader("Результаты поиска:")
                st.write(f"Найдено результатов: {total_results}")

                edited_df = display_results_table(items)
                selected_items = edited_df[edited_df["Выбрать"]].index.tolist()

                if selected_items:
                    st.subheader("Подробная информация о выбранных документах:")
                    selected_details, selected_search_data = display_document_details(selected_items, items)

                    if st.button("Сгенерировать документы для выбранных заявок"):
                        handle_document_generation(selected_details, selected_search_data)

                    if st.session_state.generated_documents:
                        display_generated_documents()

                    if st.button("Создать файлы документов"):
                        handle_document_creation(selected_details, selected_search_data)
        else:
            st.error("Произошла ошибка при выполнении поиска. Пожалуйста, попробуйте еще раз.")

def main():
    st.title("Поиск в базе FSA")

    if not authenticator.is_authenticated():
        authenticator.login()
    else:
        show_search_interface()

if __name__ == "__main__":
    main()