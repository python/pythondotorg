var hastouch = Modernizr.touch;
var hasplaceholder = Modernizr.placeholder;
var is_ltie9 = $("html").hasClass( "lt-ie9" );

if( !window.Retina ) {
    var is_retina = false;
    $("html").addClass( "no-retina" );
} else {
    var is_retina = Retina.isRetina();
    if ( is_retina ) {
        $("html").addClass( "retina" );
    } else {
        $("html").addClass( "no-retina" );
    }
}


/* For mobile, hide the iOS toolbar on initial page load */
/* /mobile/i.test(navigator.userAgent) && !window.location.hash && setTimeout(function () { window.scrollTo(0, 0); }, 1000); */


/* Load, Resize and Orientation change methods
 * http://css-tricks.com/forums/discussion/16123/reload-jquery-functions-on-ipad-orientation-change/p1 */

//initial load
$(window).load(on_resize_orientationchange);

//bind to resize
$(window).resize(on_resize_orientationchange);

//check for the orientation event and bind accordingly
if (window.DeviceOrientationEvent) {
    window.addEventListener('orientationchange', on_resize_orientationchange, false);
}


/* Variables to set to true later and check */
supernavs_loaded = false;

/* Load progressive content. Must remember to also load them for IE 7 and 8 if needed */
function on_resize_orientationchange() {

    // Check if a container is empty !$.trim( $('#mainnav').html() ).length

    /*
     * "Watch" the body:after { content } to find out how wide the viewport is.
     * Thanks to http://adactio.com/journal/5429/ for details about this method
     */
    mq_tag = window.getComputedStyle(document.body,':after').getPropertyValue('content');

    /* Click the menu button and add a class to the body for a "drawer" */
    if ( mq_tag.indexOf("drawer_navigation") !=-1 ) {

        /* TO DO: Look for a left-right swipe action (on the #touchnav-wrapper?) and also trigger the menu to open/close */
        $( "#site-map-link" ).click( function() {
            $("body").toggleClass("show-sidemenu");
            //console.log( "! #site-map-link has been tapped" );
            return false;
        });

    } else {

        /* If "drawer_navigation" is not present, treat the Menu button as a scroller down to the footer */
        $("#site-map-link").click(function() {
            $('body, html').animate({ scrollTop: $('#site-map').offset().top }, 500);
            return false;
        });
    }


    /* Load a supernav into the About dropdown */
    if ( ! hastouch ) {

        if ( mq_tag.indexOf("load_supernavs") !=-1 && ! supernavs_loaded || is_ltie9 ) {

            $.get("/box/supernav-python-about/",
                function(data){
                 $('.python-navigation li#about .subnav').append( data );
                }, "html");
            $('li#about').addClass("with-supernav");

            $.get("/box/supernav-python-downloads/",
                function(data){
                 $('li#downloads .subnav').append( data );
                    /* Toggle Download buttons by OS detection */
                    if (navigator.appVersion.indexOf("Win")!=-1) {
                        $('.download-unknown').hide();
                        $('.download-os-windows').show();
                    }
                    if (navigator.appVersion.indexOf("Mac")!=-1) {
                        $('.download-unknown').hide();
                        $('.download-os-macos').show();
                    }
                    if (navigator.appVersion.indexOf("X11")!=-1) {
                        $('.download-unknown').hide();
                        $('.download-os-source').show();
                    }
                    if (navigator.appVersion.indexOf("Linux")!=-1) {
                        $('.download-unknown').hide();
                        $('.download-os-source').show();
                    }
                }, "html");
            $('li#downloads').addClass("with-supernav");

            $.get("/box/supernav-python-documentation/",
                function(data){
                 $('li#documentation .subnav').append( data );
                }, "html");
            $('li#documentation').addClass("with-supernav");

            $.get("/box/supernav-python-community/",
                function(data){
                 $('li#community .subnav').append( data );
                }, "html");
            $('li#community').addClass("with-supernav");

            $.get("/box/supernav-python-success-stories/",
                function(data){
                 $('li#success-stories .subnav').append( data );
                }, "html");
            $('li#success-stories').addClass("with-supernav");

            $.get("/box/supernav-python-blog/",
                function(data){
                 $('li#blog .subnav').append( data );
                }, "html");
            $('li#blog').addClass("with-supernav");

            $.get("/box/supernav-python-events/",
                function(data){
                 $('li#events .subnav').append( data );
                }, "html");
            $('li#events').addClass("with-supernav");

            supernavs_loaded = true;
            //console.log( "! supernavs_loaded has fired" );
        }
    }

};


