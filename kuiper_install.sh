#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
LOGFILE_DIR="$(cat configuration.yaml | grep "Logs:" -A 8 | grep "log_folder:" | awk '/log_folder:/{print $2}' )"
LOGFILE_INSTALL="$LOGFILE_DIR$(cat configuration.yaml | grep "Logs:" -A 8 | grep "install_log:" | awk '/install_log:/{print $2}' )"
LOGFILE_ACCESS_LOG="$LOGFILE_DIR$(cat configuration.yaml | grep "Logs:" -A 8 | grep "access_log:" | awk '/access_log:/{print $2}' )"
LOGFILE_APP_LOG="$LOGFILE_DIR$(cat configuration.yaml | grep "Logs:" -A 8 | grep "app_log:" | awk '/app_log:/{print $2}' )"
LOGFILE_CELERY_LOG="$LOGFILE_DIR$(cat configuration.yaml | grep "Logs:" -A 8 | grep "celery_log:" | awk '/celery_log:/{print $2}' )"
LOGFILE_GUNICORN_PID="$LOGFILE_DIR$(cat configuration.yaml | grep "Logs:" -A 8 | grep "gunicorn_pid:" | awk '/gunicorn_pid:/{print $2}' )"



GUNICORN_IP="$(cat configuration.yaml | grep "Gunicorn:" -A 2 | grep "IP:" | awk '/IP:/{print $2}')"
GUNICORN_PORT="$(cat configuration.yaml | grep "Gunicorn:" -A 2 | grep "PORT:" | awk '/PORT:/{print $2}')"
GUNICORN_THREADS="$(cat configuration.yaml | grep "Gunicorn:" -A 4 | grep "Threads:" | awk '/Threads:/{print $2}' )"
GUNICORN_WORKER_CLASS="$(cat configuration.yaml | grep "Gunicorn:" -A 4 | grep "worker_class:" | awk '/worker_class:/{print $2}' )"
GUNICORN_TIMEOUT="$(cat configuration.yaml | grep "Gunicorn:" -A 5 | grep "timeout:" | awk '/timeout:/{print $2}' )"
GUNICORN_WORKERS="$(cat configuration.yaml | grep "Gunicorn:" -A 6 | grep "workers:" | awk '/workers:/{print $2}' )"
GUNICORN_SSL_KEY="$(cat configuration.yaml | grep "Gunicorn:" -A 8 | grep "cert_key:" | awk '/cert_key:/{print $2}' )"
GUNICORN_SSL_CERT="$(cat configuration.yaml | grep "Gunicorn:" -A 8 | grep "cert_cert:" | awk '/cert_cert:/{print $2}' )"


CELERY_WORKER_NAME="$(cat configuration.yaml | grep "CELERY:" -A 5 | grep "CELERY_WORKER_NAME:" | awk '/CELERY_WORKER_NAME:/{print $2}' )"

# create the logs files
mkdir -p $LOGFILE_DIR
touch $LOGFILE_INSTALL
touch $LOGFILE_ACCESS_LOG
touch $LOGFILE_APP_LOG
touch $LOGFILE_CELERY_LOG
touch $LOGFILE_GUNICORN_PID



