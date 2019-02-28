  // Look for any data-html-include elements, and include the content for them
  $('[data-html-include]').each(function() {
    $(this).load($(this).data('html-include'));
  });
