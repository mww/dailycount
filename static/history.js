$(document).ready(function() {
  // a workaround for a flaw in the demo system (http://dev.jqueryui.com/ticket/4375), ignore!
  $( "#dialog:ui-dialog" ).dialog( "destroy" );
  $( ".item_delete_confirm_dialog" ).dialog({
    autoOpen: false,
    title: "Delete",
    resizable: false,
    modal: true,
    buttons: {
    	"Delete": function() {
    	  var id = $(this).data('id');
    	  $.post('/user/item/' + id + '/delete', function(data) {
    	    $('.history_day_item#' + id).fadeOut('slow', function() {
    	      $(this).detach();
    	    });
    	  });
    		$(this).dialog( "close" );
    	},
    	Cancel: function() {
    		$(this).dialog( "close" );
    	}
    }
  });

  $('.delete_button').click(function() {
    var id = $(this).parent().attr('id');
    $('.item_delete_confirm_dialog#dialog_' + id).dialog('open');
  });
});