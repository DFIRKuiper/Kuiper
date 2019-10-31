
import subprocess
import json
from bson.json_util import dumps
import os
import shutil
import zipfile
import urllib
import yaml 

from flask import request, redirect, render_template, url_for, flash,send_from_directory,session
from flask import jsonify
from app import app

from werkzeug.utils import secure_filename

from app.database.elkdb import *
from app.database.dbstuff import *



# get configuration
y = yaml.load( open( 'configuration.yaml' , 'r' ) , Loader=yaml.FullLoader )


SIDEBAR = {
    "sidebar"   : y['admin_sidebar'],
    "open"      : app.config['SIDEBAR_OPEN']
}


# =================================================
#               Helper Functions
# =================================================
# return json in a beautifier
def json_beautifier(js):
    return json.dumps(js, indent=4, sort_keys=True)


# unzip files and store it on dst_path
def unzip_file(zip_path,dst_path):
    try:
        zip_ref = zipfile.ZipFile(zip_path, 'r')
        zip_ref.extractall(dst_path)
        zip_ref.close()

        return True
    except:
        return False



# list all files in the zip_path
def list_zip_file(zip_path):
    zip_ref = zipfile.ZipFile(zip_path, 'r')
    zip_content = []
    for z in zip_ref.infolist() :
        zip_content.append(z.filename)
    return zip_content



# =================================================
#               Flask Functions
# =================================================


# =================== Cases =======================
#call admin page will all content from content_management
@app.route('/admin/')
def home_page():

    # check messages or errors 
    message = None if 'message' not in request.args else request.args['message']
    err_msg = None if 'err_msg' not in request.args else request.args['err_msg']

    all_caces = db_cases.get_cases()
    if all_caces[0]:
        return render_template('admin/display_cases.html',SIDEBAR=SIDEBAR,all_caces=all_caces[1] , page_header="Cases" , message = message , err_msg=err_msg)
    else:
        message = all_caces[1]
        return render_template('admin/error_page.html',SIDEBAR=SIDEBAR , page_header="Cases" , message = message , err_msg=err_msg)



# ================================ create case
#create users called from dbstuff
@app.route('/admin/create_case', methods=['GET', 'POST'])
def admin_create_case():
    try:
        if request.method == 'GET':
            return redirect(url_for('home_page', err_msg="Invalid HTTP request method" ))

        if request.method == 'POST':
            casename_accepted_char = 'abcdefghijklmnopqrstuvwxy0123456789_'
            casename = ''.join( [ e for e in request.form['casename'].lower() if e in casename_accepted_char ] )
            casename = casename.lstrip('_')
            #get paramters from the UI query
            case_details = {
                "casename"  : casename,
                "status"    : request.form['status'],
                'date'      : str(datetime.now() ).split('.')[0]
            }
            if request.form['update_or_create_case'] == "create":

                retn_cre = db_cases.create_case( case_details )
                print retn_cre
                # if failed to create case
                if retn_cre[0] == False:
                    return redirect(url_for('home_page', err_msg="Error: " + retn_cre[1] ))
                

                create_indx = db_es.create_index(case_details['casename'])
                
                if create_indx[0] == False:
                    return redirect(url_for('home_page', err_msg="Error: " + create_indx[1] ))
                
                return redirect(url_for('home_page' , message="Case ["+case_details['casename']+"] created  "))

            else:
                retn_cre = db_cases.update_case( case_details['casename'] ,  case_details )
                # if failed to create case
                if retn_cre[0] == False:
                    return redirect(url_for('home_page', err_msg="Error: " + retn_cre[1] ))

                return redirect(url_for('home_page' , message="Case ["+case_details['casename']+"] updated "))

    except Exception as e:
        print str(e)
        return redirect(url_for('home_page', err_msg="Error: " + str(e) ))



# =================== Config =======================

# show the main config page
@app.route('/admin/config')
def config_page():
    # get all cases 
    all_caces = db_cases.get_cases()
    if all_caces[0] == False:
        print all_caces[1]

    return render_template('admin/configuration.html',SIDEBAR=SIDEBAR,all_caces=all_caces , page_header="Configuration")

