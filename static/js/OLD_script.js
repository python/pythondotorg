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


var vp_width = getViewport()[0]; 
//var vp_height = getViewport()[1]; 
var is_small =  is_small( vp_width ); /*boolean*/
var is_medium =  is_medium( vp_width ); /*boolean*/
var is_large=  is_large( vp_width ); /*boolean*/

/* Run a log for testing */
console.log( "hastouch=" + hastouch ); 
console.log( "hasplaceholder=" + hasplaceholder );
console.log( "hasgeneratedcontent=" + hasgeneratedcontent );
console.log( "hasboxsizing=" + hasboxsizing );
console.log( "is_small=" + is_small ); 
console.log( "is_medium=" + is_medium ); 
console.log( "is_large=" + is_large ); 


/* For mobile, hide the iOS toolbar on initial page load */
/* /mobile/i.test(navigator.userAgent) && !window.location.hash && setTimeout(function () { window.scrollTo(0, 0); }, 1000); */


/*
 * WE NEED the Following: 
 1) For browsers that do not support the placeholder feature on input field, the header search bar will need a JS placeholder
 2) Something like FitText.js for numbers in the statistics widget
 3) Box-sizing: border-box is not supported by IE7 or lower. We'll need to impelment a polyfill in order to have our multi-column layouts support IE7 and lower: https://github.com/Schepp/box-sizing-polyfill 
 4) Instead of using our own functions to watch the viewport, use this technique instead? http://adactio.com/journal/5429/
 */

$().ready(function() {
    
    /* Scroll the top of the page down to the "Python Network" and hide the network on page load, Make it a visible animation. */
    if ( is_small ) {
        /* Not currently working in IE10/Windows 8, though is_small returns true */
        $("body").animate({ scrollTop: $('#python-network').offset().top }, 500);
    } 
    
    /* Animate some scrolling for smoother transitions */
    /* ! 
     * Not currently working in IE10/Windows 8, Chrome for Android, Firefox (all versions)... something about the animate() function 
     */
    $("#close-python-network").click(function() {
        $("body").animate({ scrollTop: $('#python-network').offset().top }, 400);
        return false; 
    }); 
    $("#python-network").click(function() {
        $("body").animate({ scrollTop: $('#top').offset().top }, 400);
        return false; 
    });
    $("#site-map-link").click(function() {
        $("body").animate({ scrollTop: $('#site-map').offset().top }, 600);
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
    
    /* When the screen is large enough, load the main navigation */
    if ( is_small == false ) {
        $( '#mainnav' ). load( 'components/navigation.html' ); 
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
 * Functions to help with viewport detection. 
 * Used in tandem with toCleanPx() which helps calculate px to em conversions.
 * MUST declare getViewport()[0] as a variable and pass it to this function.
 * These should match the major breakpoints that our Media Queries support 
 *
 * Could be a better way to do it, relying on the media queries themselves... http://adactio.com/journal/5429/
 */

/* Less than or equal to 32em (520px) */
function is_small( vp_width ) {
    // $(myEmValue).toCleanPx()
    return vp_width <= $(32).toCleanPx(); 
}

/* Greater than 40em (640px) and less than or equal to 58.75em (940px) */
function is_medium( vp_width ) {
    return vp_width > $(40).toCleanPx() && vp_width <= $(58.75).toCleanPx(); 
}

/* Greater than 58.75em (940px) */
function is_large( vp_width ) {
    return vp_width > $(58.75).toCleanPx(); 
}


/*
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
 * DELETE LATER -- DEV ONLY
 * J's "make the browser tell me how big the viewport is on resize" script. 
 */

$('#test-window-size').html(''+getViewport()+'');
$(window).resize(function() {
	$('#test-window-size').html(''+getViewport()+'');
}); 