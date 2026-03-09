$(function () {
  // Topbar active tab support
  $(".topbar li").removeClass("active");

  var class_list = $("body").attr("class").split(/\s+/);
  $.each(class_list, function (index, item) {
    var selector;
    // Main menu entry
    selector = "ul.nav li#tab_" + item;
    $(selector).addClass("active");

    // Submenu / Dropdown items
    selector = "ul.nav a#" + item;
    $(selector).addClass("active");

    // Subnav - as seen in account pages
    selector = "a." + item;
    $(selector).addClass("active");
  });

  $("#account_logout, .account_logout").click(function (e) {
    e.preventDefault();
    $("#accountLogOutForm").submit();
  });
});

$(document).ajaxSend(function (event, xhr, settings) {
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != "") {
      var cookies = document.cookie.split(";");
      for (var i = 0; i < cookies.length; i++) {
        var cookie = jQuery.trim(cookies[i]);
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) == name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  function sameOrigin(url) {
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = "//" + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (
      url == origin ||
      url.slice(0, origin.length + 1) == origin + "/" ||
      url == sr_origin ||
      url.slice(0, sr_origin.length + 1) == sr_origin + "/" ||
      // or any other URL that isn't scheme relative or absolute i.e relative.
      !/^(\/\/|http:|https:).*/.test(url)
    );
  }
  function safeMethod(method) {
    return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
  }

  if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
  }
});

function setCookie(c_name, value, exdays) {
  var exdate = new Date();
  exdate.setDate(exdate.getDate() + exdays);
  var c_value =
    escape(value) + (exdays == null ? "" : "; expires=" + exdate.toUTCString());
  document.cookie = c_name + "=" + c_value;
}

function getCookie(c_name) {
  var i,
    x,
    y,
    ARRcookies = document.cookie.split(";");
  for (i = 0; i < ARRcookies.length; i++) {
    x = ARRcookies[i].substr(0, ARRcookies[i].indexOf("="));
    y = ARRcookies[i].substr(ARRcookies[i].indexOf("=") + 1);
    x = x.replace(/^\s+|\s+$/g, "");
    if (x == c_name) {
      return unescape(y);
    }
  }
  return "";
}
