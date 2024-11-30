FROM jbarlow83/ocrmypdf:latest

ARG APT_PROXY=http://192.168.0.4:3142
ARG PYPI_PROXY=http://192.168.0.4:3141/root/pypi/+simple/
ENV DEBIAN_FRONTEND=noninteractive

COPY . /workspaces/ocr-pdf-web
WORKDIR /workspaces/ocr-pdf-web

RUN ./docker_apt_install.sh
RUN ./docker_pip_install.sh

EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
