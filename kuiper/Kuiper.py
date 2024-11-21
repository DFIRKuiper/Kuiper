#!/usr/bin/python

from app import app
import yaml
import os 

y = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )



if __name__ == '__main__':
    IP		= os.getenv('FLASK_IP', y['Gunicorn']['IP'])  
    PORT	= os.getenv('FLASK_PORT', y['Gunicorn']['PORT']) 
    debug 	= os.getenv('FLASK_DEBUG', y['Kuiper']['Debug']).lower() in ("yes", "y", "true",  "t", "1")
    app.run(host=IP, port=int(PORT) , debug=debug)
    #app.run(IP, PORT , debug=debug)
    

