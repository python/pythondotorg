/* Use this script if you need to support IE 7 and IE 6. */

window.onload = function() {
	function addIcon(el, entity) {
		var html = el.innerHTML;
		el.innerHTML = '<span style="font-family: \'Pythonicon\'">' + entity + '</span>' + html;
	}
	var icons = {
			'icon-alert' : '&#xe000;',
			'icon-arrow-down' : '&#xe001;',
			'icon-arrow-left' : '&#xe002;',
			'icon-arrow-right' : '&#xe003;',
			'icon-arrow-up' : '&#xe004;',
			'icon-calendar' : '&#xe005;',
			'icon-close' : '&#xe006;',
			'icon-code' : '&#xe007;',
			'icon-documentation' : '&#xe008;',
			'icon-email' : '&#xe00a;',
			'icon-facebook' : '&#xe00b;',
			'icon-feed' : '&#xe00c;',
			'icon-freenode' : '&#xe00d;',
			'icon-get-started' : '&#xe00e;',
			'icon-github' : '&#xe00f;',
			'icon-help' : '&#xe011;',
			'icon-pypi' : '&#xe014;',
			'icon-python' : '&#xe015;',
			'icon-python-alt' : '&#xe016;',
			'icon-search' : '&#xe017;',
			'icon-sitemap' : '&#xe018;',
			'icon-stack-overflow' : '&#xe019;',
			'icon-statistics' : '&#xe01a;',
			'icon-success-stories' : '&#xe01b;',
			'icon-text-resize' : '&#xe01c;',
			'icon-thumbs-down' : '&#xe01d;',
			'icon-thumbs-up' : '&#xe01e;',
			'icon-twitter' : '&#xe01f;',
			'icon-versions' : '&#xe020;',
			'icon-community' : '&#xe021;',
			'icon-download' : '&#xe009;',
			'icon-news' : '&#xe012;',
			'icon-jobs' : '&#xe013;',
			'icon-beginner' : '&#xe022;',
			'icon-moderate' : '&#xe023;',
			'icon-advanced' : '&#xe024;',
			'icon-search-alt' : '&#xe025;'
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
