var toast = $.toast;



// escape html strings
var entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;',
  };

  function escapeHtml(string) {
    return String(string).replace(/[&<>"'`=\/]/g, function (s) {
      return entityMap[s];
    });
  }






function toast_msg(msg, type = "info", header = "Information") {
    toast({
        text: msg,
        heading: header,
        icon: type,
        showHideTransition: 'fade',
        allowToastClose: true,
        hideAfter: 1000,
        stack: 2,
        position: 'bottom-left',
        textAlign: 'left',
    });
}


// this function take a json variable and return a list of the elements
function convert_json_to_list(json) {
    var result = []
    for (var key in json) {
        if (typeof json[key] == 'object') {
            var fetch = convert_json_to_list(json[key]);
            for (var obj = 0; obj < fetch.length; obj++)
                result.push([key + '.' + fetch[obj][0].split('.').join('|'), fetch[obj][1]]);
        } else
            result.push([key, json[key]])
    }
    return result;
}


// it will take the json and the json_path and return the value
function get_field_from_json_path(json, path) {
    //console.log(path)
    //console.log(json)
    if (path.split('.').length == 1)
        return (json == null) ? 'null' : json[path]; // if there is not end then return the value
    
    var dot_index = path.indexOf('.');
    var field = path.substring(0, dot_index)
    var new_path = path.substring(dot_index + 1)

    if(json.hasOwnProperty(field) || field < json.length)
        return get_field_from_json_path(json[field], new_path)
}


if (!library)
   var library = {};

library.json = {
   replacer: function(match, pIndent, pKey, pVal, pEnd) {
      var key = '<span class=json-key>';
      var val = '<span class=json-value>';
      var str = '<span class=json-string>';
      var r = pIndent || '';
      if (pKey)
         r = r + key + pKey.replace(/[": ]/g, '') + '</span>: ';
      if (pVal)
         r = r + (pVal[0] == '"' ? str : val) + pVal + '</span>';
      return r + (pEnd || '');
      },
   prettyPrint: function(obj) {
      var jsonLine = /^( *)("[\w]+": )?("[^"]*"|[\w.+-]*)?([,[{])?$/mg;
      return JSON.stringify(obj, null, 3)
         .replace(/&/g, '&amp;').replace(/\\"/g, '&quot;')
         .replace(/</g, '&lt;').replace(/>/g, '&gt;')
         .replace(jsonLine, library.json.replacer);
      }
   };


// this function build the alert of rhaegal detection
function build_rhaegal_rules(record){
    if(!record['_source']['Data'].hasOwnProperty("rhaegal")){
        return "";
    }
    
    var open_badge = '<span class="badge bg-blue">'
    var html = '<div class="box-header disabled color-palette"><b>Rhaegal</b></div>';

    html = html + "<table class=\"table table-condensed table_left_header\"><tbody>";
    for (k in record['_source']['Data']['rhaegal']) {
        html += "<tr><td>" + open_badge + k + " </span></td><td>" + record['_source']['Data']['rhaegal'][k] + "</td></tr>";
    }
    
    html = html + "</tbody></table><br />";

    return html
}

// built the details window for windows event information
function build_windows_event_table(record , container) {
    
    var open_badge = '<span class="badge bg-blue">'
    //console.log(record)
    var system = record['_source']['Data']["Event"]["System"]
    var eventid = get_field_from_json_path(system , "EventID.#text")
    var event_id_link = "http://www.eventid.net/display.asp?eventid=" + eventid;
    var fields = {
        "EventID"           : "<a href=\"" + event_id_link + "\">" + eventid + "</a> <a  target=\"_blank\" href=\"" + event_id_link + "\"><i class=\"fa fa-fw fa-external-link\"></i></a>",
        "Task"              : ("Task" in system) ? system["Task"] : "",
        "TimeCreated"       : get_field_from_json_path(system , "TimeCreated.@SystemTime"),
        "Level"             : get_field_from_json_path(system , "Level"),
        "ActivityID"        : get_field_from_json_path(system , "Correlation.@ActivityID"),
        "RelatedActivityID" : get_field_from_json_path(system , "Correlation.@RelatedActivityID"),
        "Version"           : get_field_from_json_path(system , "Version"),
        "Opcode"            : get_field_from_json_path(system , "Opcode"),
        "EventRecordID"     : get_field_from_json_path(system , "EventRecordID"),
        "Provider_GUID"     : get_field_from_json_path(system , "Provider.@Guid"),
        "Provider_Name"     : get_field_from_json_path(system , "Provider.@Name"),
        "Keywords"          : get_field_from_json_path(system , "Keywords"),
        "ProcessID"         : get_field_from_json_path(system , "Execution.@ProcessID"),
        "ThreadID"          : get_field_from_json_path(system , "Execution.@ThreadID"),
        "Security_UserID"   : get_field_from_json_path(system , "Security.@UserID"),
        "Computer"          : get_field_from_json_path(system , "Computer"),
        "Channel"           : get_field_from_json_path(system , "Channel")
    }

    var rhaegal_hit = build_rhaegal_rules(record)
    
    var html = rhaegal_hit +  '<div class="box-header disabled color-palette"><b>System</b></div>';
    html = html + "<table class=\"table table-condensed table_left_header\"><tbody>";
    for (k in fields) {

        if (typeof fields[k] == "undefined")
            continue
        html += "<tr><td>" + open_badge + k + ' </span></td><td style="min-width:250px">' + fields[k] + "</td></tr>";

    }


    html = html + "</tbody></table>";



    html = html + '<div class="box-header disabled color-palette"><b>Data</b></div>';

    html = html + '<pre><code id="event_json_viewer"></code></pre>';
    

    container.html(html);

    $('#event_json_viewer').html(library.json.prettyPrint(record['_source']['Data']["Event"]));

}



// build simple table (record contains key and values)
function build_simple_artifacts_table(records , container, searchable = true) {

    var open_badge = '<span class="badge bg-blue"> '
    results = convert_json_to_list(records['_source'])

    var rhaegal_hit = build_rhaegal_rules(records)
    
    html = rhaegal_hit + "<table class=\"table table-condensed table_left_header\"><tbody>";

    for (var i = 0; i < results.length; i++) {
        var field = results[i][0].split('|').join('.');
        var value = results[i][1];

        if (searchable)
            var search_plus = '<a id="' + field + ':' + value + '" class="clickable add_to_search_query float_right"><i class="fa fa-search-plus"></i></a>'
        else
            var search_plus = ''

        
        html += '<tr><td> ' + open_badge + " " + field + ' </span> ' + search_plus + '</td><td  style="min-width:250px">' + escapeHtml(value) + '</td></tr>';
        

        
    }



    html = html + "</tbody></table>";

    container.html(html);


}


function check_hash(records) {
    var d = false;

    $.ajax({
        type: 'POST',
        url: "/piebald/",
        timeout: 30000,
        async: false,
        cache: false,
        contentType: 'application/json;charset=UTF-8',
        //data : JSON.stringify({'data': {"wanted_page":wanted_page , 'query' : decodeHtml('{{search_query}}') } }),
        data: JSON.stringify({ 'data': { "hash": records } }),
        success: function(result) {
            //console.log(result)
            d = result
        },
        error: function(error) {
            d = "timeout"
        }

    });
    return d;
    // $.getJSON($SCRIPT_ROOT + '/piebald/', {
    //         hash: records
    //       }, function(data) {
    //         // json = data;
    //         alert('gr');
    //         console.log( data );
    //         d = data
    //       });
    //       return d;

}