#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
LOGFILE="$DIR/Kuiper-install.log"

usage="$(basename "$0") [options] -- Kuiper Anaylsis framework
where:
    -install    installs all dependencies and requirements
    -run        run's Kuiper
    -h          show this help message"

echoerror() {
    printf "${RC} * ERROR${EC}: $@\n" 1>&2;
}

if [ "$1" == "-install" ]; then
    if [ "$EUID" -ne 0 ];then
        echo "Please run as root"
        exit
    fi
    echo "Starting Kuiper installation...."

    # *********** Installing python Requirments ***************
    echo "Installing Python"
    apt install -y  python-minimal python3 python-dev>> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install Python (Error Code: $ERROR)."
        fi


    echo "Installing Python pip2"
    apt install -y python-pip  >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install pip (Error Code: $ERROR)."
        fi
    echo "Upgrading pip"

    pip install --upgrade pip && hash -d pip >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install pip (Error Code: $ERROR)."
        fi


    echo "Installing dependencies"
    apt-get install -y python-libesedb build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Python dependencies failed (Error Code: $ERROR)."
        fi

    yes|pip2 install -r "$DIR/requirements.txt"  >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Requirements failed (Error Code: $ERROR)."
        fi

    echo "Installing Python pip3"
    apt install -y python3-pip  >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install pip (Error Code: $ERROR)."
        fi
    echo "Installing requirements"
    yes|pip3 install -r "$DIR/requirements2.txt"  >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Requirements failed (Error Code: $ERROR)."
        fi
    # *********** Installing redis ***************
    echo "Installing redis"
    apt-get install -y redis-server >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install redis (Error Code: $ERROR)."
        fi

    systemctl enable redis-server.service >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not enable redis service (Error Code: $ERROR)."
        fi

    # *********** Installing Elasticsearch ***************
    echo "Installing Elasicsearch prerequisite.."

    echo "Installing JDK"

    apt-get install -y openjdk-8-jre >> $LOGFILE 2>&1

    echo "JAVA_HOME=/usr/bin/java" >> /etc/environment 2>&1
    source /etc/environment 2>&1

    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install JDK (Error Code: $ERROR)."
            echo $ERROR
        fi

    wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add - >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not write the public signing key to the host (Error Code: $ERROR)."
        fi


    apt-get install apt-transport-https >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install apt-transport-https (Error Code: $ERROR)."
        fi

    echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-6.x.list >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not add elastic packages source list definitions to your source list (Error Code: $ERROR)."
        fi

    echo "Installing updates.."
    apt-get update >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install updates (Error Code: $ERROR)."
        fi

    echo "Installing Elasticsearch.."
    apt-get install elasticsearch >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install elasticsearch (Error Code: $ERROR)."
        fi



    echo "Starting elasticsearch and setting elasticsearch to start automatically when the system boots.."
    systemctl daemon-reload >> $LOGFILE 2>&1
    systemctl enable elasticsearch.service >> $LOGFILE 2>&1
    systemctl start elasticsearch.service >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not start elasticsearch and set elasticsearch to start automatically when the system boots (Error Code: $ERROR)."
        fi



    # *********** Installing MongoDB ***************
    echo "Installing MongoDB prerequisite.."
    wget -qO - https://www.mongodb.org/static/pgp/server-4.2.asc | sudo apt-key add - >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not write the public signing key to the host (Error Code: $ERROR)."
        fi

    echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/4.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.2.list>> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not write the public signing key to the host (Error Code: $ERROR)."
        fi

    apt-get update >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install updates (Error Code: $ERROR)."
        fi

    echo "Installing MongoDB "
    apt-get install -y mongodb-org >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install MongoDB (Error Code: $ERROR)."
        fi

    echo "Starting MongoDB and setting MongoDB to start automatically when the system boots.."
    echo "[Unit]
    Description=MongoDB Database
    After=network.target

    [Service]
    User=mongodb
    ExecStart=/usr/bin/mongod --quiet --config /etc/mongod.conf

    [Install]
    WantedBy=multi-user.target" > /etc/systemd/system/mongodb.service
    systemctl daemon-reload >> $LOGFILE 2>&1
    systemctl enable mongodb >> $LOGFILE 2>&1
    systemctl stop mongodb >> $LOGFILE 2>&1
    systemctl restart mongodb >> $LOGFILE 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not start MongoDB and set MongoDB to start automatically when the system boots (Error Code: $ERROR)."
        fi


    echo "**********************************************************************************************************"
    echo " "
    echo "All Kuiper prerequisite has been installed"
    echo " "
    echo "**********************************************************************************************************"

# *********** Running Kuiper ***************
elif [ "$1" == "-run" ]; then

    echo "Running Kuiper!"
    echo "Kuiper can be accessed at http://[configuredIP]:5000"
    nohup python Kuiper.py >> "$DIR/Kuiper-flask.log" &
    celery worker -A app.celery --loglevel=info --logfile="$DIR/Kuiper-celery.log" &

else echo "$usage"


fi
