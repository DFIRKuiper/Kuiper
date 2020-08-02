
#import views
from flask import Flask

import os 
import yaml


y = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )

