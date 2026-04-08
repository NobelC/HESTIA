FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

# Herramientas base + C++20 + Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake pkg-config git sudo curl wget \
    gcc-13 g++-13 clang-18 clangd \
    python3.12 python3.12-venv python3-pip python3.12-dev \
    neovim locales less man-db \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 100 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 100 \
    && locale-gen en_US.UTF-8 && update-locale LANG=en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# Entorno Python
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# LSPs Python
RUN pip install python-lsp-server "pylsp[all]" pyright

# Crear usuario dev
RUN useradd -m -s /bin/bash dev && echo "dev:dev" | chpasswd
RUN echo "dev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER dev
WORKDIR /workspace

# Copiar script de inicialización
COPY .devcontainer/setup.sh /home/dev/setup.sh
RUN chmod +x /home/dev/setup.sh
