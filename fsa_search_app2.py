import streamlit as st
import pandas as pd
from api import search_fsa
from utils import format_date, flatten_dict

st.set_page_config(layout="wide")

def main():
    st.title("Поиск в базе FSA")

    # Создаем поля ввода для параметров
    col1, col2, col3 = st.columns(3)
    with col1:
        rn = st.text_input("Регистрационный номер")
        country = st.text_input("Страна производства")
    with col2:
        doc_type = st.selectbox("Тип документа", ["", "C", "D"],
                                format_func=lambda x: "Сертификаты" if x == "C" else "Декларации" if x == "D" else "Все")
        manufacturer = st.text_input("Производитель")
    with col3:
        query = st.text_input("Поисковый запрос")
        tnved = st.text_input("Код ТН ВЭД (поиск по началу кода)")

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    if 'total_pages' not in st.session_state:
        st.session_state.total_pages = 1

    if 'search_params' not in st.session_state:
        st.session_state.search_params = {}

    if st.button("Поиск"):
        # Формируем параметры запроса
        params = {
            "rn": rn,
            "t": doc_type,
            "country": country,
            "manufacturer": manufacturer,
            "q": query,
            "tnved": tnved
        }
        # Удаляем пустые параметры
        params = {k: v for k, v in params.items() if v}
        st.session_state.search_params = params
        st.session_state.current_page = 0

    # Выполняем поиск или обновляем страницу
    if st.session_state.search_params:
        results = search_fsa(st.session_state.search_params, st.session_state.current_page)

        if results:
            # Обновляем информацию о пагинации
            total_pages = results.get('totalPages') or results.get('pagination', {}).get('totalPages', 1)
            total_results = results.get('total') or results.get('pagination', {}).get('total', 0)
            st.session_state.total_pages = total_pages

            # Получаем список элементов
            items = results.get('items') or results.get('pagination', {}).get('items', [])

            # Преобразуем результаты в более удобный формат
            formatted_results = []
            for index, item in enumerate(items):
                flat_item = flatten_dict(item)
                formatted_item = {
                    "Выбрать": False,  # Добавляем чекбокс
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

            # Создаем DataFrame
            df = pd.DataFrame(formatted_results)

            # Отображаем результаты
            st.subheader("Результаты поиска:")
            st.write(f"Найдено результатов: {total_results}")

            # Создаем конфигурацию колонок
            column_config = {
                "Выбрать": st.column_config.CheckboxColumn(
                    "Выбрать",
                    help="Выберите для просмотра подробной информации",
                    default=False,
                )
            }

            # Добавляем конфигурацию для остальных колонок, делая их неизменяемыми
            for col in df.columns:
                if col != "Выбрать":
                    column_config[col] = st.column_config.Column(
                        col,
                        disabled=True
                    )

            # Используем st.data_editor для отображения таблицы с чекбоксами
            edited_df = st.data_editor(
                df,
                hide_index=True,
                column_config=column_config,
                use_container_width=True
            )

            # Отображаем подробную информацию о выбранных элементах
            selected_items = edited_df[edited_df["Выбрать"]].index.tolist()
            if selected_items:
                st.subheader("Подробная информация о выбранных документах:")
                for index in selected_items:
                    st.json(items[index])

            # Пагинация
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                if st.button("◀ Предыдущая") and st.session_state.current_page > 0:
                    st.session_state.current_page -= 1
                    st.rerun()
            with col2:
                st.write(f"Страница {st.session_state.current_page + 1} из {st.session_state.total_pages}")
            with col3:
                if st.button("Следующая ▶") and st.session_state.current_page < st.session_state.total_pages - 1:
                    st.session_state.current_page += 1
                    st.rerun()

            # Добавляем возможность скачать результаты
            csv = df.to_csv(index=False)
            st.download_button(
                label="Скачать результаты как CSV",
                data=csv,
                file_name="fsa_search_results.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    main()