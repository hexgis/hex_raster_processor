# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-buster

LABEL maintainer="Hexgis <contato@hexgis.com>"

ENV APP_HOME /app
WORKDIR $APP_HOME

# Removes output stream buffering, allowing for more efficient logging
ENV PYTHONUNBUFFERED 1
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal

# Install system requirements
RUN apt-get update -y
RUN apt-get install -y \
    build-essential \
    libgnutls28-dev \
    python3-setuptools \
    python3-pip \
    python-dev \
    python-pil \
    python-gdal \
    libgdal-dev \
    gdal-bin \
    dans-gdal-scripts \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install setuptools==57.5.0
RUN pip uninstall gdal -y
RUN pip install numpy gdal==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"

# Install dependencies
COPY requirements_dev.txt .
RUN pip install --no-cache-dir -r requirements_dev.txt

# Adding permissions to tilers-tools package
# RUN chmod +x /usr/local/lib/python3.9/site-packages/raster_processor/tilers-tools/*.py
