# OCRmyPDF on web

A Streamlit-based web interface for OCRmyPDF.

To build and run the Docker container:

```bash
docker build -t ocr-pdf-web .
docker run -p 8501:8501 ocr-pdf-web
```

Once the container is running, navigate to `http://localhost:8501`
