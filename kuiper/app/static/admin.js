


/* ================================================= */
/* ================ Admin Configuration ============ */
/* ================================================= */



/* =================== Start Parser ================ */

// parsers options - edit parser
$('#parsers_list_table').on('click' , '.parsers_edit_parser' , function(){
    var parser = $(this).data('parsername')

    // change the view to add parser
	$(".change_parser_view[data-content='parsers_add']").click()
	
    // get parser details
    var parser_detail = null
    for(var i in parsers_details)
        if(parsers_details[i]['name'] == parser)
          parser_detail = parsers_details[i];
    
    // fill the fields with parser details
    $('#parser_name_field').attr('disabled','disabled')
    $('#parser_name_field').val(parser_detail['name'])
    $('#parser_description_field').val(parser_detail['description'])
    $('#parser_interface_function_field').val(parser_detail['interface_function'])
    $('#parser_type_field').val(parser_detail['parser_type_field'])
    $('#parser_files_categorization_type').val(parser_detail['parser_files_categorization_type'])
    $('#parser_files_categorization_values').val(parser_detail['parser_files_categorization_values'])

    for(var v in parser_detail['important_field']){
      console.log($('.parser_selection_important_field_name:last-child'))
        $(".parser_selection_important_field_name[data-num='"+v+"']").val(parser_detail['important_field'][v]['name'])
        $(".parser_selection_important_field_path[data-num='"+v+"']").val(parser_detail['important_field'][v]['path'])
        if(v < parser_detail['important_field'].length -1 )
            $('.parser_selection_add_important_field').click()
    }


    $('#add_parser_button_submit').attr('data-action' , 'edit')
    $('#add_parser_button_submit').addClass('btn-warning')
    $('#add_parser_button_submit').removeClass('btn-info')
    $('#add_parser_button_submit').html('<i class="fa fa-fw fa-edit"></i> Edit parser')

})

// parsers options - remove parser
$('#parsers_list_table').on( 'click',  '.parsers_delete_parser' , function(){
    var parser = $(this).data('parsername')
    console.log(parser)
    $.ajax({
      type : 'POST',
      url : "/admin/config/delete_parsers_ajax",
      contentType: 'application/json;charset=UTF-8',
      data: JSON.stringify( {'data' : {'parser' : parser} }),
      success: function(result) {
  
          var r = JSON.parse(result)['result'];
          if(r == 'true'){
            toast_msg('Parser ['+parser+'] Removed Successfully')
            update_parsers_table()
          } else {
            toast_msg('Parser ['+parser+'] Could not be Removed' , type='error' , header = "Error")
          }

  
      },
      error: function(error){
        console.log(error)
        toast_msg('Parser ['+parser+'] Could not be Removed \n ' + error.toString() , type='error' , header="Error")
      }
    });
})


