import streamlit as st
import pandas as pd
from src.utils.utils import format_date, flatten_dict


def display_search_form():
    st.subheader("Параметры поиска")

    col1, col2, col3 = st.columns(3)

    with col1:
        rn = st.text_input("Регистрационный номер")
        country = st.text_input("Страна производства")
        materials = st.text_input("Коды материалов (через запятую)")
        query = st.text_input("Поисковый запрос")

    with col2:
        doc_type = st.selectbox("Тип документа", ["", "C", "D"],
                                format_func=lambda
                                    x: "Сертификаты" if x == "C" else "Декларации" if x == "D" else "Все")
        manufacturer = st.text_input("Производитель")
        brand = st.text_input("Бренд")
        tnved = st.text_input("Код ТН ВЭД (поиск по началу кода)")

    with col3:
        genders = st.text_input("Коды гендеров (через запятую)")
        start_date = st.date_input("Дата начала действия")
        end_date = st.date_input("Дата окончания действия")

    advanced = st.expander("Расширенные параметры")
    with advanced:
        applicant = st.text_input("Заявитель")
        product_name = st.text_input("Наименование продукции")

    return {
        "rn": rn,
        "t": doc_type,
        "country": country,
        "manufacturer": manufacturer,
        "q": query,
        "tnved": tnved,
        "materials": materials,
        "brand": brand,
        "genders": genders,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "applicant": applicant,
        "product_name": product_name
    }


def display_results_table(items):
    formatted_results = []
    for item in items:
        flat_item = flatten_dict(item)
        formatted_item = {
            "Выбрать": False,
            "ID": flat_item.get("ID", ""),
            "Номер": flat_item.get("Number", ""),
            "Тип": "Декларация" if flat_item.get("Type") == "D" else "Сертификат",
            "Статус": flat_item.get("Status", ""),
            "Дата регистрации": format_date(flat_item.get("RegistrationDate")),
            "Действителен до": format_date(flat_item.get("ValidityPeriod")),
            "Заявитель": flat_item.get("Applicant", ""),
            "Производитель": flat_item.get("Manufacturer_Name", ""),
            "Продукция": flat_item.get("Product_Name", ""),
            "ТН ВЭД": ", ".join(flat_item.get("Product_Tnveds", [])),
            "Бренд": flat_item.get("Brand", ""),
            "Материалы": ", ".join(flat_item.get("Materials", [])),
        }
        formatted_results.append(formatted_item)

    df = pd.DataFrame(formatted_results)

    column_config = {
        "Выбрать": st.column_config.CheckboxColumn(
            "Выбрать",
            help="Выберите для просмотра подробной информации",
            default=False,
        )
    }

    for col in df.columns:
        if col != "Выбрать":
            column_config[col] = st.column_config.Column(
                col,
                disabled=True
            )

    return st.data_editor(
        df,
        hide_index=True,
        column_config=column_config,
        use_container_width=True
    )


def display_pagination(current_page, total_pages):
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("◀ Предыдущая") and current_page > 0:
            return current_page - 1
    with col2:
        st.write(f"Страница {current_page + 1} из {total_pages}")
    with col3:
        if st.button("Следующая ▶") and current_page < total_pages - 1:
            return current_page + 1
    return current_page


def display_download_button(df):
    csv = df.to_csv(index=False)
    st.download_button(
        label="Скачать результаты как CSV",
        data=csv,
        file_name="fsa_search_results.csv",
        mime="text/csv",
    )


def display_document_details(details):
    st.subheader("Подробная информация о документе")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Основная информация:")
        st.write(f"ID: {details.get('ID', 'Н/Д')}")
        st.write(f"Номер: {details.get('Number', 'Н/Д')}")
        st.write(f"Тип: {'Декларация' if details.get('Type') == 'D' else 'Сертификат'}")
        st.write(f"Статус: {details.get('Status', 'Н/Д')}")
        st.write(f"Дата регистрации: {format_date(details.get('RegistrationDate', 'Н/Д'))}")
        st.write(f"Действителен до: {format_date(details.get('ValidityPeriod', 'Н/Д'))}")

    with col2:
        st.write("Информация о продукции:")
        st.write(f"Наименование: {details.get('Product', {}).get('Name', 'Н/Д')}")
        st.write(f"ТН ВЭД: {', '.join(details.get('Product', {}).get('Tnveds', []))}")
        st.write(f"Бренд: {details.get('Product', {}).get('Brand', 'Н/Д')}")
        st.write(f"Материалы: {', '.join(details.get('Product', {}).get('Materials', []))}")

    st.write("Заявитель:")
    st.write(details.get('Applicant', {}).get('Name', 'Н/Д'))

    st.write("Производитель:")
    st.write(details.get('Manufacturer', {}).get('Name', 'Н/Д'))

    if 'Certificate' in details:
        st.write("Информация о сертификате:")
        st.write(f"Схема сертификации: {details['Certificate'].get('CertificationScheme', 'Н/Д')}")
        st.write(f"Орган по сертификации: {details['Certificate'].get('CertificationBody', {}).get('Name', 'Н/Д')}")

    if 'Declaration' in details:
        st.write("Информация о декларации:")
        st.write(f"Схема декларирования: {details['Declaration'].get('DeclarationScheme', 'Н/Д')}")
        st.write(f"Основание принятия: {details['Declaration'].get('BaseDeclaration', 'Н/Д')}")


def display_search_one_button():
    return st.button("Поиск одного наиболее релевантного документа")


def display_generate_certificates_button():
    return st.button("Сгенерировать сертификаты для выбранных документов")


def display_create_document_files_button():
    return st.button("Создать файлы документов")