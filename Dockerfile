FROM python:3.8-bullseye

USER root

ARG VIPS_VERSION=8.12.2
ARG VIPS_URL=https://github.com/libvips/libvips/releases/download
ARG OPENJPEG_VERSION=2.4.0
ARG OPENJPEG_URL=https://github.com/uclouvain/openjpeg/archive

RUN apt-get -y update \
	&& apt-get -y install \
		build-essential \
		pkg-config \
		wget 

RUN apt-get -y install \
	glib2.0-dev \
	libexif-dev \
	libexpat1-dev \
	libfftw3-dev \
	libgsf-1-dev \
	libimagequant-dev \
	liblcms2-dev \
	libmagickcore-dev \
	libopenjp2-7-dev \
	liborc-0.4-dev \
	libpng-dev \
	librsvg2-dev \
	libtiff5-dev \
	libopenjp2-tools \
	time

WORKDIR /usr/local/src

ENV LD_LIBRARY_PATH /lib:/usr/lib:/usr/local/lib

#RUN wget ${OPENJPEG_URL}/v${OPENJPEG_VERSION}.tar.gz \
#	&& tar xf v${OPENJPEG_VERSION}.tar.gz \ 
#	&& rm v${OPENJPEG_VERSION}.tar.gz  \
#	&& cd openjpeg-${OPENJPEG_VERSION} \ 
#	&& mkdir -v build \
#	&& cd build \
#	&& cmake .. -DCMAKE_BUILD_TYPE=Release \
#	&& make \
#	&& make install

RUN wget ${VIPS_URL}/v${VIPS_VERSION}/vips-${VIPS_VERSION}.tar.gz \
	&& tar xf vips-${VIPS_VERSION}.tar.gz \
	&& cd vips-${VIPS_VERSION} \
	&& ./configure \
	&& make -j V=0 \
	&& make install


COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt


# configure the container to run in an executed manner
CMD ["python", "app.py" ]
