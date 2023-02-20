FROM debian:11

ENV PATH="/root/miniconda3/bin:$PATH"

RUN apt-get update -yqq && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh

# RUN conda create -y -c conda-forge --name captini \
#     python=3.10 \
#     pysoundfile \
#     kaldi \
#     dtw-python \
#     transformers \
#     scipy

WORKDIR /app
COPY environment.yml environment.yml
RUN conda env create -f environment.yml -n captini

COPY . .
ENV TRANSFORMERS_CACHE=/cache
ENTRYPOINT ["bash", "-c", ". activate captini && python connector.py"]
