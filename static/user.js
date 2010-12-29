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
        incrementCounter(type, comment);
        $(this).dialog('close');
        $('#increment_count_lightbox #comment').val('');
      },
      Cancel: function() {
        $(this).dialog('close');
        $('#increment_count_lightbox #comment').val('');
      }
    }
  });

  $('.counter_increment_with_comment').click(function() {
    $('#increment_count_lightbox').data('type', $(this).attr('id')).dialog('open');
  });
  
  $('.counter_increment').click(function() {
    incrementCounter($(this).attr('id'));
  });
});

function incrementCounter(type, comment) {
  $.post('/user/countitem', {type: type, comment: comment}, function(data) {
    var selector = '.counter_value#' + type;
    $(selector).text(data);
  });
}