# delete important fields and labels
@app.route('/admin/config/del_impt_field', methods=["POST"])
def del_impt_field():
    if request.method == "POST":
        values = request.json
        print values['values']
        print "*"*100
        del_important_fields(values['values'])
        return json.dumps({"result" : 'done'})

# delete folders names and labels
@app.route('/admin/config/delete_folder_values', methods=["POST"])
def delete_folder_values():
    if request.method == "POST":
        values = request.json
        print values['values']
        print "*"*100
        del_important_folders_names(values['values'])
        return json.dumps({"result" : 'done'})

@app.route('/admin/config/delete_parser_values', methods=["POST"])
def delete_parser_values():
    if request.method == "POST":
        values = request.json
        print values['values']
        print "*"*100
        del_important_parsers_names(values['values'])
        return json.dumps({"result" : 'done'})

# add important fields and labels
@app.route('/admin/config/imp_fields', methods=["POST"])
def add_impt_fields():
    if request.method == "POST":
        values = request.json
        print json.loads(json.dumps(values))
        insert_imp_fields(json.loads(json.dumps(values)))
        return json.dumps({"result" : 'done'})

# add path fields and labels
@app.route('/admin/config/folder_name_fields', methods=["POST"])
def add_folder_name_fields():
    if request.method == "POST":
        values = request.json
        print json.loads(json.dumps(values))
        insert_folder_name_fields(json.loads(json.dumps(values)))
        return json.dumps({"result" : 'done'})

# add path parsers names and labels
@app.route('/admin/config/add_parsers_names', methods=["POST"])
def add_parsers_names():
    if request.method == "POST":
        values = request.json
        print json.loads(json.dumps(values))
        insert_parsers_names(json.loads(json.dumps(values)))
        return json.dumps({"result" : 'done'})


#create users called from dbstuff
@app.route('/admin/delete_case/<casename>')
def admin_delete_case(casename):

    retn_cre = db_cases.delete_case( casename )
    if retn_cre[0] == False:
        return redirect(url_for('home_page', err_msg="Error: [From MongoDB] " + retn_cre[1] ))
    
    retn_cre = db_es.delete_index(casename) # delete case index from elasticsearch 

    if retn_cre[0] == False:
        return redirect(url_for('home_page', err_msg="Error: [From ES] " + retn_cre[1] ))


    return redirect(url_for('home_page'))





# =================== Parsers =======================

# add parser information
@app.route('/admin/config/add_parser', methods=["POST"])
def admin_add_parser():
    if request.method == "POST":
        ajax_j =  request.form.to_dict()
        action = ajax_j['action'] # add or edit

        # upload and unzip parser file
        file = request.files['parser_file_field']
        print file
        # if file not selected
        if file.filename == '' and action == 'add':
            return json.dumps({'result' : 'error' , 'msg' : 'Parser file not selected'})

        # if there is uploaded parser file, unzip it 
        if file.filename != '':
            # remove the old parser folder
            old_parser_folder = db_parsers.get_parser_by_name(ajax_j['name'])
            try:
                shutil.rmtree(app.config['PARSER_PATH'] + old_parser_folder['parser_folder'])
            except:
                pass

            # unzip the uploaded parser to the parser folder 
            file_name = secure_filename(file.filename)
            print "file name: " + file_name
            tmp_path = app.config['PARSER_PATH'] + "/temp/" +  file_name
            file.save( tmp_path )
            unzip_fun = unzip_file( tmp_path  , app.config['PARSER_PATH'] + "/" + file_name.split(".")[0] )
            if unzip_fun == True:
                parser_filesname = list_zip_file( tmp_path )
                print "parser_filesname: " + str(parser_filesname)
            else:
                print "[-] Error: Failed to unzip file"
                return json.dumps( {'result' : 'error'} )
        
            ajax_j['parser_folder'] = file_name.split(".")[0] # this will store the parser folder in parsers/
            
            # if __init__.py file not in the parser folder, create one
            if not os.path.exists(app.config['PARSER_PATH'] + "/" + ajax_j['parser_folder'] + '/__init__.py'):
                f= open(app.config['PARSER_PATH'] + "/" + ajax_j['parser_folder'] + '/__init__.py',"w+")
                f.close()
        
        print ajax_j

        # reformat the parser important fields into json
        imp_fields_json = []
        imp_fields = ajax_j['important_field'].split('|')
        for i in imp_fields:
            i = i.split(',')
            if len(i) != 2:
                continue
            imp_fields_json.append({
                'name' : i[0],
                'path' : i[1],
            })
        ajax_j['important_field'] = imp_fields_json


        # add parser to database mongoDB
        if action == 'add':
            add_parser = db_parsers.add_parser(ajax_j)
        else:
            add_parser = db_parsers.edit_parser(ajax_j['name'] , ajax_j)

        if add_parser == False:
            ajax_res = {'result' : 'error' , 'msg' : 'Parser already exists'}
        else:
            ajax_res = {'result' : 'success'}

        return json.dumps(ajax_res)
    

