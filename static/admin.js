$(document).ready(function() {
  $('#create-item-type-form').dialog({
    autoOpen: false,
    height: 200,
    width: 350,
    modal: true,
    buttons: {
      Save: function() {
        var name = $('#create-item-type-form #name').val();
        $.post('/admin/createitemtype', {name: name}, function(data) {
          row = $('<tr></tr>');
          row.append('<td class="name">' + data + '</td>');
          td = $('<td class="active"></td>');
          input = $('<input type="checkbox" name="' + data
              + '" checked="yes"/>');
          td.append(input);
          row.append(td);

          var last_row = $('#counted-types-table tr').last().prev();
          last_row.after(row);
        });
        $(this).dialog('close');
        $('#create-item-type-form #name').val('');
      },
      Cancel: function() {
        $(this).dialog('close');
        $('#create-item-type-form #name').val('');
      }
    }
  });

  $('#create-item-type-button').click(function() {
    $('#create-item-type-form').dialog('open');
  });
});