function getPythonStatus() {
    $.ajax({
        url: "https://2p66nmmycsj3.statuspage.io/api/v2/status.json"
    }).done(function(data) {
        var className = 'python-status-indicator-' + data.status.indicator;
        $('#python-status-indicator')
            .removeClass('python-status-indicator-default')
            .addClass(className)
            .parent()
            .attr('title', data.status.description);
    });
};

/* Initiate some other functions as well. Fires on first page load or when called. */
$().ready(function() {

    var $container = $('#container');
    $container.masonry({ itemSelector: '.tier-1' });
    var mq = window.matchMedia('all and (max-width: 400px)');
    var check_masonry = function (msnry) {
        if(msnry.matches) {
            $container.masonry('destroy');
        } else {
            $container.masonry();
        }
    };
    check_masonry(mq);
    mq.addListener(check_masonry);

    /*
     * Ensure PythonAnywhere is open for business and only fires on homepage
     */
    if($('body#homepage').length) {
        var launch_shell = $('#launch-shell');
        launch_shell.toggle();
        $.get('https://console.python.org/python-dot-org-live-consoles-status', function (data) {
            if(data.status == 'OK') {
                launch_shell.toggle();
            }
         });
    }
    /* Animate some scrolling for smoother transitions */

    /* ! Not currently working in IE10/Windows 8, Chrome for Android, Firefox (all versions)... something about the animate() function */
    $("#close-python-network").click(function() {
        $('body, html').animate({ scrollTop: $('#python-network').offset().top }, 300);
        return false;
    });

    $("#python-network").click(function() {
        $('body, html').animate({ scrollTop: $('#top').offset().top }, 300);
        return false;
    });

    $("#back-to-top-1, #back-to-top-2").click(function() {
        $("body").animate({ scrollTop: $('#python-network').offset().top }, 500);
        return false;
    });

    /*
     * Load interactive shell on the homepage.
    */
    function loadShell(e) {
        var CONSOLE_URL = 'https://console.python.org/python-dot-org-console/';
        e.preventDefault();
        shellDiv = $($(e.target).data('shell-container'));

        // The iframe's DIV containing the shell has a min-height: 300px
        var shellHeight = 300;
        shellDiv.animate({height: shellHeight});
        var iframe = $('<iframe>').width('100%').height(shellHeight);
        $(iframe).attr('src', CONSOLE_URL);
        shellDiv.html(iframe);
    }
    $('#start-shell').click(loadShell);

    /*
     * Load a slideshow on the homepage. Set the animationtype and detect for the library first.
     */
    if ( hastouch ) {
        var animationtype = "slide";
    } else {
        var animationtype = "fade";
    }
    if ( !window.flexslider ) {

        /* Grab body and html tags only once */
        var body = $('body');
        var html = $('html');

        if ( body.hasClass( 'home' ) ) {

            html.addClass( "flexslide" );

            $('#dive-into-python').flexslider({
                animation: animationtype,
                direction: 'horizontal',
                animationLoop: true,
                slideshow: true,
                slideshowSpeed: 8000,
                animationSpeed: 600,
                randomize: false,
                smoothHeight: false,
                pauseOnAction: true,
                pauseOnHover: true,
                useCSS: true, // use CSS transitions if available
                controlNav: true, // Create navigation for paging control of each slide
                directionNav: false, // Create navigation for previous/next navigation
                prevText: "Prev.",
                nextText: "Next",
                touch: hastouch,
                start: function(slider){
                    $(this).fadeIn();
                    $('body').removeClass('loading');
                }
            });

        }

        if( body.hasClass('psf') ) {
            html.addClass( "flexslide" );
            // PSF Sponsor rotation
            $('#sponsor-rotation').flexslider({
                animation: 'slide',
                direction: 'horizontal',
                animationLoop: true,
                slideshow: true,
                slideshowSpeed: 8000,
                animationSpeed: 600,
                randomize: true,
                smoothHeight: false,
                pauseOnAction: true,
                pauseOnHover: true,
                controlNav: false,
                directionNav: false,
                useCSS: true, // use CSS transitions if available
                touch: hastouch
            });
        }

    } else {
        $("html").addClass( "no-flexslide" );
    }


    /*
     * Change or store the body font-size and save it into a cookie
     * Scales the font-size up or down by about 2 pixels.
     * Requires jQuery.cookie.js. Only load for touch devices.
     */
    if ( window.cookie ) {
        if ( hastouch ) {

            var $cookie_name = "Python-FontSize";
            var elem = "body";
            var originalFontSize = $(elem).css("font-size");

            // if exists load saved value, otherwise store it
            if($.cookie($cookie_name)) {
                var $getSize = $.cookie($cookie_name);
                $(elem).css({fontSize : $getSize + ($getSize.indexOf("px")!=-1 ? "" : "px")}); // IE fix for double "pxpx" error
            } else {
                $.cookie($cookie_name, originalFontSize, { expires: 365 }); // 365 days
            }

            // reset link
            $(".text-reset").bind("click", function() {
                $(elem).css("font-size", originalFontSize);
                $.cookie($cookie_name, originalFontSize);
                return false;
            });

            // text "A+" link
            $(".text-grow").bind("click", function() {
                var currentFontSize = $(elem).css("font-size");
                var currentFontSizeNum = parseFloat(currentFontSize, 10);
                var newFontSize = Math.round( currentFontSizeNum*1.125 );
                if (newFontSize) {
                    $(elem).css("font-size", newFontSize);
                    $.cookie($cookie_name, newFontSize);
                }
                return false;
            });

            // text "A-" link
            $(".text-shrink").bind("click", function() {
                var currentFontSize = $(elem).css("font-size");
                var currentFontSizeNum = parseFloat(currentFontSize, 10);
                var newFontSize = Math.round( currentFontSizeNum*0.89 );
                if (newFontSize) {
                    $(elem).css("font-size", newFontSize);
                    $.cookie($cookie_name, newFontSize);
                }
                return false;
            });
        } // end hastouch
    }

    /* If there is no HTML5 placeholder present, run a javascript equivalent */
    if ( hasplaceholder === false ) {

        /* polyfill from hagenburger: https://gist.github.com/379601 */
        $('[placeholder]').focus(function() {
            var input = $(this);
            if (input.val() == input.attr('placeholder')) {
                input.val('');
                input.removeClass('placeholder');
            }
        }).blur(function() {
            var input = $(this);
            if (input.val() === '' || input.val() == input.attr('placeholder')) {
                input.addClass('placeholder');
                input.val(input.attr('placeholder'));
            }
        }).blur().parents('form').submit(function() {
            $(this).find('[placeholder]').each(function() {
                var input = $(this);
                if (input.val() == input.attr('placeholder')) {
                    input.val('');
                }
            })
        });
    }

    /*
     * Add a class to the selected radio/checkbox parent label
     * Requires inputs to be nested in labels:
     * <label for="checkbox2"><input id="checkbox2" name="checkbox" type="checkbox">Choice B</label>
     * <label for="radio1"><input id="radio1" name="radio" type="radio" checked="checked">Option 1</label>
     */
    $('input:radio').click(function() {
        $('label:has(input:radio:checked)').addClass('active');
        $('label:has(input:radio:not(:checked))').removeClass('active');
    });
    $('input:checkbox').click(function() {
        $('label:has(input:checkbox:checked)').addClass('active');
        $('label:has(input:checkbox:not(:checked))').removeClass('active');
    });
    /* Loop through them on initial page load as well */
    $('input:radio').each(function() {
        $('label:has(input:radio:checked)').addClass('active');
    });
    $('input:checkbox').each(function() {
        $('label:has(input:checkbox:checked)').addClass('active');
    });

    getPythonStatus();
});
