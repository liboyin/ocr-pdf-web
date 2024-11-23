import subprocess
import tempfile

import streamlit as st


def main():
    """Streamlit app entry point."""
    st.title("OCRmyPDF Web Portal")
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    rotate_pages = st.checkbox("--rotate-pages", help="Fix a document that contains a mix of landscape and portrait pages")
    deskew = st.checkbox("--deskew", help="Rotate pages so that text is horizontal")
    clean = st.checkbox("--clean", help="Clean up pages before OCR, but does not alter the final output. Disables --clean-final")
    clean_final = st.checkbox("--clean-final", help="Clean up pages before OCR and inserts the page into the final output. Disables --clean")
    redo_ocr = st.checkbox("--redo-ocr", help="Redo OCR on an OCRed file")
    optimize_n = st.slider("--optimize N", min_value=0, max_value=3, value=1, help="Reduce the output PDF file size. 0 to perform lossless optimizations; 3 for most aggressive optimization")

    if st.button("Process", disabled=not uploaded_file):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as input_file, tempfile.NamedTemporaryFile(suffix=".pdf") as output_file:
            input_file.write(uploaded_file.read())
            input_file.flush()
            flags = {
                "--rotate-pages": rotate_pages,
                "--deskew": deskew,
                "--clean": clean,
                "--clean-final": clean_final,
                "--redo-ocr": redo_ocr,
            }
            cmd = ["ocrmypdf"] + [flag for flag, enabled in flags.items() if enabled]
            cmd.extend(["--optimize", str(optimize_n), input_file.name, output_file.name])

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
