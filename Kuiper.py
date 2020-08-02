#!/usr/bin/python

from app import app
import yaml


y = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )




if __name__ == '__main__':
    IP		= y['Gunicorn']['IP']
    PORT	= y['Gunicorn']['PORT']
    debug 	= y['Kuiper']['Debug']
    cert_file = y['Gunicorn']['cert_cert']
    cert_key  = y['Gunicorn']['cert_key']
    app.run(IP, PORT , debug=debug, ssl_context=(cert_file, cert_key))
    #app.run(IP, PORT , debug=debug)
    

