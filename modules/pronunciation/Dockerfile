FROM debian:11

RUN apt-get update -yqq && apt-get install -y curl bzip2 && rm -rf /var/lib/apt/lists/*

RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba \
    && cp bin/micromamba /usr/bin/

WORKDIR /app
COPY environment.yml environment.yml
RUN micromamba env create -f environment.yml -n captini -c conda-forge

COPY . .
ENV TRANSFORMERS_CACHE=/cache
ENTRYPOINT ["bash", "-c", "micromamba run -n captini python connector.py"]
