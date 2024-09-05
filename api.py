import requests
import streamlit as st
from config import load_config

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