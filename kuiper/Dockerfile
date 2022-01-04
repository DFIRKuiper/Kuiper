FROM python:2.7

RUN mkdir -p /app/
WORKDIR /app
RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf

#COPY ./ . 
COPY ./requirements_3.txt ./requirements_3.txt
COPY ./requirements_2.7.txt ./requirements_2.7.txt

RUN apt update -y

RUN apt install -y  python-minimal python3 python-dev libsasl2-dev libldap2-dev libssl-dev python-pip build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev python3-pip cron
RUN pip install --upgrade pip
RUN pip2 install -r "./requirements_2.7.txt"
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r "./requirements_3.txt"
