/*
 * Scripts for this specific project
 */
 
/*
 * Set variables that any script can use
 */
if( !window.Modernizr ) {
    var hastouch = has_feature( "touch" ),
        hasplaceholder = has_feature( "placeholder" ),
        hasgeneratedcontent = has_feature( "generatedcontent" ),
        is_ltie9 = has_feature( "lt-ie9" );
} else {
    var hastouch = false,
        hasplaceholder = false,
        hasgeneratedcontent = false,
        is_ltie9 = false;
}
 
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
 
 
/* "Watch" the body:after { content } to listen for functional tags at CSS breakpoints
 * Thanks to http://adactio.com/journal/5429/ for details about this method
 */
function mqtag( is_ltie9 ) {
    if ( is_ltie9 ) {
        return false;
    } else {
        return window.getComputedStyle(document.body,':after').getPropertyValue('content');
    }
}
var mq_tag = mqtag( is_ltie9 );
 
 
/*
 * Load, Resize and Orientation change methods
 * http://css-tricks.com/forums/discussion/16123/reload-jquery-functions-on-ipad-orientation-change/p1 
 */
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
 
    // Check again on resize/orientation change
    var mq_tag = mqtag( is_ltie9 );
    //console.log( "mq_tag=" + mq_tag );
    
 
    /* 
     * Set up the open/close navigation drawer effects for small screens. Adds classes. 
     * http://codepen.io/sturobson/pen/rAoBh 
     */
    if ( is_ltie9 === false && mq_tag.indexOf("navigation-drawer") !=-1  ) {
         
        $('.js-toggle-drawer').click(function(a) {
            a.preventDefault();
             
            $('body').toggleClass("active-nav"); 
            $(this).toggleClass("active-button"); 
        }); 
        // Reset all classes if click is present off the navigation area
        $(".js-close-drawer").on('click', function(a){
            a.preventDefault();
             
            $("body").removeClass('active-nav');
            $(".menu-button").removeClass("active-button");
        }); 
    } else {
        $('.js-toggle-drawer').click(function(a) {
            a.preventDefault();                 
        });
    }
 
};
 
 
/* Initiate some other functions as well. Fires on first page load or when called. */
$().ready(function() {
 
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
     * Navigation pattern for open/close of children and grandchildren
     */
    $('a.mainnav--toggle').click(function(nav) {
        nav.preventDefault();
        
        var togglethis = $(this).attr('href'); 
        $(togglethis).slideToggle("fast").toggleClass('closed'); 
        //$(togglethis).toggleClass('closed'); 
        $(this).toggleClass('open'); 
        $(this).prev('.mainnav--link').toggleClass('open'); 
    }); 
    
    
    // Make a nice "back to top" button that also opens the nav drawer for mobile
    if ($('.js-back-to-top').length > 0) {
        $('.js-back-to-top').click(function(btt) {
    		
    		var target = $(this.hash);
    		$('html,body').animate({ scrollTop: target.offset().top }, 500);
    		
    		$('body').toggleClass("active-nav"); 
    		$('.js-toggle-drawer').toggleClass("active-button"); 
    		
    		btt.preventDefault();
    	});
    }
    
 
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
        var body = $('body'),
            html = $('html');
 
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
                touch: hastouch,
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
    if ( !window.cookie ) {
        //console.log( "cookie.js has not loaded" );
    } else {
 
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
 
    /* Randomly show a success story based on weight */
    var success_divs = $("div.success-story-item");
    var weight_sum = 0;
    success_divs.each( function() {
        weight_sum += parseInt($(this).data('weight'), 10);
    });
 
    /* Random int between zero and weight_sum */
    var random_int = Math.floor(Math.random() * (weight_sum - 0 + 1)) + 0;
 
    /* Determine which to show based on weight */
    success_divs.each( function() {
        var current_weight = parseInt($(this).data('weight'), 10);
        if( random_int < current_weight ) {
            // Show
            $(this).show();
            return false;
        }
        random_int -= current_weight;
    });
 
    /* Handle case of only a single success story */
    if(success_divs.length == 1) {
        $("div.success-story-item").show();
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
 
 
    /* Trigger accordions where applicable */
    $("a.accordion-trigger").click(function() {
        var iden = jQuery(this).attr('href');
        //$(this).toggleClass("opened");
        $(iden).slideToggle();
    });
 
 
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
 
 
    /* Non-media query enabled browsers need any critical content on page load. */
    if ( is_ltie9 ) {
        //console.log( "! something has fired because this is a non-media-query browser" );
    }
 
});
 
 
/*
 * Function to help with feature detection.
 * Used in tandem with Modernizr for the best effect. Pass this function values of a Modernizr class name.
 */
function has_feature( feature ) {
    if ( $("html").hasClass( feature ) ) { return true; } else { return false; }
}