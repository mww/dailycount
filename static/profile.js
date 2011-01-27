var errorCount = 0;
function findLocation() {
  if (geo_position_js.init()) {
    geo_position_js.getCurrentPosition(successCallback, errorCallback, {
      enableHighAccuracy : true,
      timeout : 20000,
      maximumAge : 60000
    });
  } else {
    $('#location').text('Current location: Your browser sucks');
  }
}

function successCallback(p) {
  var lon = p.coords.longitude.toFixed(6);
  var lat = p.coords.latitude.toFixed(6);
  var location = $('#location');
  location.text('Current location: Lat=' + lat + ', Lon=' + lon);
  location.data('lat', lat);
  location.data('lon', lon);
  var button = $('#use_current_location_button');
  button.removeAttr('disabled').removeClass('ui-state-disabled');
}

function errorCallback(p) {
  if(errorCount++ < 2) {
    findLocation();
  }
  else {
    $('#location').text('Current location: The Moon');
  }
}

$(document).ready(function() {
  var button = $('#use_current_location_button');
  button.attr('disabled', 'disabled').addClass('ui-state-disabled');
  $('#use_current_location_button').click(function() {
    var location = $('#location');
    var lat = location.data('lat');
    var lon = location.data('lon');
    $('#create_saved_location_lightbox #latitude').val(lat);
    $('#create_saved_location_lightbox #longitude').val(lon);
  });

  $.get('/user/profile/timezones', function(data) {
    options = JSON.parse(data);
    var select_option = $('#user_timezone_select');
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

  $('#create_saved_location_lightbox').dialog({
    autoOpen: false,
    modal: true,
    buttons: {
      Save: function() {
        var name = document.create_saved_location_form.name.value;
        var latitude = document.create_saved_location_form.latitude.value;
        var longitude = document.create_saved_location_form.longitude.value;
        createSavedLocation(name, latitude, longitude);
        $(this).dialog('close');
        resetDialog();
      },
      Cancel: function() {
        $(this).dialog('close');
        resetDialog();
      }
    }
  });

  $('.create_saved_location_button').click(function() {
    $('#create_saved_location_lightbox').dialog('open');
    findLocation();
  });

});

function resetDialog() {
  $('#create_saved_location_lightbox #name').val('');
  $('#create_saved_location_lightbox #latitude').val('');
  $('#create_saved_location_lightbox #longitude').val('');
  $('#location').text('Current location: Searching...');
  var button = $('#use_current_location_button');
  button.attr('disabled', 'disabled').addClass('ui-state-disabled');
  errorCount=0;
}

function createSavedLocation(name, latitude, longitude) {
  $.post('/user/location',
      {name: name, latitude: latitude, longitude: longitude}, function(data) {
    if (data.indexOf('OK') === 0) {
      row = $('<tr></tr>');
      row.append('<td class="name">' + name + '</td>');
      row.append('<td class="coords">' + latitude + ', ' + longitude + '</td>');
      var last_row = $('#saved_locations_table tr').last();
      last_row.after(row);
    } else if (data.indexOf('FAIL') === 0) {
      var message = data.substr(5);
      // 5 is index of FAIL\n, so we only have the message
      alert(message);
    } else {
      alert('Unknown result: ' + data);
    }
  });
}
