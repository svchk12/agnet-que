FROM python:3.11

WORKDIR /app

# 시스템 패키지 설치 및 업데이트
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 비루트 사용자 생성
RUN groupadd -r python && \
    useradd -r -g python python

# 가상환경 생성 및 활성화
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install google-adk

# 애플리케이션 파일 복사 및 권한 설정
COPY . .
RUN chown -R python:python /app

# 비루트 사용자로 전환
USER python

EXPOSE 8001

CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8001"] 