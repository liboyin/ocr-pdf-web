from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from itertools import chain
from pathlib import Path
import subprocess
import tempfile
from typing import Iterable
import zipfile

from PIL.Image import Image
from pdf2image import convert_from_bytes
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
                st.error(f"OCRmyPDF failed to process {file_path} with error code {result.return_code}")
                st.code(f"stdout:\n{result.stdout.decode()}\nstderr:\n{result.stderr.decode()}", language="text")
                failed.append(result)
    return successful, failed


def create_ocr_zip_buffer(ocr_results: Iterable[OcrResult]) -> BytesIO:
    """
    Creates a ZIP archive buffer from an iterable of successful OCR results.
    """
    with st.spinner("Creating ZIP archive..."):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            for result in ocr_results:
                zip_file.writestr(result.file_name, result.output_file_content)
        buffer.seek(0)
        return buffer


def save_image_file(image: Image, dir_path: Path, source_file_name: str, page_number: int, image_format: str, quality: int) -> Path:
    """
    Saves a PIL Image in the specified directory with the given format and (if JPEG) quality.
    """
    file_path = dir_path / f"{source_file_name}.page_{page_number}.{image_format.lower()}"
    match image_format.lower():
        case 'jpeg':
            image.save(file_path, 'JPEG', quality=quality)
        case 'png':
            image.save(file_path, 'PNG')
        case _:
            raise ValueError(f"Unexpected image format: {image_format}")
    return file_path


def extract_images_from_multi_pdf(uploaded_files: Iterable[UploadedFile], dpi: int) -> dict[str, list[Image]]:
    """
    Extracts pages as images from multiple PDF files using pdf2image and returns a dictionary with PDF file names as keys and lists of PIL Image objects as values.
    """
    results = {}
    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        with st.spinner(f"Processing {filename}..."):
            try:
                results[filename] = convert_from_bytes(uploaded_file.read(), dpi=dpi)
            except Exception as e:
                st.error(f"Failed to extract images from {filename}: {e}")
                continue
    return results


def create_images_zip_buffer(extraction: dict[str, list[Image]], image_format: str, quality: int) -> BytesIO:
    """
    Creates a ZIP archive buffer containing extracted images from PDF files.
    """
    with st.spinner("Creating ZIP archive..."):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            for file_name, images in extraction.items():
                for i, img in enumerate(images):
                    file_paths.append(save_image_file(img, Path(temp_dir), Path(file_name).stem, i + 1, image_format, quality))
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in file_paths:
                    zip_file.write(file_path, file_path.name)
            zip_buffer.seek(0)
            return zip_buffer


def main() -> None:
    """Streamlit app entry point."""
    st.set_page_config(page_title="OCRmyPDF")
    st.title("OCRmyPDF Web Portal")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)
    st.session_state.result = b''
    with st.form(key="ocr"):
        rotate_pages = st.checkbox("Fix a mixture of landscape and portrait pages")
        deskew = st.checkbox("Rotate pages so that text is horizontal")
        redo_ocr = st.checkbox("Redo OCR on an OCRed file")
        clean_option = st.radio("Cleanup options", ("Do not clean up", CLEAN, CLEAN_FINAL))
        optimize_n = st.slider("Reduce output PDF file size. 0 for lossless optimization; 3 for most aggressive optimization", min_value=0, max_value=3, value=1)
        if st.form_submit_button("OCR"):
            options = OcrOptions(rotate_pages, deskew, clean_option, redo_ocr, optimize_n)
            st.session_state.result = create_ocr_zip_buffer(ocr_multi_pdf(uploaded_files, options)[0])
    with st.form("extract"):
        col1, col2, col3 = st.columns(3)
        with col1:
            dpi = st.number_input("DPI", min_value=72, max_value=1200, value=200)
        with col2:
            image_format = st.selectbox("Image Format", ["JPEG", "PNG"])
        with col3:
            quality = st.number_input("JPEG Quality", min_value=1, max_value=100, value=95)
        if st.form_submit_button("Extract"):
            st.session_state.result = create_images_zip_buffer(extract_images_from_multi_pdf(uploaded_files, dpi), image_format, quality)
    st.download_button(
        label="Download",
        disabled=not st.session_state.result,
        data=st.session_state.result,
        file_name=f"OCRmyPDF.{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip",
    )


if __name__ == "__main__":
    main()
