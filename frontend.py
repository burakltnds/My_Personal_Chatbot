import streamlit as st
import requests
import ast

st.set_page_config(page_title="GayuhGPT", page_icon="👑")
st.title("👑 GayuhGPT")
st.caption("Komut bekleniyor...")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Komutunuzu buraya yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = requests.post(
                "http://web:8080/chat", 
                json={"session_id": "sohbet", "message": prompt} 
            )
            
            
            raw_text = response.text
            answer = raw_text
            
            
            try:
                veri = response.json()
                
                if isinstance(veri, dict) and 'message' in veri:
                    answer = veri['message']
            
                elif isinstance(veri, str):
                    try:
                        sozluk = ast.literal_eval(veri)
                        if isinstance(sozluk, dict) and 'message' in sozluk:
                            answer = sozluk['message']
                    except:
                        answer = veri
            except:
                pass

            
            answer = answer.replace('\\n', '\n')
            
            if answer.startswith("{'id':"):
                import re
                match = re.search(r"'message':\s*'(.*)'\}$", answer, re.DOTALL)
                if match:
                    answer = match.group(1).replace('\\n', '\n')
                
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
        except Exception as e:
            st.error(f"Bağlantı hatası oluştu: {e}")