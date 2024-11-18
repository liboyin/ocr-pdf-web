# docker build -t ocr-streamlit-app .
# docker run -p 8501:8501 ocr-streamlit-app
FROM jbarlow83/ocrmypdf:latest
RUN apt-get update && apt-get install -y --no-install-recommends python3-pip
RUN pip install streamlit
COPY app.py /app.py
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "/app.py"]
