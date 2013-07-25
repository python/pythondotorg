/*
 * Scripts for this specific project
 */

/*
 * Set variables that any script can use
 */
var hastouch = has_feature( "touch" );
var hasplaceholder = has_feature( "placeholder" );
var hasgeneratedcontent = has_feature( "generatedcontent" );
var is_ltie9 = has_feature( "lt-ie9" );
var is_retina = Retina.isRetina();

/* Run a log for testing */
console.log( "hastouch=" + hastouch );
//console.log( "is_ltie9=" + is_ltie9 );
//console.log( "is_retina=" + is_retina );

if ( is_retina ) {
    $("html").addClass( "retina" ); 
} else {
    $("html").addClass( "no-retina" ); 
}


/* For mobile, hide the iOS toolbar on initial page load */
/* /mobile/i.test(navigator.userAgent) && !window.location.hash && setTimeout(function () { window.scrollTo(0, 0); }, 1000); */


/*
 * WE NEED the Following:

 1) Something like FitText.js for numbers in the statistics widget
 2) A down and dirty Retina detection kit to swap out what few images would benefit.

 */


/* Load, Resize and Orientation change methods 
 * http://css-tricks.com/forums/discussion/16123/reload-jquery-functions-on-ipad-orientation-change/p1 */

    //initial load
    $(window).load( function() { on_resize_orientationchange(); });
    
    //bind to resize
    $(window).resize( function() { on_resize_orientationchange(); });
    
    //check for the orientation event and bind accordingly
    if (window.DeviceOrientationEvent) { window.addEventListener('orientationchange', on_resize_orientationchange, false); } 


/* Variables to set to true later and check */
scroll_fired = false;
supernavs_loaded = false;


/* Load progressive content. Must remember to also load them for IE 7 and 8 if needed */
function on_resize_orientationchange() {

    // Check if a container is empty !$.trim( $('#mainnav').html() ).length


    /*
     * "Watch" the body:after { content } to find out how wide the viewport is.
     * Thanks to http://adactio.com/journal/5429/ for details about this method
     */
    mq_tag = window.getComputedStyle(document.body,':after').getPropertyValue('content');
    //console.log( "media query tag=" + mq_tag );


    /* Move the top nav (sister sites) out of the way for small screens */
    if ( mq_tag.indexOf("animatebody") !=-1 && ! scroll_fired ) {
        $('body, html').animate({ scrollTop: $('#python-network').offset().top }, 300);
        scroll_fired = true;
    }
    
    
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
                 $('li#about .subnav').append( data );
                }, "html");
            $('li#about').addClass("with-supernav");
    
            $.get("/box/supernav-python-downloads/",
                function(data){
                 $('li#downloads .subnav').append( data );
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
    
    
    /* Load a Google Map into the Community landing page
    if ( mq_tag.indexOf("local_meetup_map") !=-1 && ! local_meetups_loaded ) {

        $.getScript('//maps.google.com/maps/api/js?sensor="+hastouch+"');

        if (navigator.geolocation) {
            
            navigator.geolocation.getCurrentPosition(function(position){
                var latitude = position.coords.latitude;
                var longitude = position.coords.longitude;
                var coords = new google.maps.LatLng(latitude, longitude);
                
                var mapOptions = {
                    zoom: 15,
                    center: coords,
                    mapTypeControl: true,
                    navigationControlOptions: {
                        style: google.maps.NavigationControlStyle.SMALL
                    },
                    mapTypeId: google.maps.MapTypeId.ROADMAP
                };
                map = new google.maps.Map(
                    document.getElementById("#local_meetups"), mapOptions
                );
                var marker = new google.maps.Marker({
                    position: coords,
                    map: map,
                    title: "Your current location!"
                });
 
            });
        } else {
            alert("Geolocation API is not supported in your browser.");
        }
        local_meetups_loaded = true;
        console.log( "! local_meetups_map has fired" );
    } */

};


/* Initiate some other functions as well. Fires on first page load or when called. */
$().ready(function() {

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
     * Change or store the body font-size and save it into a cookie
     * Scales the font-size up or down by about 2 pixels.
     * Requires jQuery.cookie.js
     */
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
    if ( $("html").hasClass( feature ) ) {
        return true;
    } else {
        return false;
    }
}


/*
 * DELETE LATER -- DEV ONLY
 * Get the viewport dimensions. Edit this and refine as needed.
 * Used to bind media-query-like conditions to Javscript actions.
 */
function getViewport() {

    var viewPortWidth;
    var viewPortHeight;

    // the more standards compliant browsers (mozilla/netscape/opera/IE7) use window.innerWidth and window.innerHeight
    if (typeof window.innerWidth != 'undefined') {
        viewPortWidth = window.innerWidth,
        viewPortHeight = window.innerHeight
    }

    // IE6 in standards compliant mode (i.e. with a valid doctype as the first line in the document)
    else if (typeof document.documentElement != 'undefined'
    && typeof document.documentElement.clientWidth !=
    'undefined' && document.documentElement.clientWidth !== 0) {
        viewPortWidth = document.documentElement.clientWidth,
        viewPortHeight = document.documentElement.clientHeight
    }

    // older versions of IE
    else {
        viewPortWidth = document.getElementsByTagName('body')[0].clientWidth,
        viewPortHeight = document.getElementsByTagName('body')[0].clientHeight
    }
    return [viewPortWidth, viewPortHeight];
}


/*
 * J's "make the browser tell me how big the viewport is on resize" script.
 */
$('#test-window-size').html(''+getViewport()+'');
$(window).resize(function() {
	$('#test-window-size').html(''+getViewport()+'');
});