// build the table of parsers list 
var parsers_details = null
function update_parsers_table(){
  $.ajax({
    type : 'POST',
    url : "/admin/config/get_parsers_ajax",
    
    success: function(result) {

        var r = JSON.parse(result)['result'];
        console.log(r)
        parsers_details = r
        var parsers_list_table = $('#parsers_list_table')
        parsers_list_table.html('')
        // add parsers table content
        for(var i = 0 ; i < r.length ; i++){

          // convert important fields from json to html
          var imp_fields_html = ''
          for(var imp in r[i]['important_field']){
            imp_fields_html += '<span class="badge">Name</span> ' + r[i]['important_field'][imp]['name'] + ' <span class="badge">Path</span> ' + r[i]['important_field'][imp]['path'] + "<br />"
          }

          var cat_files_html = '<b>'+r[i]['parser_files_categorization_type']+'</b><br />'
          cat_files_vals = (r[i]['parser_files_categorization_values'] != null) ? r[i]['parser_files_categorization_values'].split(",") : []
          for(var v in cat_files_vals){
            cat_files_html += '<span class="badge bg-light-blue">'+cat_files_vals[v]+'</span> '
          }

          // add the html to parsers table
          parsers_list_table.append('<tr>\
              <td>'+(i+1)+' <a data="'+i+'" class="dropdown_parser_details" style="cursor: pointer;"><i class="fa fa-fw fa-chevron-right"></i></a></td>\
              <td>'+r[i]['name']+'</td>\
              <td>'+r[i]['parser_type_field']+'</td>\
              <td>'+r[i]['creation_time'].split('T').join(' ').split('.')[0] +'</td>\
              <td>'+r[i]['description']+'</td>\
              <td>\
                  <div class="btn-group">\
                    <button type="button" class="parsers_delete_parser btn btn-danger btn-xs" data-parsername="'+r[i]['name']+'" title="Remove Parser"><i class="fa fa-fw fa-remove "></i></button>\
                    <button type="button" class="parsers_edit_parser btn btn-warning btn-xs" data-parsername="'+r[i]['name']+'" title="Edit Parser"><i class="fa fa-fw fa-edit"></i></button>\
                  </div>\
              </td>\
          </tr><tr id="parser_details_'+i+'" style="display:none">\
            <td colspan="6">\
              <table class="table table-bordered">\
              <tr><td width="200"><b>Name</b></td><td> '+r[i]['_id']+'</td></tr>\
              <tr><td width="200"><b>Interface Function</b></td><td> '+r[i]['interface_function']+'</td></tr>\
              <tr><td width="200"><b>Description</b></td><td> '+r[i]['description']+'</td></tr>\
              <tr><td width="200"><b>Creation Time</b></td><td> '+r[i]['creation_time'].split('T').join(' ').split('.')[0]+'</td></tr>\
              <tr><td width="200"><b>Parser Type</b></td><td> '+r[i]['parser_type_field']+'</td></tr>\
              <tr><td width="200"><b>Important Fields</b></td><td> '+imp_fields_html+'</td></tr>\
              <tr><td width="200"><b>Files Categorization</b></td><td> '+cat_files_html+'</td></tr>\
              </table>\
            </td>\
          </tr>')
        }

    },
    error: function(error){
      alert(JSON.stringify(error));
    }
  });
}

$(document).ready(function(){
    $('#parsers_list').fadeIn("fast")
    update_parsers_table()
})

// show details of the parsers on the parser tab table
$(document).ready(function(){
  $('#parsers_list_table').on('click' , '.dropdown_parser_details' , function(){
      var id = $(this).attr('data')
      $('#parser_details_' + id).fadeToggle()
      console.log( parsers_details[id] )
  })
})


// showing the parsers content tab
var current_parser_view = 'parsers_list'
$('.change_parser_view').on( 'click' , function(){
  var clicked_parser_view = $(this).data('content')
  if( current_parser_view ==  clicked_parser_view){
    console.log('no change: ' + current_parser_view)
  } else {
    console.log( clicked_parser_view )
    $('#' + current_parser_view).fadeOut( "fast", function() {
        $('#' + clicked_parser_view).fadeIn("fast")
    });
    current_parser_view = clicked_parser_view
  }
  // if current view is parsers_list then build the table of parsers
  if(current_parser_view == "parsers_list"){
    update_parsers_table()
  }

  // if current view is 
  if(current_parser_view == 'parsers_add'){

      $('#parser_name_field').removeAttr('disabled')
      $('#parser_name_field').val('')
      $('#parser_description_field').val('')
      $('#parser_interface_function_field').val('')
      $('#parser_type_field').val('logging_information')
      $('#parser_files_categorization_type').val('extension')
      $('#parser_files_categorization_values').val('')
      
      $('.parser_selection_important_field_path').parent().parent().remove()
      $('.parser_selection_add_important_field').click()

      $('#add_parser_button_submit').attr('data-action' , 'add')
      $('#add_parser_button_submit').removeClass('btn-warning')
      $('#add_parser_button_submit').addClass('btn-info')
      $('#add_parser_button_submit').html('<i class="fa fa-plus"></i> Add parser')
  } 

})


