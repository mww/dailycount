$(document).ready(function() {
  // a workaround for a flaw in the demo system (http://dev.jqueryui.com/ticket/4375), ignore!
  $('#dialog:ui-dialog').dialog('destroy');
  $('.item_delete_confirm_dialog').dialog({
    autoOpen: false,
    title: 'Delete',
    resizable: false,
    modal: true,
    buttons: {
      Close: function() {
        $(this).dialog('close');
      },
      "Delete": function() {
        var id = $(this).data('id');
        $.post('/user/item/' + id + '/delete', function(data) {
          $('.history_day_item#' + id).slideUp('slow', function() {
            $(this).detach();
          });
        });
        $(this).dialog('close');
      }
    }
  });

  //$('.item_details_container').hide();

  $('.item_comment_details').hide();
  $('.item_comment_button').click(function() {
    var id = $(this).data('id');
    var comment = $('.item_comment_details#item_' + id).toggle();
    toggleDetailsContainer(id);
  });

  $('.item_location_details').hide();
  $('.item_location_button').click(function() {
    var id = $(this).data('id');
    var location = $('.item_location_details#item_' + id).toggle();
    toggleDetailsContainer(id);
  });

  $('.item_delete_button').click(function() {
    var id = $(this).data('id');
    $('.item_delete_confirm_dialog#item_' + id).dialog('open');
  });
});

function toggleDetailsContainer(id) {
  var comment = $('.item_comment_details#item_' + id);
  var location = $('.item_location_details#item_' + id);

  if ($(comment).is(':visible') || $(location).is(':visible')) {
    var details = $('.item_details_container#item_' + id);
    $('.item_details_container#item_' + id)
        .removeClass('hidden')
        .addClass('visible');
  } else {
    var details = $('.item_details_container#item_' + id);
    $('.item_details_container#item_' + id)
        .removeClass('visible')
        .addClass('hidden');
  }
}