var toast = $.toast;

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
    if (path.split('.').length == 1){
        return json[path] // if there is not end then return the value
    }
    var dot_index = path.indexOf('.');
    var field = path.substring(0, dot_index)
    var new_path = path.substring(dot_index + 1)

    if(json.hasOwnProperty(field) || field < json.length)
        return get_field_from_json_path(json[field], new_path)
}



// built the details window for windows event information
function build_windows_event_table(record) {
    var event_id_link = "http://www.eventid.net/display.asp?eventid=" + record['_source']['Data']["Event"]["System"]["EventID"]["#text"];
    var open_badge = '<span class="badge bg-light-blue">'
    var system = record['_source']['Data']["Event"]["System"]
    var fields = {
        "EventID": "<a href=\"" + event_id_link + "\">" + system["EventID"]["#text"] + "</a> <a  target=\"_blank\" href=\"" + event_id_link + "\"><i class=\"fa fa-fw fa-external-link\"></i></a>",
        "Task": ("Task" in system) ? system["Task"] : "",
        "TimeCreated": ("TimeCreated" in system) ? system["TimeCreated"]["@SystemTime"] : "",
        "Level": ("Level" in system) ? system["Level"] : "",
        "ActivityID": ("Correlation" in system) ? system["Correlation"]['@ActivityID'] : "",
        "RelatedActivityID": ("Correlation" in system) ? system["Correlation"]["@RelatedActivityID"] : "",
        "Version": ("Version" in system) ? system["Version"] : "",
        "Opcode": ("Opcode" in system) ? system["Opcode"] : "",
        "EventRecordID": ("EventRecordID" in system) ? system["EventRecordID"] : "",
        "Provider_GUID": ("Provider" in system) ? system["Provider"]["@Guid"] : "",
        "Provider_Name": ("Provider" in system) ? system["Provider"]["@Name"] : "",
        "Keywords": ("Keywords" in system) ? system["Keywords"] : "",
        "ProcessID": ("Execution" in system) ? system["Execution"]["@ProcessID"] : "",
        "ThreadID": ("Execution" in system) ? system["Execution"]["@ThreadID"] : "",
        "Security_UserID": ("Security" in system) ? system["Security"]["@UserID"] : "",
        "Computer": ("Computer" in system) ? system["Computer"] : "",
        "Channel": ("Channel" in system) ? system["Channel"] : ""
    }
    var html = '<div class="box-header bg-gray disabled color-palette">System</div>';
    html = html + "<table class=\"table table-condensed\"><tbody>";
    for (k in fields) {

        if (typeof fields[k] == "undefined")
            continue
        html += "<tr><td>" + open_badge + k + " </span></td><td>" + fields[k] + "</td></tr>";

    }


    html = html + "</tbody></table>";



    html = html + '<div class="box-header bg-gray disabled color-palette">Data</div>';
    console.log(JSON.stringify(record['_source']['Data']["Event"]))
    for (var key in record['_source']['Data']["Event"]) {
        if (key == "System" || key == "@xmlns")
            continue;

        html = html + "<pre class=\"box-body\">" + JSON.stringify(record['_source']['Data']["Event"][key], null, 4).split('\\n').join('<br />') + "</pre>";
    }

    return html;
}


// build simple table (record contains key and values)
function build_simple_artifacts_table(records, searchable = true) {

    var open_badge = '<span class="badge bg-light-blue"> '
    results = convert_json_to_list(records['_source'])
    console.log(results)

    var html = '';
    html = html + "<table class=\"table table-condensed\"><tbody>";
    // var hashes = []
    for (var i = 0; i < results.length; i++) {
        var failed = results[i][0].split('|').join('.');
        var value = results[i][1];

        if (searchable)
            var search_plus = '<a id="' + failed + ':' + value + '" class="clickable add_to_search_query float_right"><i class="fa fa-search-plus"></i></a>'
        else
        // if(failed.contains("Hash"))
        //   alert('hash found');
            var search_plus = ''

        if (failed.indexOf("Data.Hash") >= 0) {
            // hashes.push(value);
            //
            var positives = '<span class="pull-right-container" > <small data="' + value + '" class="hash_data label bg-red"> waiting... </small> </span>'
            html += '<tr><td> ' + open_badge + " " + failed + ' </span> ' + search_plus + '</td><td>' + value + positives + '</td></tr>';
        } else {
            html += '<tr><td> ' + open_badge + " " + failed + ' </span> ' + search_plus + '</td><td>' + value + '</td></tr>';
        }

        // check_hash(hashes);
    }



    html = html + "</tbody></table>";

    return html;


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
            console.log(result)
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