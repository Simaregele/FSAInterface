import streamlit as st
from typing import Dict, Any
from src.api.document_constructor import DocumentConstructor

class DocumentConstructorUI:
    def __init__(self):
        self.constructor = DocumentConstructor()

    def display_request_status(self, doc_id: str):
        """Отображение статуса запросов для документа"""
        status = self.constructor.get_request_status(doc_id)
        if status:
            with st.expander("Статус запросов"):
                for request_type, state in status.items():
                    icon = {
                        'processing': '⏳',
                        'success': '✅',
                        'error': '❌'
                    }.get(state, '❓')
                    st.write(f"{icon} {request_type}: {state}")

    def display_document_generation_form(self, document_data: Dict[str, Any]):
        """Отображение формы для генерации документов"""
        doc_id = str(document_data.get('ID', 'unknown'))
        st.subheader(f"Генерация документов ({doc_id})")
        
        self.display_request_status(doc_id)
        
        with st.expander("Данные для генерации"):
            st.json(document_data)
            
        if st.button("Сгенерировать документы", key=f"gen_btn_{doc_id}"):
            with st.spinner("Генерация документов..."):
                result = self.constructor.generate_documents(document_data)
                if result:
                    st.session_state.generated_documents = result
                    st.success("Документы успешно сгенерированы!")
                    st.rerun()

    def display_generated_documents(self):
        """Отображение сгенерированных документов"""
        if 'generated_documents' not in st.session_state:
            return

        documents = st.session_state.generated_documents
        st.subheader("Сгенерированные документы")
        
        doc_id = str(documents.get('merged_data', {}).get('ID', 'unknown'))
        self.display_request_status(doc_id)

        for doc in documents.get('documents', []):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"📄 {doc['name']}")
                
            with col2:
                content = self.constructor.download_document(doc['url'], doc_id)
                if content:
                    mime_type = self.constructor.get_mime_type(doc['format'])
                    if st.download_button(
                        label=f"Скачать {doc['format'].upper()}",
                        data=content,
                        file_name=f"{doc['name']}.{doc['format']}",
                        mime=mime_type,
                        key=f"download_{doc['name']}"
                    ):
                        st.success(f"Файл {doc['name']} успешно скачан") 