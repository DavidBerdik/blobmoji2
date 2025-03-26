FROM ubuntu:latest

ENV PATH="$PATH:/harfbuzz/build/util"

RUN apt-get update && apt-get install -y python3 python-is-python3 python3-pip python3-venv git meson pkg-config ragel gtk-doc-tools gcc g++ libfreetype6-dev libglib2.0-dev libcairo2-dev zopfli imagemagick \
	&& apt-get clean && rm -f /var/lib/apt/lists/*_* \
	&& pip install notofonttools --no-cache-dir --break-system-packages \
	&& mkdir /output \
	&& git clone https://github.com/harfbuzz/harfbuzz.git \
	&& cd harfbuzz \
	&& meson build && ninja -Cbuild && meson test -Cbuild

ADD . /blobmoji
WORKDIR /blobmoji
CMD ./full_rebuild.sh
