import requests
import streamlit as st
from config import load_config
from auth import authenticator

config = load_config()


def search_fsa(params, page=0, page_size=20):
    url = f"{config['api_base_url']}{config['search_endpoint']}"
    params['page'] = page
    params['pageSize'] = page_size

    headers = {}
    token = authenticator.get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        st.error("Ошибка аутентификации. Пожалуйста, войдите в систему снова.")
        st.session_state["authentication_status"] = False
        st.rerun()
    else:
        st.error(f"Ошибка при запросе: {response.status_code}")
        return None


def get_document_details(doc_id, doc_type):
    url = f"{config['api_base_url']}{config['document_endpoints'][doc_type]}/{doc_id}"

    headers = {}
    token = authenticator.get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        st.error("Ошибка аутентификации. Пожалуйста, войдите в систему снова.")
        st.session_state["authentication_status"] = False
        st.rerun()
    else:
        st.error(f"Ошибка при запросе детальной информации: {response.status_code}")
        return None


def sync_document(doc_id, doc_type):
    url = f"{config['api_base_url']}{config['sync_endpoints'][doc_type]}/{doc_id}"

    headers = {}
    token = authenticator.get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        st.error("Ошибка аутентификации. Пожалуйста, войдите в систему снова.")
        st.session_state["authentication_status"] = False
        st.rerun()
    else:
        st.error(f"Ошибка при синхронизации документа: {response.status_code}")
        return None