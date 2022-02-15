FROM python:3.8-alpine

USER root

ARG VIPS_VERSION=8.12.2
ARG VIPS_URL=https://github.com/libvips/libvips/releases/download
ARG OPENJPEG_VERSION=2.4.0
ARG OPENJPEG_URL=https://github.com/uclouvain/openjpeg/archive

RUN apk update && apk upgrade

RUN apk add \
    build-base \
	cmake \
	autoconf \
	automake \
	libtool \
	bc \
	zlib-dev \
	libxml2-dev \
	jpeg-dev \
	tiff-dev \
	glib-dev \
	gdk-pixbuf-dev \
	sqlite-dev \
	libjpeg-turbo-dev \
	libexif-dev \
	lcms2-dev \
	fftw-dev \
	giflib-dev \
	libpng-dev \
	libwebp-dev \
	orc-dev \
	poppler-dev \
	librsvg-dev \
	libgsf-dev \
	openexr-dev \
	gtk-doc

WORKDIR /usr/local/src

RUN wget ${OPENJPEG_URL}/v${OPENJPEG_VERSION}.tar.gz \
	&& tar xf v${OPENJPEG_VERSION}.tar.gz \ 
	&& rm v${OPENJPEG_VERSION}.tar.gz  \
	&& cd openjpeg-${OPENJPEG_VERSION} \ 
	&& mkdir -v build \
	&& cd build \
	&& cmake .. -DCMAKE_BUILD_TYPE=Release \
	&& make \
	&& make install

RUN wget ${VIPS_URL}/v${VIPS_VERSION}/vips-${VIPS_VERSION}.tar.gz \
	&& tar xf vips-${VIPS_VERSION}.tar.gz \
	&& cd vips-${VIPS_VERSION} \
	&& ./configure \
	&& make V=0 \
	&& make install


COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

# copy every content from the local file to the image
COPY . /app

# configure the container to run in an executed manner
ENTRYPOINT [ "python" ]

CMD ["app.py" ]