FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    cmake \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/root/.deno/bin:${PATH}"

# whisper-cpp local — Transcrição Local do painel (não usado pelo pipeline principal,
# que continua na Groq Whisper API via transcriber.py)
RUN git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git /opt/whisper.cpp \
    && cmake -B /opt/whisper.cpp/build -S /opt/whisper.cpp -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /opt/whisper.cpp/build -j --config Release \
    && bash /opt/whisper.cpp/models/download-ggml-model.sh small /opt/whisper.cpp/models

ENV WHISPER_CPP_BIN=/opt/whisper.cpp/build/bin/whisper-cli
ENV WHISPER_MODEL_PATH=/opt/whisper.cpp/models/ggml-small.bin

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

CMD ["python", "-m", "src.main"]