usage="$(basename "$0") [command] -- Kuiper Anaylsis framework
where:
    -install            installs all dependencies and requirements
    -run                run's Kuiper
    -stop               stop kuiper processes (celery and gunicorn)
    -w_restart          Restart Gunicorn workers
    -update             Update Kuiper (run the script Kuiper-update.py)
    -restart_service    Restart the provided service
    -h                  show this help message"

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
    apt install -y  python-minimal python3 python-dev>> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install Python (Error Code: $ERROR)."
        fi


    echo "Installing Python pip2"
    apt install -y python-pip  >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install pip (Error Code: $ERROR)."
        fi
    echo "Upgrading pip"

    pip install --upgrade pip && hash -d pip >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install pip (Error Code: $ERROR)."
        fi


    echo "Installing dependencies"
    apt-get install -y build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Python dependencies failed (Error Code: $ERROR)."
        fi

    yes 2>/dev/null |pip2 install -r "$DIR/requirements_2.7.txt"  >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Requirements failed (Error Code: $ERROR)."
        fi

    echo "Installing Python pip3"
    apt install -y python3-pip  >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install pip (Error Code: $ERROR)."
        fi
    echo "Upgrade Python pip3"
    python3 -m pip install --upgrade pip  >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install pip (Error Code: $ERROR)."
        fi

    echo "Installing requirements"
    yes 2>/dev/null | python3 -m pip install -r "$DIR/requirements_3.txt"  >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Requirements failed (Error Code: $ERROR)."
        fi
    # *********** Installing redis ***************
    echo "Installing redis"
    apt-get install -y redis-server >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install redis (Error Code: $ERROR)."
        fi

    systemctl enable redis-server.service >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not enable redis service (Error Code: $ERROR)."
        fi

    # *********** Installing Elasticsearch ***************
    echo "Installing Elasicsearch prerequisite.."

    echo "Installing JDK"

    apt-get install -y openjdk-12-jre >> $LOGFILE_INSTALL 2>&1

    echo "JAVA_HOME=/usr/bin/java" >> /etc/environment 2>&1
    source /etc/environment 2>&1

    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install JDK (Error Code: $ERROR)."
            echo $ERROR
        fi

    wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add - >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not write the public signing key to the host (Error Code: $ERROR)."
        fi


    apt-get install apt-transport-https >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install apt-transport-https (Error Code: $ERROR)."
        fi

    echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not add elastic packages source list definitions to your source list (Error Code: $ERROR)."
        fi

    echo "Installing updates.."
    apt-get update >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install updates (Error Code: $ERROR)."
        fi

    echo "Installing Elasticsearch.."
    apt-get install elasticsearch >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install elasticsearch (Error Code: $ERROR)."
        fi



    echo "Starting elasticsearch and setting elasticsearch to start automatically when the system boots.."
    systemctl daemon-reload >> $LOGFILE_INSTALL 2>&1
    systemctl enable elasticsearch.service >> $LOGFILE_INSTALL 2>&1
    systemctl start elasticsearch.service >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not start elasticsearch and set elasticsearch to start automatically when the system boots (Error Code: $ERROR)."
        fi



    # *********** Installing MongoDB ***************
    echo "Installing MongoDB prerequisite.."
    wget -qO - https://www.mongodb.org/static/pgp/server-4.2.asc | sudo apt-key add - >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not write the public signing key to the host (Error Code: $ERROR)."
        fi

    echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/4.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.2.list>> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not write the public signing key to the host (Error Code: $ERROR)."
        fi

    apt-get update >> $LOGFILE_INSTALL 2>&1
    ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Could not install updates (Error Code: $ERROR)."
        fi

    echo "Installing MongoDB "
    apt-get install -y mongodb-org >> $LOGFILE_INSTALL 2>&1
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
    systemctl daemon-reload >> $LOGFILE_INSTALL 2>&1
    systemctl enable mongodb >> $LOGFILE_INSTALL 2>&1
    systemctl stop mongodb >> $LOGFILE_INSTALL 2>&1
    systemctl restart mongodb >> $LOGFILE_INSTALL 2>&1
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
    
    CURRENT_DATE=$(date -Isecond -u | awk -F '+' '{print $1}')
    echo "Moving old logs to folder ./logs/$CURRENT_DATE"
    mkdir "./logs/$CURRENT_DATE"
    find ./logs/ -maxdepth 1 -type f -exec mv {} "./logs/$CURRENT_DATE" \;

    echo "Set JVM configuration"
    REQUIRE_RESTART_ES=false
    MEMORY_SIZE="$( expr $(cat /proc/meminfo  | grep "MemTotal" | awk '{print $2}') / 2 / 1024 / 1024)"

    
    XMS_OPTIONS="$(sudo grep "^\-Xms" /etc/elasticsearch/jvm.options)"
    XMX_OPTIONS="$(sudo grep "^\-Xmx" /etc/elasticsearch/jvm.options)"

    if [ "$XMS_OPTIONS" != "-Xms${MEMORY_SIZE}g" ]; then
        echo "Changing ${XMS_OPTIONS} to -Xms${MEMORY_SIZE}g"
        sudo sed -ri "s/-Xms.?g/-Xms$(echo $MEMORY_SIZE)g/g" /etc/elasticsearch/jvm.options
        REQUIRE_RESTART_ES=true
    fi

    if [ "$XMX_OPTIONS" != "-Xmx${MEMORY_SIZE}g" ]; then
        echo "Changing ${XMX_OPTIONS} to -Xmx${MEMORY_SIZE}g"
        sudo sed -ri "s/-Xmx.?g/-Xmx$(echo $MEMORY_SIZE)g/g" /etc/elasticsearch/jvm.options
        REQUIRE_RESTART_ES=true
    fi

    if [ "$REQUIRE_RESTART_ES" = true ]; then
        echo "Restarting elasticsearch service..."
        sudo service elasticsearch restart
    fi

    
    echo "Running Celery"
    celery worker -A app.celery_app --loglevel=info --logfile=$LOGFILE_CELERY_LOG --hostname="$CELERY_WORKER_NAME" &

    echo -e "Gunicorn configuration: 
        THREADS\t\t[$GUNICORN_THREADS] 
        WORKER_CLASS\t[$GUNICORN_WORKER_CLASS] 
        TIMEOUT\t\t[$GUNICORN_TIMEOUT]"
    echo "Running Kuiper"
    nohup gunicorn --bind $GUNICORN_IP:$GUNICORN_PORT Kuiper:app --worker-class $GUNICORN_WORKER_CLASS --workers=$GUNICORN_WORKERS --threads=$GUNICORN_THREADS -p $LOGFILE_GUNICORN_PID --timeout=$GUNICORN_TIMEOUT --access-logfile $LOGFILE_ACCESS_LOG --certfile $GUNICORN_SSL_CERT --keyfile $GUNICORN_SSL_KEY >> $LOGFILE_APP_LOG &
    echo "Kuiper can be accessed at https://$GUNICORN_IP:$GUNICORN_PORT/"


