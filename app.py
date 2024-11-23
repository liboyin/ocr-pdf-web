import itertools
import subprocess
import tempfile

import streamlit as st

CLEAN = "Clean up pages before OCR, but do not alter the final output"
CLEAN_FINAL = "Clean up pages before OCR and inserts the page into the final output"


def main():
    """Streamlit app entry point."""
    st.set_page_config(page_title="OCRmyPDF")
    st.title("OCRmyPDF Web Portal")
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    rotate_pages = st.checkbox("Fix a mixture of landscape and portrait pages")
    deskew = st.checkbox("Rotate pages so that text is horizontal")
    redo_ocr = st.checkbox("Redo OCR on an OCRed file")
    clean_option = st.radio("Cleanup options", ("Do not clean up", CLEAN, CLEAN_FINAL))
    optimize_n = st.slider("Reduce output PDF file size. 0 for lossless optimization; 3 for most aggressive optimization", min_value=0, max_value=3, value=1)

    if st.button("Process", disabled=not uploaded_file):
        with (tempfile.NamedTemporaryFile(suffix=".pdf") as input_file,
              tempfile.NamedTemporaryFile(suffix=".pdf") as output_file):
            input_file.write(uploaded_file.read())
            input_file.flush()
            flags = {
                "--rotate-pages": rotate_pages,
                "--deskew": deskew,
                "--clean": clean_option == CLEAN,
                "--clean-final": clean_option == CLEAN_FINAL,
                "--redo-ocr": redo_ocr,
            }
            cmd = list(itertools.chain(
                ["ocrmypdf"],
                (flag for flag, enabled in flags.items() if enabled),
                ["--optimize", str(optimize_n)],
                [input_file.name, output_file.name],
            ))
            with st.spinner("Processing..."):
                result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                if result.returncode != 0:
                    st.error("Error processing PDF:")
                    st.error(result.stderr.decode())
                else:
                    output_file.seek(0)
                    st.download_button(
                        label="Download",
                        data=output_file.read(),
                        file_name=uploaded_file.name,
                        mime="application/pdf",
                    )


if __name__ == "__main__":
    main()
