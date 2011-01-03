$(document).ready(function() {
  // a workaround for a flaw in the demo system (http://dev.jqueryui.com/ticket/4375), ignore!
  $( "#dialog:ui-dialog" ).dialog( "destroy" );
  $( ".item-delete-confirm-dialog" ).dialog({
    autoOpen: false,
    title: "Delete",
    resizable: false,
    modal: true,
    buttons: {
    	"Delete": function() {
    	  var id = $(this).data('id');
    	  $.post('/user/item/' + id + '/delete', function(data) {
    	    $('.history-day-item#' + id).fadeOut('slow', function() {
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

  $('.delete-button').click(function() {
    var id = $(this).parent().attr('id');
    $('.item-delete-confirm-dialog#dialog-' + id).dialog('open');
  });
});