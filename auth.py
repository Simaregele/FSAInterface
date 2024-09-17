import requests
import streamlit as st
from datetime import datetime, timedelta
from config import load_config

config = load_config()


class Authenticator:
    def __init__(self):
        self.api_url = config['auth_url']
        self.token_key = "jwt_token"
        self.token_expiry_key = "jwt_token_expiry"

    def login(self):
        st.subheader("Вход в систему")
        username = st.text_input("Имя пользователя")
        password = st.text_input("Пароль", type="password")

        if st.button("Войти"):
            with st.spinner('Выполняется вход в систему...'):
                try:
                    response = requests.post(self.api_url, json={"username": username, "password": password})

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            token = data.get("access")
                            if token:
                                st.session_state[self.token_key] = token
                                st.session_state[self.token_expiry_key] = datetime.now() + timedelta(hours=72)
                                st.session_state["authentication_status"] = True
                                st.success("Вход выполнен успешно!")
                                st.rerun()
                            else:
                                st.error("Токен отсутствует в ответе сервера")
                        except ValueError:
                            st.error("Ошибка при разборе JSON-ответа")
                    else:
                        st.error(f"Ошибка при входе: {response.status_code}")
                        st.write(f"Ответ сервера: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Ошибка при отправке запроса: {str(e)}")

    def logout(self):
        if st.button("Выйти"):
            st.session_state[self.token_key] = None
            st.session_state[self.token_expiry_key] = None
            st.session_state["authentication_status"] = False
            st.rerun()

    def is_authenticated(self):
        if st.session_state.get("authentication_status", False):
            expiry = st.session_state.get(self.token_expiry_key)
            if expiry and expiry > datetime.now():
                return True
            else:
                st.session_state["authentication_status"] = False
                st.session_state[self.token_key] = None
                st.session_state[self.token_expiry_key] = None
        return False

    def get_token(self):
        return st.session_state.get(self.token_key)

    def login_required(self, func):
        def wrapper(*args, **kwargs):
            if self.is_authenticated():
                return func(*args, **kwargs)
            else:
                st.warning("Пожалуйста, выполните вход для доступа к этой странице.")
                self.login()

        return wrapper


authenticator = Authenticator()


# # Пример использования декоратора login_required
# @authenticator.login_required
# def protected_function():
#     st.write("Это защищенная функция, доступная только аутентифицированным пользователям.")
#
# # Если вам нужно использовать аутентификацию в другом файле, вы можете импортировать authenticator:
# # from auth import authenticator