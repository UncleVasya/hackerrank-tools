/**
 * @fileOverview This file acts as the central import point for the other JavaScript files that make
 *               up the visualizer.
 */

namespace_vis = {};
namespace_vis.scripts = [];

$import('Util');
$import('Cell');
$import('VisContainer');
$import('VisApplication');
$import('Buttons');
$import('Config');
$import('Const');
$import('Director');
$import('ImageManager');
$import('LifeSimulator');
$import('Replay');
$import('CanvasElement');

/**
 * Imports a file in Java package notation.
 * 
 * @param {String} file
 *        the 'package' name
 */
function $import(file) {
	var ends_with = function(str, pat) {
		return str.slice(-pat.length) == pat;
	};
	var scripts = document.getElementsByTagName("script");
	if (namespace_vis.$import_base === undefined) {
		for ( var i = 0, len = scripts.length; i < len; ++i) {
			if (ends_with(scripts[i].src, 'visualizer.js')) {
				var pathLen = scripts[i].src.lastIndexOf('/') + 1;
				namespace_vis.$import_base = scripts[i].src.substr(0, pathLen);
				break;
			}
		}
	}
	file = namespace_vis.$import_base + file.replace(/[.]/g, '/') + '.js';
	for (i = 0; i < scripts.length; i++) {
		if (scripts[i].src === file) {
			return;
		}
	}
    namespace_vis.scripts.push(file);
	document.write('<script src="' + file + '"></script>');
}
