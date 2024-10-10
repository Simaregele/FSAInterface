import streamlit as st
from src.api.api import search_fsa, get_document_details, search_one_fsa
from src.api.document_file_creator import create_document_file
from src.auth import authenticator
from src.utils.certificate_generator import generate_certificate
from src.ui.ui_components import display_search_form, display_results_table, display_pagination, display_download_button

st.set_page_config(layout="wide")

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

        if results:
            st.session_state.total_pages = results.get('totalPages', 1)
            total_results = results.get('total', 0)
            items = results.get('items', [])

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

                    if st.button("Сгенерировать сертификаты для выбранных документов"):
                        for doc_id, details in selected_details.items():
                            pptx_content = generate_certificate(details)
                            if pptx_content:
                                st.download_button(
                                    label=f"Скачать сертификат для {doc_id}",
                                    data=pptx_content,
                                    file_name=f"certificate_{doc_id}.pptx",
                                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                                )
                            else:
                                st.error(f"Не удалось сгенерировать сертификат для документа {doc_id}")

                    if st.button("Создать файлы документов"):
                        for doc_id, details in selected_details.items():
                            result = create_document_file(details)
                            if result:
                                st.success(f"Файл документа {doc_id} успешно создан.")
                            else:
                                st.error(f"Не удалось создать файл документа {doc_id}.")

                new_page = display_pagination(st.session_state.current_page, st.session_state.total_pages)
                if new_page != st.session_state.current_page:
                    st.session_state.current_page = new_page
                    st.rerun()

                display_download_button(edited_df)
        else:
            st.error("Произошла ошибка при выполнении поиска. Пожалуйста, попробуйте еще раз.")

if __name__ == "__main__":
    main()