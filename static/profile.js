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
    $('div.location').text('Current location: Your browser sucks');
  }
}

function success_callback(p) {
  lon = p.coords.longitude.toFixed(2);
  lat = p.coords.latitude.toFixed(2);
  $('div.location').text('Current location: Lat=' + lat + ', Lon=' + lon);
}

function error_callback(p) {
  if(errorCount++ < 6)
    findLocation();
  else
    $('div.location').text('Current location: The Moon');
}

$(document).ready(function() {
  $('#create_saved_location_lightbox').dialog({
    autoOpen: false,
    height: 375,
    width: 375,
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
  $('div.location').text('Current location: Searching...');
  errorCount=0;
}

function createSavedLocation(name, latitude, longitude) {
  $.post('/user/location', {name: name, latitude: latitude, longitude: longitude}, function(data) {
    row = $('<tr></tr>');
    row.append('<td class="name">' + name + '</td>');
    row.append('<td class="coords">(' + latitude + ', ' + longitude + ')</td>');
    var last_row = $('#saved_locations_table tr').last().prev();
    last_row.after(row);
  });
}