# get parser information
@app.route('/admin/config/get_parsers_ajax', methods=["POST"])
def get_parsers_ajax():
    if request.method == "POST":
        
        parsers = db_parsers.get_parser()
        print parsers
        ajax_res = {'result' : parsers}
        return json.dumps(ajax_res)


# delete parser
@app.route('/admin/config/delete_parsers_ajax', methods=["POST"])
def delete_parsers_ajax():
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')
        ajax_data = json.loads(ajax_str)['data']

        print "[+] Delete parser " + ajax_data['parser']
        res = db_parsers.delete_parser_by_name(ajax_data['parser'])
        if res:
            return json.dumps({'result' : 'true'})
        else:
            return json.dumps({'result' : 'false'})





# =================== Rules and Alerts =======================

# add tag to a specifc record
@app.route('/admin/add_rule', methods=["POST"])
def admin_add_rule():
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')

        ajax_data = json.loads(ajax_str)['data']
        print json_beautifier(ajax_data)

        res = db_rules.add_rule(ajax_data['rule_name'] , ajax_data['rule'] , ajax_data['rule_severity'] , ajax_data['rule_description'])
        if res[0] == True:
            return json.dumps({"result" : 'success'})
        else:
            return json.dumps({"result" : 'failed' , 'message' : res[1]})

    else:
        return json.dumps({"result" : 'failed' , 'message' : res[1]})



# delete rule
@app.route('/admin/delete_rule', methods=["POST"])
def admin_delete_rule():
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')

        ajax_data = json.loads(ajax_str)['data']
        print json_beautifier(ajax_data)

        res = db_rules.delete_rule(ajax_data['rule_id'])
        if res[0] == True:
            return json.dumps({"result" : 'success'})
        else:
            return json.dumps({"result" : 'failed' , 'message' : res[1]})

    else:
        return json.dumps({"result" : 'failed' , 'message' : "use POST request"})


# delete rule
@app.route('/admin/update_rule', methods=["POST"])
def admin_update_rule():
    if request.method == "POST":
        ajax_str =  urllib.unquote(request.data).decode('utf8')

        ajax_data = json.loads(ajax_str)['data']
        print json_beautifier(ajax_data)

        res = db_rules.update_rule(ajax_data['rule_id'] , ajax_data['new_rule'], ajax_data['new_sev'] , ajax_data['new_desc'])
        if res[0] == True:
            return json.dumps({"result" : 'success'})
        else:
            return json.dumps({"result" : 'failed' , 'message' : res[1]})

    else:
        return json.dumps({"result" : 'failed' , 'message' : "use POST request"})



#call admin page will all content from content_management
@app.route('/admin/rules', methods=["GET"])
def admin_rules():
    all_rules = db_rules.get_rules()

    if all_rules[0]:
        return render_template('admin/display_rules.html',SIDEBAR=SIDEBAR , all_rules=all_rules[1] , page_header="Rules")
    else:
        return render_template('admin/error_page.html',SIDEBAR=SIDEBAR , message=all_rules[1] , page_header="Cases")


