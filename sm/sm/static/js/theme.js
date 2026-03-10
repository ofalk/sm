$(function () {
  // Topbar active tab support
  $(".topbar li").removeClass("active");

  var class_list = $("body").attr("class").split(/\s+/);
  $.each(class_list, function (index, item) {
    if (!item) return;
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

  // Cookie-synced checkboxes
  $(".cookie-sync").each(function () {
    var $cb = $(this);
    var cookieName = "srvmanager-" + $cb.attr("id");
    var checked = getCookie(cookieName);

    if (checked === "true" || checked === "") {
      $cb.prop("checked", true);
    } else if (checked === "false") {
      $cb.prop("checked", false);
    }

    $cb.on("change", function () {
      setCookie(cookieName, this.checked, 30);
      location.reload();
    });
  });

  // Responsive table helper: populate data-label from th
  $("table.table").each(function () {
    var $table = $(this);
    var $headers = $table.find("thead th");
    $table.find("tbody tr").each(function () {
      $(this)
        .find("td")
        .each(function (i) {
          var label = $headers.eq(i).text().trim();
          if (label && !$(this).attr("data-label")) {
            $(this).attr("data-label", label);
          }
        });
    });
  });

  // Command Palette (Ctrl+K or Cmd+K)
  var isMac = navigator.platform.toUpperCase().indexOf("MAC") >= 0;
  var cmdKeyHint = isMac ? "⌘K" : "Ctrl+K";

  // Update placeholders with OS-aware hints
  $("#commandSearch").attr(
    "placeholder",
    $("#commandSearch").attr("placeholder").replace("...", " (" + cmdKeyHint + ")")
  );
  $(".search-form input").attr(
    "placeholder",
    $(".search-form input").attr("placeholder") + " (" + cmdKeyHint + ")"
  );

  $(document).on("keydown", function (e) {
    if (e.key.toLowerCase() === "k" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      e.stopPropagation();
      $("#commandPalette").modal("show");
    }
  });

  $("#commandPalette").on("shown.bs.modal", function () {
    $("#commandSearch").focus();
  });

  var searchTimeout;
  var selectedIndex = -1;

  $("#commandSearch").on("input", function () {
    var q = $(this).val();
    clearTimeout(searchTimeout);
    if (q.length < 2) {
      $("#commandResults").html("");
      selectedIndex = -1;
      return;
    }

    searchTimeout = setTimeout(function () {
      $.get("/search/?q=" + encodeURIComponent(q) + "&ajax=1", function (data) {
        $("#commandResults").html(data);
        selectedIndex = -1;
      });
    }, 300);
  });

  $("#commandSearch").on("keydown", function (e) {
    var $items = $("#commandResults .list-group-item");
    if (!$items.length) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, $items.length - 1);
      updateSelection($items);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
      updateSelection($items);
    } else if (e.key === "Enter") {
      if (selectedIndex >= 0) {
        e.preventDefault();
        $items.eq(selectedIndex)[0].click();
      }
    }
  });

  function updateSelection($items) {
    $items.removeClass("active bg-primary text-white");
    if (selectedIndex >= 0) {
      var $selected = $items.eq(selectedIndex);
      $selected.addClass("active bg-primary text-white");
      $selected[0].scrollIntoView({ block: "nearest" });
    }
  }
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
