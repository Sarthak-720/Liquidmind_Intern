import streamlit as st
import json
from PIL import Image
from azureocr import azure_ocr
from Gemini1 import find_details

st.header("INVOICE DETAILS")
st.divider()

if "page" not in st.session_state:
    st.session_state["page"]="Home"

if "invoice" not in st.session_state:
    st.session_state["invoice"]={}

extracted_text="none"
if "Total_data" not in st.session_state:
    st.session_state["Total_data"] = ""

if st.session_state["page"] == "Home":
    if st.button("Add new document"):
        st.session_state["page"] = "new"

    elif st.button("View past records"):
        st.session_state["page"] = "past"
        pass

    elif st.button("Chat"):
        st.session_state["page"] = "Chat"

    else:pass

elif st.session_state["page"] == "new":

    date = st.text_input("Enter the date in format dd/mm/yy")

    uploaded_file = st.file_uploader("Upload your invoice", type=["jpg", "jpeg", "png", "tiff", "pdf"])


    if uploaded_file is not None:
        st.write("File uploaded successfully")
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        #Extract text using OCR 
        extracted_text = azure_ocr(uploaded_file)
        st.subheader("Extracted Invoice Details")
        edited_text = st.text_area("Edit the extracted details below, in case you want to:", value=extracted_text, height=300)
        st.session_state["invoice"][date] = edited_text
        if st.button("Save Details"):
           st.success("Details have been saved successfully!")
           st.write("Saved Invoice Details:")
        cleaned_data = st.session_state["invoice"][date].strip("```json").strip("```").strip("'''\"").strip()
        st.session_state["Total_data"] += cleaned_data
        st.write(cleaned_data)

    if st.button("Go back"):
            st.session_state["page"] = "Home"    
    
elif st.session_state['page'] == "past":
    date = st.text_input("Enter the date you want to access (dd/mm/yy)")
    if date in st.session_state["invoice"]:
        invoice_data = st.session_state["invoice"][date]
        st.write(f"Invoice for {date}:")
        st.write(invoice_data)
    else:
        st.write(f"No invoice data found for {date}.")
    
    if st.button("Go back"):
            st.session_state["page"] = "Home"   


elif st.session_state['page'] == "Chat":
    detail = st.text_input("Detail which you want to search:")
    if st.button("Go"):
        st.write(find_details(st.session_state["invoice"],detail))
        if st.button("try again"):
            st.session_state["page"] = "Chat" 
    if st.button("Go back"):
        st.session_state["page"] = "Home"  
    




