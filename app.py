from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from itertools import chain
import subprocess
import tempfile
from typing import Iterable
import zipfile

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

CLEAN = "Clean up pages before OCR, but do not alter the final output"
CLEAN_FINAL = "Clean up pages before OCR and inserts the page into the final output"


@dataclass(frozen=True)
class OcrOptions:
    rotate_pages: bool
    deskew: bool
    clean_option: str
    redo_ocr: bool
    optimize_n: int

    def get_cli_parameters(self) -> list[str]:
        flags: dict[str, bool] = {
            "--rotate-pages": self.rotate_pages,
            "--deskew": self.deskew,
            "--clean": self.clean_option == CLEAN,
            "--clean-final": self.clean_option == CLEAN_FINAL,
            "--redo-ocr": self.redo_ocr,
        }
        result = [flag for flag, enabled in flags.items() if enabled]
        result.append("--optimize")
        result.append(str(self.optimize_n))
        return result


@dataclass(frozen=True)
class OcrResult:
    file_name: str
    return_code: int
    stdout: str
    stderr: str
    output_file_content: bytes


def ocr_single_pdf(uploaded_file: UploadedFile, options: OcrOptions) -> OcrResult:
    """
    Performs OCR on a single PDF file by calling `ocrmypdf` in a subprocess and returns the execution result regardless of success.
    """
    with (tempfile.NamedTemporaryFile(suffix=".pdf") as input_file,
          tempfile.NamedTemporaryFile(suffix=".pdf") as output_file):
        input_file.write(uploaded_file.read())
        input_file.flush()
        cmd: list[str] = list(chain(
            ["ocrmypdf"],
            options.get_cli_parameters(),
            [input_file.name, output_file.name],
        ))
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output_file.seek(0)
        return OcrResult(uploaded_file.name, result.returncode, result.stdout.decode(), result.stderr.decode(), output_file.read())


def ocr_multi_pdf(uploaded_files: Iterable[UploadedFile], options: OcrOptions) -> tuple[list[OcrResult], list[OcrResult]]:
    """
    Performs OCR on multiple PDF files and returns a tuple of successful and failed results.
    """
    successful: list[OcrResult] = []
    failed: list[OcrResult] = []
    for uploaded_file in uploaded_files:
        file_path = uploaded_file.name
        with st.spinner(f"Processing {file_path}..."):
            result = ocr_single_pdf(uploaded_file, options)
            if result.return_code == 0:
                successful.append(result)
            else:
                st.error(f"Failed to process: {file_path}")
                st.code(result.stderr, language="text")
                failed.append(result)
    return successful, failed


def create_zip_buffer(ocr_results: Iterable[OcrResult]) -> BytesIO:
    """
    Creates a ZIP archive buffer from an iterable of successful OCR results.
    """
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for result in ocr_results:
            zip_file.writestr(result.file_name, result.output_file_content)
    buffer.seek(0)
    return buffer


def main() -> None:
    """Streamlit app entry point."""
    st.set_page_config(page_title="OCRmyPDF")
    st.title("OCRmyPDF Web Portal")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)
    rotate_pages = st.checkbox("Fix a mixture of landscape and portrait pages")
    deskew = st.checkbox("Rotate pages so that text is horizontal")
    redo_ocr = st.checkbox("Redo OCR on an OCRed file")
    clean_option = st.radio("Cleanup options", ("Do not clean up", CLEAN, CLEAN_FINAL))
    optimize_n = st.slider("Reduce output PDF file size. 0 for lossless optimization; 3 for most aggressive optimization", min_value=0, max_value=3, value=1)
    if st.button("Process", disabled=not uploaded_files):
        options = OcrOptions(rotate_pages, deskew, clean_option, redo_ocr, optimize_n)
        successful, _ = ocr_multi_pdf(uploaded_files, options)
        st.download_button(
            label="Download",
            data=create_zip_buffer(successful).getvalue(),
            file_name="OCRmyPDF.zip",
            mime="application/zip",
        )


if __name__ == "__main__":
    main()