// add parsers - add important field input 
$('.parser_selection_add_important_field').click(function(event){
    var num = $('.parser_selection_important_field_name').length
    var input_imp_field = '<tr>\
          <td><input type="text" class="parser_selection_important_field_name form-control" data-num="'+num+'"  placeholder="Example: Event ID"/></td>\
          <td><input type="text" class="parser_selection_important_field_path form-control" data-num="'+num+'" placeholder="Example: Event.System.EventID.#text"/></td>\
          <td><button type="button" class="btn btn-info parser_selection_del_important_field"><i class="fa fa-fw fa-minus"></i></button></td>\
      </tr>'
    
    $('#parser_selection_important_field_table').append(input_imp_field)

})

// add parsers - delete important field input
$('#parser_selection_important_field_table').on( 'click' , '.parser_selection_del_important_field' , function(event){
    console.log($(this))
    $(this).parent().parent().remove()
})

// add parser submit
$('#add_parser_button_submit').click( function(event){

    event.preventDefault();
    var action = $(this).data('action')
    console.log($('#upload-file'))
    var formData = new FormData($('#upload-file')[0]);
    formData.append('name' , $('#parser_name_field').val())
    formData.append('description' ,  $('#parser_description_field').val())
    formData.append('interface_function' , $('#parser_interface_function_field').val())
    formData.append('parser_type_field' , $('#parser_type_field').val() )
    formData.append('parser_files_categorization_type' , $('#parser_files_categorization_type').val() )
    formData.append('parser_files_categorization_values' , $('#parser_files_categorization_values').val() )
    formData.append('action' , action ) // add or edit 

    // get all the important fields from the table
    var parser_selection_important_field_name = []
    var parser_selection_important_field_path = []
    $.each( $('.parser_selection_important_field_name') , function(){
      parser_selection_important_field_name.push( $(this).val() )
    } )
    $.each( $('.parser_selection_important_field_path') , function(){
      parser_selection_important_field_path.push( $(this).val() )
    } )
    // combine both list into json important fields
    var parser_selection_important_field = []
    for(var v = 0 ; v < parser_selection_important_field_name.length ; v++)
        if(parser_selection_important_field_name[v] != '' || parser_selection_important_field_path[v] != '')
            parser_selection_important_field.push(parser_selection_important_field_name[v] + ',' + parser_selection_important_field_path[v])
    
    // name,path|name,path|....
    console.log(parser_selection_important_field.join('|'))
    formData.append('important_field' , parser_selection_important_field.join('|') )

    console.log('parser information ')
    console.log(formData)

    
    var url_page = '/admin/config/add_parser'
    $.ajax({
            xhr : function() {
              var xhr = new window.XMLHttpRequest();
              console.log('xhr: ')
              console.log(xhr)

              xhr.upload.addEventListener('progress', function(e) {

                if (e.lengthComputable) {
                    var percent = Math.round((e.loaded / e.total) * 100);
                    $('#progressBar').attr('aria-valuenow', percent).css('width', percent + '%').text(percent + '%');
                    $('#filesit').empty();
                    if ( percent == 100)
                      $('#progressBar').attr('aria-valuenow', percent).css('width', percent + '%').text('Done');
                }
              });
              return xhr;
            },
            type: 'POST',
            url: url_page,
            data : formData,
            processData : false,
            contentType : false,
            async: true,
            dataType: 'json',
            success: function(data, status, request) {
                if(data['result'] == "error")
                  toast_msg(data['msg'], type = "error" , header = "Error")
                else
                  toast_msg( (action == 'add') ? 'Parser added' : 'Parser Updated' , type = "info" , header = "Done")
                
            },
            error: function() {
                alert('Unexpected error');
            }
      });
      

})




/* =================== End Parser ================ */
