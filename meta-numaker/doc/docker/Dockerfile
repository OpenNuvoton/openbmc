FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install essential Yocto/OpenBMC host packages
# Reference: https://github.com/OpenNuvoton/MA35D1_Docker_Script
# Additional: OpenBMC build dependencies (gawk, diffstat, chrpath, zstd, lz4, etc.)
RUN apt-get update && apt-get install -y \
        gawk \
        wget \
        git \
        git-lfs \
        diffstat \
        unzip \
        texinfo \
        gcc-multilib \
        build-essential \
        chrpath \
        socat \
        cpio \
        file \
        bzip2 \
        zstd \
        lz4 \
        curl \
        lzop \
        u-boot-tools \
        sudo \
        locales \
        bc \
        libncurses5-dev \
        flex \
        bison \
        device-tree-compiler \
        libssl-dev \
        net-tools \
        libyaml-dev \
        rsync \
        python3 \
        python3-pip \
        iputils-ping \
        jq \
        xz-utils \
        debianutils \
        iproute2 \
        libelf-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for NuWriter
RUN pip3 install --no-cache-dir --break-system-packages \
        pyusb \
        ecdsa \
        crcmod \
        tqdm \
        pycryptodome \
        pycryptodomex \
        pyelftools

# Set locale
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && echo 'LANG="en_US.UTF-8"' > /etc/default/locale \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG=en_US.UTF-8

ENV LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8

# Create non-root build user (Yocto refuses to run as root)
RUN useradd --uid 30000 --create-home build \
    && echo "build ALL=(ALL) NOPASSWD: ALL" | tee -a /etc/sudoers

USER build
WORKDIR /home/build
CMD ["/bin/bash"]
