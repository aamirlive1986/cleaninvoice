import streamlit as st
import openai
import os
import json
import pandas as pd
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# --- CONFIGURATION ---
st.set_page_config(page_title="CleanInvoice AI", page_icon="🧾")

# OpenAI Client
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("❌ API Key not found! Please check your .env file.")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- SESSION STATE ---
if 'count' not in st.session_state:
    st.session_state['count'] = 0

if 'data' not in st.session_state:
    st.session_state['data'] = []

# --- MAIN UI ---
st.title("🧾 CleanInvoice AI")
st.write("Upload a receipt/invoice (PNG, JPG) and get extracted data!")

# Sidebar
with st.sidebar:
    st.write(f"**Parses used:** {st.session_state['count']} / 3")
    if st.session_state['count'] >= 3:
        st.error("Limit reached!")
    else:
        st.success("Free Tier Active")

# File Uploader
uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Receipt", width=300)
    
    if st.session_state['count'] < 3:
        if st.button("Process Invoice", type="primary"):
            with st.spinner("Analyzing with AI..."):
                try:
                    import base64
                    base64_image = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an invoice parser. Extract Vendor, Total Amount, Date, and Tax. Return ONLY JSON."
                            },
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        response_format={"type": "json_object"},
                        max_tokens=500
                    )
                    
                    result = json.loads(response.choices[0].message.content)
                    result['Filename'] = uploaded_file.name
                    
                    st.session_state['data'].append(result)
                    st.session_state['count'] += 1
                    
                    st.success("Extraction Successful!")
                    st.json(result)
                    
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.warning("Limit reached!")

# --- DATA TABLE ---
st.divider()
st.subheader("📊 Extracted Invoices")

if st.session_state['data']:
    df = pd.DataFrame(st.session_state['data'])
    st.dataframe(df)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="invoices.csv",
        mime="text/csv"
    )