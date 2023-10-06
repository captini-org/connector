FROM python:3.10

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install --upgrade websockets
COPY . .
RUN apt-get update -yqq && apt-get install -yqq \
    libgraphviz-dev
EXPOSE 3000
# Run python script
CMD ["python", "main.py"]
