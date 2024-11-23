import os
import subprocess
import tempfile

import streamlit as st

st.title("OCRmyPDF Web Portal")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    rotate_pages = st.checkbox("--rotate-pages", help="Rotate pages to correct orientation")
    remove_background = st.checkbox("--remove-background", help="Remove background from the PDF")
    deskew = st.checkbox("--deskew", help="Deskew the PDF pages")
    clean = st.checkbox("--clean", help="Clean the PDF")
    clean_final = st.checkbox("--clean-final", help="Perform final cleaning on the PDF")
    redo_ocr = st.checkbox("--redo-ocr", help="Redo OCR on the PDF")
    optimize_n = st.slider("--optimize N", min_value=0, max_value=3, value=1, help="Optimize the PDF with level N")

    if st.button("Process"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
            tmp_input.write(uploaded_file.read())
            input_pdf = tmp_input.name

        output_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        flags = {
            "--rotate-pages": rotate_pages,
            "--remove-background": remove_background,
            "--deskew": deskew,
            "--clean": clean,
            "--clean-final": clean_final,
            "--redo-ocr": redo_ocr,
        }
        cmd = ["ocrmypdf"] + [flag for flag, enabled in flags.items() if enabled]
        cmd.extend(["--optimize", str(optimize_n), input_pdf, output_pdf])

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
