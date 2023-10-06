FROM python:3.10

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN apt-get update -yqq && apt-get install -yqq \
    libgraphviz-dev
RUN pip install --upgrade websockets
COPY . .
ENTRYPOINT ["python", "connector.py"]
