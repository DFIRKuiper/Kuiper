FROM docker.elastic.co/elasticsearch/elasticsearch-oss:7.8.1


RUN yum -y update
RUN yum -y install python3 python3-pip 
RUN pip3 install --upgrade pip

RUN pip3 install requests
RUN pip3 install psutil
RUN pip3 install elasticsearch==7.6.0

RUN yum install -y cronie 

COPY ./system_health/ /system_health/

COPY ./system_health/crontabs/crontab.es /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN crontab /etc/cron.d/crontab
RUN touch /var/log/cron_es.log


CMD crond && /tini -- /usr/local/bin/docker-entrypoint.sh eswrapper