/**
 * Add support fo CSS3 box-sizing: border-box model for IE6 and IE7
 * 
 * @author Alberto Gasparin http://albertogasparin.it/
 * @version 1.1, License MIT
 * 
 **/

var borderBoxModel = (function(elements, value) {
  var element, cs, s, width, height;
  
  // cycle through all DOM elements
  for (var i=0, max=elements.length; i < max; i++) {
    element = elements[i];
    s = element.style;
    cs = element.currentStyle;
    
    // check if box-sizing is specified and is equal to border-box
    if(s.boxSizing == value || s["box-sizing"] == value
       || cs.boxSizing == value || cs["box-sizing"] == value) {
      
      // change width and height
      try {
        apply();
      } catch(e) {}
    }
  }
  
  function apply() {
    
    width = parseInt(cs.width, 10) || parseInt(s.width, 10);
    height = parseInt(cs.height, 10) || parseInt(s.height, 10);
    
    // if width is declared (and not 'auto','',...)
    if(width) {
      
      var // border value could be 'medium' so parseInt returns NaN
          borderLeft = parseInt(cs.borderLeftWidth || s.borderLeftWidth, 10) || 0,
          borderRight = parseInt(cs.borderRightWidth || s.borderRightWidth, 10) || 0,
          
          paddingLeft = parseInt(cs.paddingLeft || s.paddingLeft, 10),
          paddingRight = parseInt(cs.paddingRight || s.paddingRight, 10),
          
          horizSum = borderLeft + paddingLeft + paddingRight + borderRight;
      
      // remove from width padding and border two times if != 0
      if(horizSum) {
        s.width = width - horizSum; //width ? width - horizSum * 2 : styleWidth - horizSum;
      }
    }
    
    // if height is declared (and not 'auto','',...)
    if(height) {
      
      var // border value could be 'medium' so parseInt returns NaN
          borderTop = parseInt(cs.borderTopWidth || s.borderTopWidth, 10) || 0,
          borderBottom = parseInt(cs.borderBottomWidth || s.borderBottomWidth, 10) || 0,
          
          paddingTop = parseInt(cs.paddingTop || s.paddingTop, 10),
          paddingBottom = parseInt(cs.paddingBottom || s.paddingBottom, 10),
          
          vertSum = borderTop + paddingTop + paddingBottom + borderBottom;
      
      // remove from height padding and border two times if != 0
      if(vertSum) {
        s.height = height - vertSum; //height ? height - vertSum * 2 : styleHeight - vertSum;
      }
    }
  }
  
})(document.getElementsByTagName('*'), 'border-box');