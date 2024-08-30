import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime


def load_config():
    with open('config.json') as config_file:
        return json.load(config_file)


config = load_config()


def search_fsa(params, page=0, page_size=20):
    url = config['api_url']
    params['page'] = page
    params['pageSize'] = page_size
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Ошибка при запросе: {response.status_code}")
        return None


def format_date(date_string):
    if date_string:
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ").strftime("%d.%m.%Y")
    return ""


def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def main():
    st.title("Поиск в базе FSA")

    # Создаем поля ввода для параметров
    rn = st.text_input("Регистрационный номер")
    doc_type = st.selectbox("Тип документа", ["", "C", "D"],
                            format_func=lambda x: "Сертификаты" if x == "C" else "Декларации" if x == "D" else "Все")
    country = st.text_input("Страна производства")
    manufacturer = st.text_input("Производитель")
    query = st.text_input("Поисковый запрос")

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
            "q": query
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
            for item in items:
                flat_item = flatten_dict(item)
                formatted_item = {
                    "ID": flat_item.get("ID", ""),
                    "Номер": flat_item.get("Number", ""),
                    "Тип": "Декларация" if flat_item.get("Type") == "D" else "Сертификат",
                    "Статус": flat_item.get("Status", ""),
                    "Дата регистрации": format_date(flat_item.get("RegistrationDate")),
                    "Действителен до": format_date(flat_item.get("ValidityPeriod")),
                    "Заявитель": flat_item.get("Applicant", ""),
                    "Производитель_Наименование": flat_item.get("Manufacturer_Name", ""),
                    "Производитель_Адрес": flat_item.get("Manufacturer_Address", ""),
                    "Производитель_Филиалы": flat_item.get("Manufacturer_Branches", ""),
                    "Продукция_Наименование": flat_item.get("Product_Name", ""),
                    "Продукция_Описание": flat_item.get("Product_Description", ""),
                    "Продукция_Страна": flat_item.get("Product_Country", ""),
                    "Продукция_Бренды": flat_item.get("Product_Brands", ""),
                    "Продукция_Пол": flat_item.get("Product_Genders", ""),
                    "Продукция_Материалы": flat_item.get("Product_Materials", ""),
                    "Продукция_ТН_ВЭД": flat_item.get("Product_Tnveds", ""),
                }
                formatted_results.append(formatted_item)

            # Создаем DataFrame
            df = pd.DataFrame(formatted_results)

            # Отображаем результаты
            st.subheader("Результаты поиска:")
            st.write(f"Найдено результатов: {total_results}")
            st.dataframe(df)

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