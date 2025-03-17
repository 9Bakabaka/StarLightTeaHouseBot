FROM alpine:latest

LABEL maintainer="kongbaixx@outlook.com"

# 使用 apk 安装 Python3 和 pip
RUN apk update && apk add --no-cache \
    python3 \
    py3-pip \
    gcc \
    python3-dev \
    musl-dev \
    linux-headers

# 设置工作目录
WORKDIR /app

# 复制 main.py 到镜像中的 /app 目录
COPY ./main.py /app/main.py
COPY ./notifyAdmin.py /app/notifyAdmin.py
COPY ./docker_requirements.txt /app/requirements.txt
COPY ./bottoken /app/bottoken

# 创建并激活虚拟环境
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# 安装 requirements.txt 中的 Python 包
RUN pip3 install --no-cache-dir -r requirements.txt

# 启动时执行 python3 main.py
CMD ["python3", "main.py"]