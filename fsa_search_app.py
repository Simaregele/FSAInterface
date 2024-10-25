import streamlit as st
from src.api.api import search_fsa, get_document_details, search_one_fsa
from src.api.document_file_creator import create_document_file
from src.auth import authenticator
from src.utils.certificate_generator import generate_documents
from src.ui.ui_components import display_search_form, display_results_table

st.set_page_config(layout="wide")


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
                st.write(f"Найдено результатов: {total_results}")

                edited_df = display_results_table(items)

                selected_items = edited_df[edited_df["Выбрать"]].index.tolist()

                if selected_items:
                    st.subheader("Подробная информация о выбранных документах:")
                    selected_details = {}
                    for index in selected_items:
                        item = items[index]
                        doc_type = "declaration" if item["Type"] == "D" else "certificate"
                        details = get_document_details(item["ID"], doc_type)
                        if details:
                            selected_details[item["ID"]] = details
                            st.json(details)

                    if st.button("Сгенерировать документы для выбранных заявок"):
                        clear_generated_documents()  # Очищаем предыдущие результаты
                        for doc_id, details in selected_details.items():
                            documents = generate_documents(details)
                            if documents:
                                st.session_state.generated_documents[doc_id] = documents
                                st.success(f"Документы для заявки {doc_id} успешно сгенерированы!")
                            else:
                                st.error(f"Не удалось сгенерировать документы для заявки {doc_id}")
                        st.rerun()  # Перезапускаем приложение для обновления интерфейса

                    if st.session_state.generated_documents:
                        for doc_id, documents in st.session_state.generated_documents.items():
                            st.write(f"Документы для заявки {doc_id}:")
                            col1, col2 = st.columns(2)

                            with col1:
                                if st.download_button(
                                    label="Скачать сертификат / Декларацию.",
                                    data=documents['certificate_content'],
                                    file_name=documents['certificate_filename'],
                                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                    key=f"cert_{doc_id}"
                                ):
                                    st.session_state.downloaded_documents.setdefault(doc_id, {})["certificate"] = True
                                    st.rerun()

                            with col2:
                                if st.download_button(
                                    label="Скачать доверенность",
                                    data=documents['attorney_content'],
                                    file_name=documents['attorney_filename'],
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"atty_{doc_id}"
                                ):
                                    st.session_state.downloaded_documents.setdefault(doc_id, {})["attorney"] = True
                                    st.rerun()

                            # Обновляем текст кнопок, если документы уже скачаны
                            if st.session_state.downloaded_documents.get(doc_id, {}).get("certificate"):
                                st.write("Сертификат скачан")
                            if st.session_state.downloaded_documents.get(doc_id, {}).get("attorney"):
                                st.write("Доверенность скачана")

                    if st.button("Создать файлы документов"):
                        for doc_id, details in selected_details.items():
                            result = create_document_file(details)
                            if result:
                                st.success(f"Файл документа {doc_id} успешно создан.")
                            else:
                                st.error(f"Не удалось создать файл документа {doc_id}.")

        else:
            st.error("Произошла ошибка при выполнении поиска. Пожалуйста, попробуйте еще раз.")

if __name__ == "__main__":
    main()