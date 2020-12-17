FROM ubuntu:20.04

ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
  python3 \
  python3-distutils \
  qpdf \
  ca-certificates \
  curl 
    
# Get the latest pip (Ubuntu version doesn't support manylinux2010)
RUN \
  curl https://bootstrap.pypa.io/get-pip.py | python3


# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app
COPY . /app

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "watcher.py"]
