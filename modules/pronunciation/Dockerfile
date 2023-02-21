FROM debian:11

ENV PATH="/root/miniconda3/bin:$PATH"

RUN apt-get update -yqq && apt-get install -y curl bzip2 && rm -rf /var/lib/apt/lists/*

RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba \
    && cp bin/micromamba /usr/bin/

# RUN conda create -y -c conda-forge --name captini \
#     python=3.10 \
#     pysoundfile \
#     kaldi \
#     dtw-python \
#     transformers \
#     scipy

WORKDIR /app
COPY environment.yml environment.yml
RUN micromamba env create -f environment.yml -n captini -c conda-forge

COPY . .
ENV TRANSFORMERS_CACHE=/cache
ENTRYPOINT ["bash", "-c", "micromamba activate captini && python connector.py"]
