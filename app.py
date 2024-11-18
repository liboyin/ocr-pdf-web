import os
import subprocess
import tempfile

import streamlit as st

st.title("OCRmyPDF Streamlit Web Portal")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    rotate_pages = st.checkbox("--rotate-pages")
    remove_background = st.checkbox("--remove-background")
    deskew = st.checkbox("--deskew")
    clean = st.checkbox("--clean")
    clean_final = st.checkbox("--clean-final")
    redo_ocr = st.checkbox("--redo-ocr")
    optimize_n = st.slider("--optimize N", min_value=0, max_value=3, value=1)

    if st.button("Process"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
            tmp_input.write(uploaded_file.read())
            input_pdf = tmp_input.name

        output_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        cmd = ["ocrmypdf"]
        if rotate_pages:
            cmd.append("--rotate-pages")
        if remove_background:
            cmd.append("--remove-background")
        if deskew:
            cmd.append("--deskew")
        if clean:
            cmd.append("--clean")
        if clean_final:
            cmd.append("--clean-final")
        if redo_ocr:
            cmd.append("--redo-ocr")

        cmd.extend(["--optimize", str(optimize_n)])
        cmd.extend([input_pdf, output_pdf])

        with st.spinner("Processing..."):
            result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            if result.returncode != 0:
                st.error("Error processing PDF:")
                st.error(result.stderr.decode())
            else:
                with open(output_pdf, "rb") as file:
                    st.download_button(
                        label="Download processed PDF",
                        data=file,
                        file_name="processed.pdf",
                        mime="application/pdf"
                    )
        os.remove(input_pdf)
        os.remove(output_pdf)
else:
    st.warning("Please upload a PDF file to begin.")
