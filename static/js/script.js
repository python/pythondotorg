/* 
 * Scripts for this specific project
 */

/*
 * Set variables that any script can use
 */
var hastouch = has_feature( "touch" ); 
var hasplaceholder = has_feature( "placeholder" );
var hasgeneratedcontent = has_feature( "generatedcontent" );
var hasboxsizing = has_feature( "boxsizing" );
var is_ltie9 = has_feature( "lt-ie9" );

/* Run a log for testing */
console.log( "hastouch=" + hastouch ); 
console.log( "hasplaceholder=" + hasplaceholder );
console.log( "hasgeneratedcontent=" + hasgeneratedcontent );
console.log( "hasboxsizing=" + hasboxsizing );
console.log( "is_ltie9=" + is_ltie9 );


/* 
 * "Listen" to the body:after { content } to find out how wide the viewport is. 
 * Thanks to http://adactio.com/journal/5429/ for details about this method
 */
//mq_tag = window.getComputedStyle(document.body,':after').getPropertyValue('content');
//console.log( "media query tag=" + mq_tag ); 


/* For mobile, hide the iOS toolbar on initial page load */
/* /mobile/i.test(navigator.userAgent) && !window.location.hash && setTimeout(function () { window.scrollTo(0, 0); }, 1000); */


/*
 * WE NEED the Following: 
 
 1) Make the body text larger, make the body text smaller functions
 2) Something like FitText.js for numbers in the statistics widget
 
 */


/* Variables to set to true later and check */
about_supernav_loaded = false; 
downloads_supernav_loaded = false; 
documentation_supernav_loaded = false; 
community_supernav_loaded = false; 
successstories_supernav_loaded = false; 
blog_supernav_loaded = false; 
events_supernav_loaded = false; 
local_meetups_loaded = false; 


/* Debulked onresize handler from @louis_remi. https://github.com/louisremi/jquery-smartresize */
function on_resize(c,t){onresize=function(){clearTimeout(t);t=setTimeout(c,100)};return c};


