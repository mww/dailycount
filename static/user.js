$(document).ready(function() {
  $('.counter-increment').click(function() {
    var type = $(this).attr('id');
    $.get('/user/countitem', {type: type}, function(data) {
      var selector = '.counter-value#' + type;
      var value = $(selector).text(data);
    });
  });
});
