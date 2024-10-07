import streamlit as st
import pandas as pd
from src.utils.utils import format_date, flatten_dict


def display_search_form():
    col1, col2, col3 = st.columns(3)
    with col1:
        rn = st.text_input("Регистрационный номер")
        country = st.text_input("Страна производства")
    with col2:
        doc_type = st.selectbox("Тип документа", ["", "C", "D"],
                                format_func=lambda
                                    x: "Сертификаты" if x == "C" else "Декларации" if x == "D" else "Все")
        manufacturer = st.text_input("Производитель")
    with col3:
        query = st.text_input("Поисковый запрос")
        tnved = st.text_input("Код ТН ВЭД (поиск по началу кода)")

    return {"rn": rn, "t": doc_type, "country": country, "manufacturer": manufacturer, "q": query, "tnved": tnved}


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