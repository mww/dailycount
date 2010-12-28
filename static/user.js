$(document).ready(function() {
  $('#increment_count_lightbox').dialog({
    autoOpen: false,
    height: 310,
    width: 350,
    modal: true,
    buttons: {
      Save: function() {
	    var type = $(this).data('type');
	    var comment = document.increment_form.comment.value;
	    $.post('/user/countitem', {type: type, comment: comment});
        $(this).dialog('close');
        $('#increment_count_lightbox #comment').val('');
        $.get('/user/countitem', {type: type}, function(data) {
	      var selector = '.counter_value#' + type;
	      $(selector).text(data);
	    });
      },
      Cancel: function() {
        $(this).dialog('close');
        $('#increment_count_lightbox #comment').val('');
      }
    }
  });

  $('.counter_increment').click(function() {
    $('#increment_count_lightbox').data('type', $(this).attr('id')).dialog('open');
  });
});