# ************* Stopping Kuiper ****************
elif [ "$1" == "-stop" ]; then
    printf "Killing Gunicorn processes ..." 
    while kill -9 $(ps aux | grep "gunicorn"| grep -v "grep" | awk '{print $2}' | head -1) 2> /dev/null; do 
        sleep 1
    done 
    printf "done\n"
    printf "Killing Celery processes ..."
    while kill -9 $(ps aux | grep "celery"| grep -v "grep"  | awk '{print $2}') 2> /dev/null; do
        sleep 1
    done
    printf "done\n"
    printf "Killing ./kuiper_install.sh -run ..."
    while kill -9 $(ps aux | grep "./kuiper_install.sh"| grep -v "grep" | awk '{print $2}') 2> /dev/null; do
        sleep 1
    done
    printf "done\n"

# ************* Starting Gunicorn workers ****************
elif [ "$1" == "-w_restart" ]; then
    echo "Restart Gunicorn workers [PID:$(cat $LOGFILE_GUNICORN_PID)]" 
    kill -HUP "$(cat $LOGFILE_GUNICORN_PID)"


# ************* Restart service ****************
elif [ "$1" == "-restart_service" ]; then
    if [ $# -eq 2 ] 
        then
            echo "[+] Restart the service $2"
            sudo -S systemctl restart $2
            echo "[+] Service restarted"
    else 
        echo "[-] Error: you need to provide the service name"

    fi


# ************* Kuiper update ****************
elif [ "$1" == "-update" ]; then
    echo "Update Kuiper:"
    echo "Provided arguments: ${@:2}"
    
    python Kuiper-update.py "${@:2}"
    sleep 4
    echo "Restart Gunicorn workers [PID:$(cat $LOGFILE_GUNICORN_PID)]" 
    kill -HUP "$(cat $LOGFILE_GUNICORN_PID)"

else echo "$usage"


fi
