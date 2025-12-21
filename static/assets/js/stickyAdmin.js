
'use strict';

(function () {

    var stickyElement = $(".app-header.header.sticky"),
        stickyClass = "sticky-pin",
        stickyPos = 75,   // 일반이랑 맞추거나 원하는 값
        stickyHeight;

    if (!stickyElement.length) return;

    if (!stickyElement.next().hasClass('jumps-prevent')) {
        stickyElement.after('<div class="jumps-prevent"></div>');
    }

    function jumpsPrevent() {
        stickyHeight = stickyElement.outerHeight() || 0;
        stickyElement.css({ "margin-bottom": "-" + stickyHeight + "px" });
        stickyElement.next(".jumps-prevent").css({ "padding-top": stickyHeight + "px" });
    }
    jumpsPrevent();

    $(window).on("resize", jumpsPrevent);

    function stickerFn() {
        var winTop = $(this).scrollTop();
        if (winTop >= stickyPos) {
            stickyElement.addClass('stickyClass');
        } else {
            stickyElement.removeClass('stickyClass');
        }
    }
    stickerFn();
    $(window).on("scroll", stickerFn);

    // sidemenu
    $('.app-sidebar').on("scroll",function () {
        var s = $(".app-sidebar .ps__rail-y");
        if (s[0].style.top.split('px')[0] <= 60) {
            $('.app-sidebar').removeClass('sidemenu-scroll')
        } else {
            $('.app-sidebar').addClass('sidemenu-scroll')
        }

    })
    $('.app-sidebar').on("scroll",function () {
        var s = $(".app-sidebar .ps__rail-y");
        if (s[0].style.top.split('px')[0] <= 60) {
            $('.app-header').removeClass('res-scroll')
        } else {
            $('.app-header').addClass('res-scroll')
        }

    })

})();
