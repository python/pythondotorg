/* Use this script if you need to support IE 7 and IE 6. */

window.onload = function() {
	function addIcon(el, entity) {
		var html = el.innerHTML;
		el.innerHTML = '<span style="font-family: \'Pythonicon\'">' + entity + '</span>' + html;
	}
	var icons = {
			'icon-arrow-up' : '&#xe001;',
			'icon-arrow-down' : '&#xe002;',
			'icon-arrow-left' : '&#xe003;',
			'icon-arrow-right' : '&#xe004;',
			'icon-search' : '&#xe005;',
			'icon-search-alt' : '&#xe006;',
			'icon-text-resize' : '&#xe007;',
			'icon-documentation' : '&#xe008;',
			'icon-pypi' : '&#xe009;',
			'icon-jobs' : '&#xe00a;',
			'icon-beginner' : '&#xe00b;',
			'icon-moderate' : '&#xe00c;',
			'icon-advanced' : '&#xe00d;',
			'icon-statistics' : '&#xe00e;',
			'icon-success-stories' : '&#xe00f;',
			'icon-versions' : '&#xe010;',
			'icon-community' : '&#xe011;',
			'icon-news' : '&#xe012;',
			'icon-calendar' : '&#xe013;',
			'icon-get-started' : '&#xe014;',
			'icon-close' : '&#xe015;',
			'icon-sitemap' : '&#xe016;',
			'icon-email' : '&#xe017;',
			'icon-download' : '&#xe018;',
			'icon-code' : '&#xe019;',
			'icon-help' : '&#xe01a;',
			'icon-alert' : '&#xe01b;',
			'icon-feed' : '&#xe01c;',
			'icon-python' : '&#xe01d;',
			'icon-github' : '&#xe01e;',
			'icon-thumbs-up' : '&#xe01f;',
			'icon-thumbs-down' : '&#xe020;',
			'icon-facebook' : '&#xe021;',
			'icon-twitter' : '&#xe022;',
			'icon-google-plus' : '&#xe023;',
			'icon-freenode' : '&#xe024;',
			'icon-stack-overflow' : '&#xe000;'
		},
		els = document.getElementsByTagName('*'),
		i, attr, html, c, el;
	for (i = 0; i < els.length; i += 1) {
		el = els[i];
		attr = el.getAttribute('data-icon');
		if (attr) {
			addIcon(el, attr);
		}
		c = el.className;
		c = c.match(/icon-[^\s'"]+/);
		if (c && icons[c[0]]) {
			addIcon(el, icons[c[0]]);
		}
	}
};