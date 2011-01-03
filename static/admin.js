$(document).ready(function() {
  $('#create_item_type_form').dialog({
    autoOpen: false,
    height: 200,
    width: 350,
    modal: true,
    buttons: {
      Save: function() {
        var name = $('#create_item_type_form #name').val();
        $.post('/admin/createitemtype', {name: name}, function(data) {
          row = $('<tr></tr>');
          row.append('<td class="name">' + data + '</td>');
          td = $('<td class="active"></td>');
          input = $('<input type="checkbox" name="' + data
              + '" checked="yes"/>');
          td.append(input);
          row.append(td);

          var last_row = $('#counted_types_table tr').last().prev();
          last_row.after(row);
        });
        $(this).dialog('close');
        $('#create_item_type_form #name').val('');
      },
      Cancel: function() {
        $(this).dialog('close');
        $('#create_item_type_form #name').val('');
      }
    }
  });

  $('#create_item_type_button').click(function() {
    $('#create_item_type_form').dialog('open');
  });
});