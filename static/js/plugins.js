// usage: log('inside coolFunc', this, arguments);
// paulirish.com/2009/log-a-lightweight-wrapper-for-consolelog/
window.log = function f(){ log.history = log.history || []; log.history.push(arguments); if(this.console) { var args = arguments, newarr; args.callee = args.callee.caller; newarr = [].slice.call(args); if (typeof console.log === 'object') log.apply.call(console.log, console, newarr); else console.log.apply(console, newarr);}};

// make it safe to use console.log always
(function(a){function b(){}for(var c="assert,count,debug,dir,dirxml,error,exception,group,groupCollapsed,groupEnd,info,log,markTimeline,profile,profileEnd,time,timeEnd,trace,warn".split(","),d;!!(d=c.pop());){a[d]=a[d]||b;}})
(function(){try{console.log();return window.console;}catch(a){return (window.console={});}}());


/*!
 * jQuery Cookie Plugin v1.3.1
 * https://github.com/carhartl/jquery-cookie
 *
 * Copyright 2013 Klaus Hartl
 * Released under the MIT license
 */
(function(factory){if(typeof define==='function'&&define.amd&&define.amd.jQuery){define(['jquery'],factory);}else{factory(jQuery);}}(function($){var pluses=/\+/g;function raw(s){return s;}
function decoded(s){return decodeURIComponent(s.replace(pluses,' '));}
function converted(s){if(s.indexOf('"')===0){s=s.slice(1,-1).replace(/\\"/g,'"').replace(/\\\\/g,'\\');}
try{return config.json?JSON.parse(s):s;}catch(er){}}
var config=$.cookie=function(key,value,options){if(value!==undefined){options=$.extend({},config.defaults,options);if(typeof options.expires==='number'){var days=options.expires,t=options.expires=new Date();t.setDate(t.getDate()+days);}
value=config.json?JSON.stringify(value):String(value);return(document.cookie=[encodeURIComponent(key),'=',config.raw?value:encodeURIComponent(value),options.expires?'; expires='+options.expires.toUTCString():'',options.path?'; path='+options.path:'',options.domain?'; domain='+options.domain:'',options.secure?'; secure':''].join(''));}
var decode=config.raw?raw:decoded;var cookies=document.cookie.split('; ');var result=key?undefined:{};for(var i=0,l=cookies.length;i<l;i++){var parts=cookies[i].split('=');var name=decode(parts.shift());var cookie=decode(parts.join('='));if(key&&key===name){result=converted(cookie);break;}
if(!key){result[name]=converted(cookie);}}
return result;};config.defaults={};$.removeCookie=function(key,options){if($.cookie(key)!==undefined){$.cookie(key,'',$.extend(options,{expires:-1}));return true;}
return false;};}));


/*! Retina.js
 * https://github.com/imulus/retinajs/blob/master/src/retina.js
 * Copyright (C) 2012 Ben Atkin
 * MIT License.
 */
(function(){var root=(typeof exports=='undefined'?window:exports);var config={check_mime_type:true};root.Retina=Retina;function Retina(){}
Retina.configure=function(options){if(options===null)options={};for(var prop in options)config[prop]=options[prop];};Retina.init=function(context){if(context===null)context=root;var existing_onload=context.onload||new Function;context.onload=function(){var images=document.getElementsByTagName("img"),retinaImages=[],i,image;for(i=0;i<images.length;i++){image=images[i];retinaImages.push(new RetinaImage(image));}
existing_onload();}};Retina.isRetina=function(){var mediaQuery="(-webkit-min-device-pixel-ratio: 1.5),\
                      (min--moz-device-pixel-ratio: 1.5),\
                      (-o-min-device-pixel-ratio: 3/2),\
                      (min-resolution: 1.5dppx)";if(root.devicePixelRatio>1)
return true;if(root.matchMedia&&root.matchMedia(mediaQuery).matches)
return true;return false;};root.RetinaImagePath=RetinaImagePath;function RetinaImagePath(path){this.path=path;this.at_2x_path=path.replace(/\.\w+$/,function(match){return"@2x"+match;});}
RetinaImagePath.confirmed_paths=[];RetinaImagePath.prototype.is_external=function(){return!!(this.path.match(/^https?\:/i)&&!this.path.match('//'+document.domain));}
RetinaImagePath.prototype.check_2x_variant=function(callback){var http,that=this;if(this.is_external()){return callback(false);}else if(this.at_2x_path in RetinaImagePath.confirmed_paths){return callback(true);}else{http=new XMLHttpRequest;http.open('HEAD',this.at_2x_path);http.onreadystatechange=function(){if(http.readyState!=4){return callback(false);}
if(http.status>=200&&http.status<=399){if(config.check_mime_type){var type=http.getResponseHeader('Content-Type');if(type===null||!type.match(/^image/i)){return callback(false);}}
RetinaImagePath.confirmed_paths.push(that.at_2x_path);return callback(true);}else{return callback(false);}}
http.send();}}
function RetinaImage(el){this.el=el;this.path=new RetinaImagePath(this.el.getAttribute('src'));var that=this;this.path.check_2x_variant(function(hasVariant){if(hasVariant)that.swap();});}
root.RetinaImage=RetinaImage;RetinaImage.prototype.swap=function(path){if(typeof path=='undefined')path=this.path.at_2x_path;var that=this;function load(){if(!that.el.complete){setTimeout(load,5);}else{that.el.setAttribute('width',that.el.offsetWidth);that.el.setAttribute('height',that.el.offsetHeight);that.el.setAttribute('src',path);}}
load();}
if(Retina.isRetina()){Retina.init(root);}})();


/*
 *  Heading Anchors v1.0.2
 *  Copyright (c) 2010-2012 Rafaël Blais Masson <http://twitter.com/rafBM>
 *
 *  Freely distributable under the terms of the MIT license.
 *  <http://github.com/rafBM/heading-anchors>
 *
 
function HeadingAnchors(customSelector) {
        
    if (!document.querySelectorAll || ![].forEach)
        return; 
    
    var $ = function(selector) {
        return [].slice.call(document.querySelectorAll(selector), 0); 
    }; 
    
    var slugize = function(str) {
        return str.replace(/['’]/g, '').replace(/[^a-z0-9]+/ig, '-'); 
    }; 
    
    var existingSlugsNumbers = {},
        selector = customSelector ? customSelector : 'h2, h3, h4'; 
    
    $(selector).forEach(function(heading) {
        var anchor = document.createElement('a'),
            slug = slugize(heading.id ? heading.id : heading.textContent); 
        
        anchor.className = 'heading-anchor'; 
        
        // if slug #Foo-bar already exists, create #Foo-bar-2, #Foo-bar-3 and so on
        if (slug in existingSlugsNumbers) {
        existingSlugsNumbers[slug] += 1; 
        slug += '-' + existingSlugsNumbers[slug]; 
        } else {
        existingSlugsNumbers[slug] = 1; 
        }
        
        anchor.href = '#' + slug; 
        heading.id = slug; 
        
        anchor.innerHTML = '¶'; 
        heading.appendChild(anchor); 
    }); 
    
    var headingInHash = document.getElementById(location.hash.substr(1)); 
    if (headingInHash)
        window.scrollTo(0, headingInHash.offsetTop); 
}*/


/*! A fix for the iOS orientationchange zoom bug.
 * Script by @scottjehl, rebound by @wilto.
 * https://github.com/scottjehl/iOS-Orientationchange-Fix
 * MIT License.
 */
(function(w){if(!(/iPhone|iPad|iPod/.test(navigator.platform)&&navigator.userAgent.indexOf("AppleWebKit")>-1)){return;}
var doc=w.document;if(!doc.querySelector){return;}
var meta=doc.querySelector("meta[name=viewport]"),initialContent=meta&&meta.getAttribute("content"),disabledZoom=initialContent+",maximum-scale=1",enabledZoom=initialContent+",maximum-scale=10",enabled=true,x,y,z,aig;if(!meta){return;}
function restoreZoom(){meta.setAttribute("content",enabledZoom);enabled=true;}
function disableZoom(){meta.setAttribute("content",disabledZoom);enabled=false;}
function checkTilt(e){aig=e.accelerationIncludingGravity;x=Math.abs(aig.x);y=Math.abs(aig.y);z=Math.abs(aig.z);if(!w.orientation&&(x>7||((z>6&&y<8||z<8&&y>6)&&x>5))){if(enabled){disableZoom();}}
else if(!enabled){restoreZoom();}}
w.addEventListener("orientationchange",restoreZoom,false);w.addEventListener("devicemotion",checkTilt,false);})(this);
