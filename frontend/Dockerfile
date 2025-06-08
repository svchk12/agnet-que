FROM node:20

WORKDIR /app

# 보안 취약점 스캔을 위한 패키지 업데이트
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 비루트 사용자 생성 및 권한 설정
RUN groupadd -r nodejs && \
    useradd -r -g nodejs -m nodejs && \
    mkdir -p /home/nodejs/.npm && \
    chown -R nodejs:nodejs /home/nodejs

# 애플리케이션 파일 복사 및 권한 설정
COPY package*.json ./
RUN npm install
COPY . .
RUN chown -R nodejs:nodejs /app

# 비루트 사용자로 전환
USER nodejs

ENV FAST_REFRESH=false
ENV WATCHPACK_POLLING=true

EXPOSE 3000

CMD ["npm", "start"] 