# OCRmyPDF on web

A Streamlit-based web interface for OCRmyPDF.

To build and run the Docker container:

```bash
docker build -t ocr-pdf-web .
docker run --name ocr-pdf-web-app -d --rm -p 8502:8502 ocr-pdf-web
```

Once the container is running, navigate to `http://localhost:8502`