/* Proof of concept for loading progressive content. Must remember to also load them for IE 7 and 8 if needed (see above) */
on_resize(function() {
    
    // Check if a container is empty !$.trim( $('#mainnav').html() ).length
    
    /* "Watch" the content of the body:after element. Will change as media queries fire */
    mq_tag = window.getComputedStyle(document.body,':after').getPropertyValue('content');
    console.log( "media query tag=" + mq_tag ); 
    
    if ( mq_tag.indexOf("animatebody") !=-1 ) {
        $("body").animate({ scrollTop: $('#python-network').offset().top }, 500);
        console.log( "! animatebody has fired" );
    }
    
    /* Load a supernav into the About dropdown */
    if ( mq_tag.indexOf("about_supernav") !=-1 && ! about_supernav_loaded ) {
        $.get("supernav-python-about",
            function(data){
             $('li#about .subnav').append( data );
            }, "html");
        $('li#about').addClass("with-supernav"); 
        about_supernav_loaded = true; 
        console.log( "! about_supernav has fired" );
    }
    
    /* Load a supernav into the Downloads dropdown */
    if ( mq_tag.indexOf("downloads_supernav") !=-1 && ! downloads_supernav_loaded ) {
        $.get("supernav-python-downloads",
            function(data){
             $('li#downloads .subnav').append( data ); 
            }, "html"); 
        $('li#downloads').addClass("with-supernav"); 
        downloads_supernav_loaded = true; 
        console.log( "! downloads_supernav has fired" );
    }
    
    /* Load a supernav into the Documentation dropdown */
    if ( mq_tag.indexOf("documentation_supernav") !=-1 && ! documentation_supernav_loaded ) {
        $.get("supernav-python-documentation",
            function(data){
             $('li#documentation .subnav').append( data ); 
            }, "html"); 
        $('li#documentation').addClass("with-supernav"); 
        documentation_supernav_loaded = true; 
        console.log( "! documentation_supernav has fired" );
    }
    
    /* Load a supernav into the Community dropdown */
    if ( mq_tag.indexOf("community_supernav") !=-1 && ! community_supernav_loaded ) {
        $.get("supernav-python-community",
            function(data){
             $('li#community .subnav').append( data ); 
            }, "html"); 
        $('li#community').addClass("with-supernav"); 
        community_supernav_loaded = true; 
        console.log( "! community_supernav has fired" );
    }
    
    /* Load a supernav into the Success-stories dropdown */
    if ( mq_tag.indexOf("successstories_supernav") !=-1 && ! successstories_supernav_loaded ) {
        $.get("supernav-python-success-stories",
            function(data){
             $('li#success-stories .subnav').append( data ); 
            }, "html"); 
        $('li#success-stories').addClass("with-supernav"); 
        successstories_supernav_loaded = true; 
        console.log( "! successstories_supernav has fired" );
    }
    
    /* Load a supernav into the Blog dropdown */
    if ( mq_tag.indexOf("blog_supernav") !=-1 && ! blog_supernav_loaded ) {
        $.get("supernav-python-blog",
            function(data){
             $('li#blog .subnav').append( data ); 
            }, "html"); 
        $('li#blog').addClass("with-supernav"); 
        blog_supernav_loaded = true; 
        console.log( "! blog_supernav has fired" );
    }
    
    /* Load a supernav into the Events dropdown */
    if ( mq_tag.indexOf("events_supernav") !=-1 && ! events_supernav_loaded ) {
        $.get("supernav-python-events",
            function(data){
             $('li#events .subnav').append( data ); 
            }, "html"); 
        $('li#events').addClass("with-supernav"); 
        events_supernav_loaded = true; 
        console.log( "! events_supernav has fired" );
    }
    
    /* Load a Google Map into the Community landing page
    if ( mq_tag.indexOf("local_meetup_map") !=-1 && ! local_meetups_loaded ) {
        
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


$().ready(function() {
    
    /* Animate some scrolling for smoother transitions */
    /* ! 
     * Not currently working in IE10/Windows 8, Chrome for Android, Firefox (all versions)... something about the animate() function 
     */
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
    
    /* Treat the drop down menus in the main nav like select lists */
    if ( hastouch ) {
        $(".main-navigation .tier-1 > a").click(function() { 
            $(".subnav").removeClass( 'touched' );
            $(this).next( '.subnav' ).addClass( 'touched' );
            return false; 
        });
        $(".close-for-touch").click(function() {
            $(this).offsetParent().removeClass( 'touched' );
            return false;  
        }); 
    }
    
    /* If there is no box-sizing present (IE 7 & 8 mostly) run the javascript polyfill */
    if ( hasboxsizing == false ) {
        /*
         * @author Alberto Gasparin http://albertogasparin.it/
         * @version 1.1, License MIT
         */
var borderBoxModel=(function(elements,value){var element,cs,s,width,height;for(var i=0,max=elements.length;i<max;i++){element=elements[i];s=element.style;cs=element.currentStyle;if(s.boxSizing==value||s["box-sizing"]==value||cs.boxSizing==value||cs["box-sizing"]==value){try{apply();}catch(e){}}}
function apply(){width=parseInt(cs.width,10)||parseInt(s.width,10);height=parseInt(cs.height,10)||parseInt(s.height,10);if(width){var
borderLeft=parseInt(cs.borderLeftWidth||s.borderLeftWidth,10)||0,borderRight=parseInt(cs.borderRightWidth||s.borderRightWidth,10)||0,paddingLeft=parseInt(cs.paddingLeft||s.paddingLeft,10),paddingRight=parseInt(cs.paddingRight||s.paddingRight,10),horizSum=borderLeft+paddingLeft+paddingRight+borderRight;if(horizSum){s.width=width-horizSum;}}
if(height){var
borderTop=parseInt(cs.borderTopWidth||s.borderTopWidth,10)||0,borderBottom=parseInt(cs.borderBottomWidth||s.borderBottomWidth,10)||0,paddingTop=parseInt(cs.paddingTop||s.paddingTop,10),paddingBottom=parseInt(cs.paddingBottom||s.paddingBottom,10),vertSum=borderTop+paddingTop+paddingBottom+borderBottom;if(vertSum){s.height=height-vertSum;}}}})(document.getElementsByTagName('*'),'border-box');
    }
    
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