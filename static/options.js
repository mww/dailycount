$(document).ready(function() {
  $.get('/user/options/timezones', function(data) {
    options = JSON.parse(data);
    var select_option = $('#user-timezone-select');
    timezones = options['timezones']
    for (i in timezones) {
      var tz = timezones[i];
      if (tz == options['user_timezone']) {
        select_option.append('<option selected="yes">' + tz + '</option>');
      } else {
        select_option.append('<option>' + tz + '</option>');
      }
    }
  });
});