import streamlit as st
from src.api.api import search_fsa, get_document_details, search_one_fsa
from src.api.document_file_creator import create_document_file
from src.auth import authenticator
from src.ui.ui_components import display_search_form, display_results_table
from config.config import load_config
from src.ui.document_constructor_ui import DocumentConstructorUI

st.set_page_config(layout="wide")

# Загружаем конфигурацию
config = load_config()

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

                    # Инициализация UI конструктора документов
                    doc_constructor_ui = DocumentConstructorUI()
                    
                    # Для каждого выбранного документа показываем форму генерации
                    for doc_id, details in selected_details.items():
                        search_data = selected_search_data.get(doc_id, {})
                        merged_data = details.copy()
                        merged_data.update({f'search_{k}': v for k, v in search_data.items()})
                        
                        doc_constructor_ui.display_document_generation_form(merged_data)
                    
                    # Отображение сгенерированных документов
                    doc_constructor_ui.display_generated_documents()

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