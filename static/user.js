var error_count = 0;

function findLocation() {
  if (geo_position_js.init()) {
    geo_position_js.getCurrentPosition(showLocations, errorFindingLocation, {
      enableHighAccuracy : true,
      timeout : 3000,
      maximumAge : 60000
    });
  } else {
    showLocations(null);
  }
}

function cacheLocation() {
  if (geo_position_js.init()) {
    geo_position_js.getCurrentPosition(function(p) {}, function(p) {}, {
      enableHighAccuracy : true,
      timeout : 60000,
      maximumAge : 60000
    });
    setTimeout("cacheLocation()", 60000);
  }
}

function showLocations(p) {
  var lon = null;
  var lat = null;
  if (p != null) {
    lon = p.coords.longitude.toFixed(2);
    lat = p.coords.latitude.toFixed(2);
  }
  $.get('/user/location',
      {latitude : lat == null ? "" : lat, longitude : lon == null ? "" : lon},
      function(data) {
    loc_data = JSON.parse(data);
    var select_location = $('#user_location_select');
    select_location.empty();
    select_location.append('<option>I won\'t tell!</option>');
    locations = loc_data['locations'];
    for (i in locations) {
      var loc = locations[i];
      if (loc == loc_data['user_location']) {
        select_location.append('<option selected="yes">' + loc + '</option>');
      } else {
        select_location.append('<option>' + loc + '</option>');
      }
    }
  });
}

function errorFindingLocation(p) {
  if (error_count++ < 2)
    findLocation();
  else {
    showLocations(null);
  }
}

$(document).ready(function() {
  $('#increment_count_lightbox').dialog({
    autoOpen: false,
    modal: true,
    resizable: false,
    buttons: {
      Save: function() {
        var type = $(this).data('type');
        var comment = $('#increment_form #comment').val();
        var loc = $('#increment_form #user_location_select').val();
        incrementCounter(type, comment, loc);
        $(this).dialog('close');
        resetDialog();
      },
      Cancel: function() {
        $(this).dialog('close');
        resetDialog();
      }
    }
  });

  $('.counter_increment_advanced').click(function() {
    findLocation();
    $('#increment_count_lightbox').data('type', $(this).attr('id')).dialog('open');
  });

  $('.counter_increment').click(function() {
    incrementCounter($(this).attr('id'));
  });
});

function resetDialog() {
  $('#increment_count_lightbox #comment').val('');
  var select_location = $('#user_location_select');
  select_location.empty();
  select_location.append('<option>Searching...</option>');
  error_count=0;
}

function incrementCounter(type, comment, loc) {
  $.post('/user/countitem', {type: type, comment: comment, location: loc}, function(data) {
    var selector = '.counter_value#' + type;
    $(selector).text(data);
  });
}