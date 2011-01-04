var lon, lat;
var errorCount = 0;

function findLocation() {
  if (geo_position_js.init()) {
    geo_position_js.getCurrentPosition(success_callback, error_callback, {
      enableHighAccuracy : true,
      timeout : 10000,
      maximumAge : 60000
    });
  } else {
    $('div.location').text('Your browser sucks...');
  }
}

function success_callback(p) {
  lon = p.coords.longitude.toFixed(2);
  lat = p.coords.latitude.toFixed(2);
  $('div.location').text('Lon=' + lon + ', Lat=' + lat);
}

function error_callback(p) {
  if(errorCount++ < 30)
    findLocation();
  else
    $('div.location').text('Oh noes. Failed to find location!');
}

$(document).ready(function() {
  $('#increment_count_lightbox').dialog({
    autoOpen: false,
    height: 350,
    width: 350,
    modal: true,
    buttons: {
      Save: function() {
        var type = $(this).data('type');
        var comment = document.increment_form.comment.value;
        incrementCounter(type, comment, lat, lon);
        $(this).dialog('close');
        resetDialog();
      },
      Cancel: function() {
        $(this).dialog('close');
        resetDialog();
      }
    }
  });

  $('.counter_increment_with_comment').click(function() {
    $('#increment_count_lightbox').data('type', $(this).attr('id')).dialog('open');
    findLocation();
  });
  
  $('.counter_increment').click(function() {
    incrementCounter($(this).attr('id'));
  });
});

function resetDialog() {
  $('#increment_count_lightbox #comment').val('');
  $('div.location').text('Finding location...');
  
  errorCount=0;
}

function incrementCounter(type, comment, latitude, longitude) {
  $.post('/user/countitem', {type: type, comment: comment, latitude: latitude, longitude: longitude}, function(data) {
    var selector = '.counter_value#' + type;
    $(selector).text(data);
  });
}
