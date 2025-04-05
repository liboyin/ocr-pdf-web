FROM jbarlow83/ocrmypdf:latest

ARG APT_PROXY
ARG PYPI_PROXY

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONFAULTHANDLER=1

COPY --chown=ubuntu . /workspaces/ocr-pdf-web
WORKDIR /workspaces/ocr-pdf-web

RUN ./docker_apt_install.sh
USER ubuntu
RUN ./docker_pip_install.sh

EXPOSE 8502
# streamlit run app.py --server.port 8502 --server.address 0.0.0.0 --browser.gatherUsageStats false
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port", "8502", "--server.address", "0.0.0.0", "--browser.gatherUsageStats", "false"]
