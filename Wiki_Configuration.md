
# Configuration


All configuration for Kuiper plased in one single file named **configuration.yaml** to be more straight forward as seen below.

The following section of the configuration file is responsible for setting the parameters for Flask web application. 
by default Kuiper will use the IP address 0.0.0.0 and port 5000 for the web application

~~~yaml
...
# ============ Kuiper Platform
Kuiper:
  IP    : 0.0.0.0
  PORT  : 5000
  Debug : True   # enable debugging mode
...
~~~

The following section of the configuration file is responsible for setting the parameters for celery based on redis configurations. 

~~~yaml
...
# ============ configuration of celery
CELERY:
  CELERY_BROKER_URL     : redis://localhost:6379
  CELERY_RESULT_BACKEND : redis://localhost:6379
  CELERY_TASK_ACKS_LATE : True
...
~~~

The following section of the configuration file is responsible for setting the parameters for the elasticsearch database. 
by default it will use the IP address 127.0.0.1 and port 9200

~~~yaml
...
# ============ Elasticsearch
ElasticSearch:
  IP    : 127.0.0.1
  PORT  : 9200
...
~~~
