#!/usr/bin/python

from app import app
import yaml



y = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )


if __name__ == '__main__':
	IP 		= y['Kuiper']['IP']
	PORT 	= y['Kuiper']['PORT']
	debug 	= y['Kuiper']['Debug']
	app.run(IP,PORT, debug=debug)
