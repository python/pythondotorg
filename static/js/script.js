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

/* Run a log for testing */
console.log( "hastouch=" + hastouch ); 
console.log( "hasplaceholder=" + hasplaceholder );
console.log( "hasgeneratedcontent=" + hasgeneratedcontent );
console.log( "is_ltie9=" + is_ltie9 );


/* For mobile, hide the iOS toolbar on initial page load */
/* /mobile/i.test(navigator.userAgent) && !window.location.hash && setTimeout(function () { window.scrollTo(0, 0); }, 1000); */


/*
 * WE NEED the Following: 
 
 1) Make the body text larger, make the body text smaller functions
 2) Something like FitText.js for numbers in the statistics widget
 
 */


/* Debulked onresize handler from @louis_remi. https://github.com/louisremi/jquery-smartresize */
function on_resize(c,t){onresize=function(){clearTimeout(t);t=setTimeout(c,100)};return c};


/* Variables to set to true later and check */
supernavs_loaded = false; 


/* Load progressive content. Must remember to also load them for IE 7 and 8 if needed */
on_resize(function() {
    
    // Check if a container is empty !$.trim( $('#mainnav').html() ).length
    
    /* 
     * "Watch" the body:after { content } to find out how wide the viewport is. 
     * Thanks to http://adactio.com/journal/5429/ for details about this method
     */
    mq_tag = window.getComputedStyle(document.body,':after').getPropertyValue('content');
    console.log( "media query tag=" + mq_tag ); 
    
    if ( mq_tag.indexOf("animatebody") !=-1 ) {
        $("body").animate({ scrollTop: $('#python-network').offset().top }, 500);
        console.log( "! animatebody has fired" );
    }
    
    /* Load a supernav into the About dropdown */
    if ( mq_tag.indexOf("load_supernavs") !=-1 && ! supernavs_loaded || is_ltie9 ) {
        
        $.get("/supernav-python-about",
            function(data){
             $('li#about .subnav').append( data );
            }, "html");
        $('li#about').addClass("with-supernav"); 
        
        $.get("/supernav-python-downloads",
            function(data){
             $('li#downloads .subnav').append( data ); 
            }, "html"); 
        $('li#downloads').addClass("with-supernav"); 
        
        $.get("/supernav-python-documentation",
            function(data){
             $('li#documentation .subnav').append( data ); 
            }, "html"); 
        $('li#documentation').addClass("with-supernav"); 
        
        $.get("/supernav-python-community",
            function(data){
             $('li#community .subnav').append( data ); 
            }, "html"); 
        $('li#community').addClass("with-supernav"); 
        
        $.get("/supernav-python-success-stories",
            function(data){
             $('li#success-stories .subnav').append( data ); 
            }, "html"); 
        $('li#success-stories').addClass("with-supernav"); 
        
        $.get("/supernav-python-blog",
            function(data){
             $('li#blog .subnav').append( data ); 
            }, "html"); 
        $('li#blog').addClass("with-supernav"); 
        
        $.get("/supernav-python-events",
            function(data){
             $('li#events .subnav').append( data ); 
            }, "html"); 
        $('li#events').addClass("with-supernav"); 
        
        supernavs_loaded = true; 
        console.log( "! supernavs_loaded has fired" );
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
    
})(); // the magic extra () makes this function fire on page load


/* Initiate some other functions as well. Fires on first page load or when called. */
$().ready(function() {
    
    /* Animate some scrolling for smoother transitions */
    
    /* ! Not currently working in IE10/Windows 8, Chrome for Android, Firefox (all versions)... something about the animate() function */
    $("#close-python-network").click(function() {
        $('body, html').animate({ scrollTop: $('#python-network').offset().top }, 400);
        return false; 
    }); 
    $("#python-network").click(function() {
        $('body, html').animate({ scrollTop: $('#top').offset().top }, 400);
        return false; 
    });
    $("#site-map-link").click(function() {
        $('body, html').animate({ scrollTop: $('#site-map').offset().top }, 600);
        return false; 
    });
    $("#back-to-top-1, #back-to-top-2").click(function() {
        $("body").animate({ scrollTop: $('#python-network').offset().top }, 600);
        return false; 
    }); 
    
    
    /* Treat the drop down menus in the main nav like select lists for touch devices */
    if ( hastouch ) {
        $(".main-navigation .tier-1 > a").click(function() { 
            $(".subnav").removeClass( 'touched' );
            $(this).next( '.subnav' ).addClass( 'touched' );
            return false; 
        });
        $(".close-for-touch").click(function() {
            $(this).offsetParent().offsetParent().removeClass( 'touched' );
            return false;  
        }); 
        
        $(".winkwink-nudgenudge .tier-1 > a").click(function() { 
            $(".subnav").removeClass( 'touched' );
            $(this).next( '.subnav' ).addClass( 'touched' );
            return false; 
        });
        $(".adjust-font-size .tier-1 > a").click(function() { 
            $(".subnav").removeClass( 'touched' );
            $(this).next( '.subnav' ).addClass( 'touched' );
            return false; 
        });
    }
    
    
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
    if ( hasplaceholder == false ) {
        
        /* polyfill from hagenburger: https://gist.github.com/379601 */
        $('[placeholder]').focus(function() {
            var input = $(this);
            if (input.val() == input.attr('placeholder')) {
                input.val('');
                input.removeClass('placeholder');
            }
        }).blur(function() {
            var input = $(this);
            if (input.val() == '' || input.val() == input.attr('placeholder')) {
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
    
    
    /* Non-media query enabled browsers need any critical content on page load. */
    if ( is_ltie9 ) {
        //$( '#mainnav' ). load( 'components/navigation.php' ); 
        
        //console.log( "! loadmainnav has fired because this is a non-media-query browser" );
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
    'undefined' && document.documentElement.clientWidth != 0) {
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


/*
 * add class to nav element of current url
 */
$(function() {
    $('#mainnav li.tier-1 > a[href^="/' + location.pathname.split("/")[1] + '"]').parent('li').addClass('selected');
});
