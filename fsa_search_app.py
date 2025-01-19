import streamlit as st
from src.api.api import search_fsa, get_document_details, search_one_fsa
from src.api.document_file_creator import create_document_file
from src.auth import authenticator
from src.utils.certificate_generator import generate_documents
from src.ui.ui_components import display_search_form, display_results_table
from config.config import load_config
import requests
from src.ui.document_download import display_document_download_button

st.set_page_config(layout="wide")

# Загружаем конфигурацию
config = load_config()

def clear_generated_documents():
    st.session_state.generated_documents = {}
    st.session_state.downloaded_documents = {}

def main():
    st.title("Поиск в базе FSA")

    if not authenticator.is_authenticated():
        authenticator.login()
    else:
        show_search_interface()

def show_search_interface():
    col1, col2 = st.columns([3, 1])
    with col2:
        authenticator.logout()

    search_params = display_search_form()

    # Инициализация состояний
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    if 'total_pages' not in st.session_state:
        st.session_state.total_pages = 1

    if 'search_params' not in st.session_state:
        st.session_state.search_params = {}

    if 'generated_documents' not in st.session_state:
        st.session_state.generated_documents = {}

    if 'downloaded_documents' not in st.session_state:
        st.session_state.downloaded_documents = {}

    if st.button("Поиск"):
        st.session_state.search_params = {k: v for k, v in search_params.items() if v}
        st.session_state.current_page = 0

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Поиск одного наиболее релевантного документа"):
            result = search_one_fsa(st.session_state.search_params)
            if result:
                st.subheader("Наиболее релевантный документ:")
                st.json(result)
            else:
                st.warning("Не найдено подходящих документов.")

    if st.session_state.search_params:
        results = search_fsa(st.session_state.search_params, st.session_state.current_page)

        if results is not None:
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
                return

            if not items:
                st.warning("По вашему запросу ничего не найдено.")
            else:
                st.subheader("Результаты поиска:")
                st.write(f"Нйдено результатов: {total_results}")

                edited_df = display_results_table(items)
                selected_items = edited_df[edited_df["Выбрать"]].index.tolist()

                if selected_items:
                    st.subheader("Подробная информация о выбранных документах:")
                    selected_details = {}
                    selected_search_data = {}  # Сохраняем данные из поиска

                    for index in selected_items:
                        item = items[index]
                        doc_type = "declaration" if item["Type"] == "D" else "certificate"
                        details = get_document_details(item["ID"], doc_type)

                        if details:
                            selected_details[item["ID"]] = details
                            selected_search_data[item["ID"]] = item  # Сохраняем данные поиска

                            # Показываем данные из обоих источников
                            st.write(f"Документ {item['ID']}:")

                            with st.expander("Данные из поиска"):
                                st.json(item)

                            with st.expander("Детальные данные"):
                                st.json(details)

                    if st.button("Сгенерировать документы для выбранных заявок"):
                        clear_generated_documents()  # Очищаем предыдущие результаты
                        for doc_id, details in selected_details.items():
                            # Передаем оба набора данных в функцию генерации
                            search_data = selected_search_data.get(doc_id, {})
                            documents = generate_documents(details, search_data=search_data)

                            if documents:
                                st.session_state.generated_documents[doc_id] = documents
                                st.success(f"Документы для заявки {doc_id} успешно сгенерированы!")

                                # Показываем данные, использованные при генерации
                                with st.expander(f"Данные, использованные для генерации {doc_id}"):
                                    st.json(documents.get('merged_data', {}))
                            else:
                                st.error(f"Не удалось сгенерировать документы для заявки {doc_id}")
                        st.rerun()

                    if st.session_state.generated_documents:
                        for doc_id, documents in st.session_state.generated_documents.items():
                            st.write(f"Документы для заявки {doc_id}:")
                            
                            # Создаем колонки динамически в зависимости от количества документов
                            cols = st.columns(len(documents['documents']))
                            
                            for col, doc in zip(cols, documents['documents']):
                                with col:
                                    display_document_download_button(doc, doc_id)

                    if st.button("Создать файлы документов"):
                        for doc_id, details in selected_details.items():
                            # Для создания файлов также используем объединенные данные
                            search_data = selected_search_data.get(doc_id, {})
                            merged_details = details.copy()
                            merged_details.update({f'search_{k}': v for k, v in search_data.items()})

                            result = create_document_file(merged_details)
                            if result:
                                st.success(f"Файл документа {doc_id} успешно создан.")
                            else:
                                st.error(f"Не удалось создать файл документа {doc_id}.")

        else:
            st.error("Произошла ошибка при выполнении поиска. Пожалуйста, попробуйте еще раз.")

if __name__ == "__main__":
    main()