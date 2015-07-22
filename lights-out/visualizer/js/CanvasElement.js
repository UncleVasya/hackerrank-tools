/**
 * @class A canvas that serves as an off-screen buffer for some graphics to be displayed possibly in
 *        tandem with other canvas elements or graphics.
 * @constructor
 */
function CanvasElement() {
	this.canvas = document.createElement('canvas');
	this.ctx = this.canvas.getContext('2d');
	this.invalid = true;
	this.resized = false;
	this.x = 0;
	this.y = 0;
	this.w = this.canvas.width;
	this.h = this.canvas.height;
	this.dependencies = [];
	this.invalidates = [];
}

/**
 * Sets the size of this canvas and invalidates it, if an actual change is detected.
 * 
 * @param {Number} width
 *        the new width
 * @param {Number} height
 *        the new height
 */
CanvasElement.prototype.setSize = function(width, height) {
	if (this.w !== width || this.h !== height) {
		this.w = width;
		this.h = height;
		if (width > 0 && height > 0) {
			this.canvas.width = width;
			this.canvas.height = height;
		}
		this.invalid = true;
		this.resized = true;
	}
};

/**
 * Checks if a coordinate pair is within the canvas area. The canvas' x and y properties are used as
 * it's offset.
 * 
 * @param {Number} x
 *        the x coordinate in question
 * @param {Number} y
 *        the y coordinate in question
 *
 * @returns {Boolean} true, if the coordinates are contained within the canvas area
 */
CanvasElement.prototype.contains = function(x, y) {
	return (x >= this.x && x < this.x + this.w && y >= this.y && y < this.y + this.h);
};

/**
 * Ensures that the contents of the canvas are up to date. A redraw is triggered if necessary.
 * 
 * @returns {Boolean} true, if the canvas had to be redrawn
 */
CanvasElement.prototype.validate = function() {
	var i;
	for (i = 0; i < this.dependencies.length; i++) {
		if (this.dependencies[i].validate()) this.invalid = true;
	}
	this.checkState();
	if (this.invalid) {
		this.draw(this.resized);
		this.invalid = false;
		this.resized = false;
		return true;
	}
	return false;
};

/**
 * Causes a comparison of the relevant values that make up the visible content of this canvas
 * between the visualizer and cached values. If the cached values are out of date the canvas is
 * marked as invalid.
 * 
 * @returns {Boolean} true, if the internal state has changed
 */
CanvasElement.prototype.checkState = function() {
// default implementation doesn't invalidate
};

/**
 * Makes another canvas a dependency of this one. This will cause this canvas to be invalidated if
 * the dependency becomes invalid and will cause this canvas to validate the dependency before
 * attempting to validate itself. Do not create cyclic dependencies!
 * 
 * @param {CanvasElement} element
 *        the dependency
 */
CanvasElement.prototype.dependsOn = function(element) {
	this.dependencies.push(element);
	element.invalidates.push(this);
};

/**
 * @class Base class for maps
 * @extends CanvasElement
 *
 * @constructor
 * @param {AppState} appState
 *        the application state for reference
 * @param {VisState} visState
 *        the visualizer state for reference
 */
function CanvasElementAbstractMap(appState, visState) {
	this.upper();
	this.appState = appState;
    this.visState = visState;
}
CanvasElementAbstractMap.extend(CanvasElement);

/**
 * Draws the terrain map.
 */
CanvasElementAbstractMap.prototype.draw = function(resized, drawGrid) {
    if (typeof(drawGrid) === 'undefined')
        drawGrid = true;
    
    var row, col;
	var rows = this.visState.replay.rows;
	var cols = this.visState.replay.cols;
	this.ctx.fillStyle = SAND_COLOR;
	this.ctx.fillRect(0, 0, this.w, this.h);
    
    if (drawGrid) {
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 0.5;
        this.ctx.beginPath();
        for (row = 0; row <= rows; row++) {   
            this.ctx.moveTo(0, this.scale * row);
            this.ctx.lineTo(this.scale * cols, this.scale * row);
        }
        for (col = 0; col <= cols; col++) {   
            this.ctx.moveTo(this.scale * col, 0);
            this.ctx.lineTo(this.scale * col, this.scale * rows);
        }
    }
    this.ctx.stroke();
};

/**
 * @class A canvas element for the mini map.
 * @extends CanvasElementAbstractMap
 *
 * @constructor
 * @param {AppState} appState
 *        the application state for reference
 * @param {VisState} visState
 *        the visualizer state for reference
 */
function CanvasElementMiniMap(appState, visState) {
	this.upper(appState, visState);
	this.scale = 1;
	this.turn = undefined;
	this.cells = [];
}
CanvasElementMiniMap.extend(CanvasElementAbstractMap);

/**
 * Causes a comparison of the relevant values that make up the visible content of this canvas
 * between the visualizer and cached values. If the cached values are out of date the canvas is
 * marked as invalid.
 * 
 * @returns {Boolean} true, if the internal state has changed
 */
CanvasElementMiniMap.prototype.checkState = function() {
	if ((this.visState.time | 0) !== this.turn) {
		this.invalid = true;
		this.turn = (this.visState.time | 0);
		this.cells = this.visState.replay.getTurn(this.turn);
	}
};

/**
 * Invokes {@link CanvasElementAbstractMap#draw} to draw the map and then renders cells as pixels on
 * top of it.
 */
CanvasElementMiniMap.prototype.draw = function() {
	var i, cell, color;
	CanvasElementAbstractMap.prototype.draw.call(this, false, false);
	for (i = this.cells.length - 1; i >= 0; i--) {
		if ((cell = this.cells[i].interpolate(this.turn))) {
			color = '#';
			color += INT_TO_HEX[cell['r']];
			color += INT_TO_HEX[cell['g']];
			color += INT_TO_HEX[cell['b']];
			this.ctx.fillStyle = color;
			this.ctx.fillRect(cell['x'], cell['y'], 1, 1);
		}
	}
};

/**
 * @class A canvas element for the main map.
 * @extends CanvasElementAbstractMap
 *
 * @constructor
 * @param {AppState} appState
 *        the application state for reference
 * @param {VisState} visState
 *        the visualizer state for reference
 */
function CanvasElementMap(appState, visState) {
	this.upper(appState, visState);
}
CanvasElementMap.extend(CanvasElementAbstractMap);

/**
 * Causes a comparison of the relevant values that make up the visible content of this canvas
 * between the visualizer and cached values. If the cached values are out of date the canvas is
 * marked as invalid.
 * 
 * @returns {Boolean} true, if the internal state has changed
 */
CanvasElementMap.prototype.checkState = function() {
	if (this.scale !== this.appState.scale) {
		this.invalid = true;
		this.scale = this.appState.scale;
	}
};

/**
 * @class The main map including cells and indicators
 * @extends CanvasElement
 *
 * @constructor
 * @param {AppState} appState
 *        the application state for reference
 * @param {VisState} visState
 *        the visualizer state for reference
 * @param {CanvasElementMap} map
 *        the background map
 */
function CanvasElementCellsMap(appState, visState, map) {
	this.upper();
    this.appState = appState;
    this.visState = visState;
	this.map = map;
	this.dependsOn(map);
	this.time = 0;
	this.cells = [];
	this.drawStates = {};
	this.scale = 1;
    this.label = 0;
    this.cellShape = 0;
	this.mouseOverVis = false;
}
CanvasElementCellsMap.extend(CanvasElement);

/**
 * Causes a comparison of the relevant values that make up the visible content of this canvas
 * between the visualizer and cached values. If the cached values are out of date the canvas is
 * marked as invalid.
 * 
 * @returns {Boolean} true, if the internal state has changed
 */
CanvasElementCellsMap.prototype.checkState = function() {
	var i, kf;
	var hash = undefined;
	if (this.time !== this.visState.time
        || this.scale !== this.appState.scale
        || this.label !== this.appState.config['label']
        || this.cellShape !== this.appState.config['cellShape'])
    {
		this.invalid = true;
		this.time = this.visState.time;
		this.scale = this.appState.scale;
		this.label = this.appState.config['label'];
        this.cellShape = this.appState.config['cellShape'];

		// per turn calculations
		if (this.turn !== (this.time | 0)) {
			this.turn = this.time | 0;
			this.cells = this.visState.replay.getTurn(this.turn);
		}

		// interpolate cells for this point in time
		this.drawStates = {};
		for (i = this.cells.length - 1; i >= 0; i--) {
			if ((kf = this.cells[i].interpolate(this.time))) {
				hash = '#';
				hash += INT_TO_HEX[kf['r']];
				hash += INT_TO_HEX[kf['g']];
				hash += INT_TO_HEX[kf['b']];
				kf.calcMapCoords(this.scale, this.w, this.h);
				if (!this.drawStates[hash]) this.drawStates[hash] = [];
				this.drawStates[hash].push(kf);
			}
		}
	}
};

/**
 * Draws cells onto the map image. This includes overlay letters / ids, attack lines, effect circles
 * and finally the fog of war.
 */
CanvasElementCellsMap.prototype.draw = function() {
    var halfScale, drawList, hash, n, kf, d, fontSize, label, caption, order;
    var changes, change, i, mapX, mapY;
    var w, dx, dy;
    var player;
    var turn = Math.floor(this.time);
    var replay = this.visState.replay;

    // draw map
    this.ctx.drawImage(this.map.canvas, 0, 0);

    halfScale = 0.5 * this.scale;

    // draw cells sorted by color
    for (hash in this.drawStates) {
        this.ctx.fillStyle = hash;
        drawList = this.drawStates[hash];
        for (n = drawList.length - 1; n >= 0; n--) {
            kf = drawList[n];
            if (kf['owner'] !== undefined) {
                var cellShape = this.appState.config['cellShape'];
                var shapes = this.appState.config['CELL_SHAPES'];
                switch (cellShape) {
                    case shapes['CIRCLE']:
                        this.ctx.beginPath();
                        this.ctx.arc(kf.mapX + halfScale, kf.mapY + halfScale, halfScale * kf['size'],
                            0, 2 * Math.PI, false);
                        this.ctx.fill();
                        break;
                    case shapes['RECTANGLE']:
                        w = this.scale;
                        dx = kf.mapX;
                        dy = kf.mapY;
                        if (kf['size'] !== 1) {
                            d = 0.5 * (1.0 - kf['size']) * this.scale;
                            dx += d;
                            dy += d;
                            w *= kf['size'];
                        }
                        this.ctx.fillRect(dx, dy, w, w);
                        break;
                }
            }
        }
    }

    // draw A, B, C, D ... on cells or alternatively the global kf id
    label = this.appState.config['label'];
    if (label) {
        fontSize = Math.ceil(Math.max(this.scale, 10) / label);
        this.ctx.save();
        this.ctx.translate(halfScale, halfScale);
        this.ctx.textBaseline = 'middle';
        this.ctx.textAlign = 'center';
        this.ctx.font = 'bold ' + fontSize + 'px Arial';
        this.ctx.fillStyle = '#000';
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 0.2 * fontSize;
        order = new Array(this.appState.order.length);
        for (n = 0; n < order.length; n++) {
            order[this.appState.order[n]] = n;
        }
        for (hash in this.drawStates) {
            drawList = this.drawStates[hash];
            for (n = drawList.length - 1; n >= 0; n--) {
                kf = drawList[n];
                if (label === 1) {
                    if (kf['owner'] === undefined) continue;
                    player = order[kf['owner']];
                    caption = PLAYER_SYMBOLS[player];
                } else {
                    caption = kf.cellId;
                }
                this.ctx.strokeText(caption, kf.mapX, kf.mapY);
                this.ctx.fillText(caption, kf.mapX, kf.mapY);
                if (kf.mapX < 0) {
                    this.ctx.strokeText(caption, kf.mapX + this.map.w, kf.mapY);
                    this.ctx.fillText(caption, kf.mapX + this.map.w, kf.mapY);
                    if (kf.mapY < 0) {
                        this.ctx.strokeText(caption, kf.mapX + this.map.w, kf.mapY + this.map.h);
                        this.ctx.fillText(caption, kf.mapX + this.map.w, kf.mapY + this.map.h);
                    }
                }
                if (kf.mapY < 0) {
                    this.ctx.strokeText(caption, kf.mapX, kf.mapY + this.map.h);
                    this.ctx.fillText(caption, kf.mapX, kf.mapY + this.map.h);
                }
            }
        }
        this.ctx.restore();
    }

    // draw indicator of player move
    if (this.time > 0 && turn < replay.duration) {
        this.ctx.lineWidth += 3;
        player = replay.getCurrentPlayer(turn);
        this.ctx.strokeStyle = replay.htmlPlayerColors[player];
        changes = replay.getTurnChanges(turn + 1);
        if (changes) {
            change = changes[0];
            mapX = Math.round(this.scale * change[1]);
            mapY = Math.round(this.scale * change[0]);
            this.ctx.strokeRect(mapX, mapY, this.scale, this.scale);
        }
        this.ctx.lineWidth -= 3;
    }
};

/**
 * @class The main map with cells, dragged with the mouse and extended by borders if required
 * @extends CanvasElement
 *
 * @constructor
 * @param {AppState} appState
 *        the application state for reference
 * @param {VisState} visState
 *        the visualizer state for reference
 * @param {CanvasElementCellsMap} cellsMap
 *        the prepared map with cells
 */
function CanvasElementShiftedMap(appState, visState, cellsMap) {
	this.upper();
    this.appState = appState;
    this.visState = visState;
	this.cellsMap = cellsMap;
	this.dependsOn(this.cellsMap);
	this.shiftX = 0;
	this.shiftY = 0;
	this.fade = undefined;
}
CanvasElementShiftedMap.extend(CanvasElement);

/**
 * Causes a comparison of the relevant values that make up the visible content of this canvas
 * between the visualizer and cached values. If the cached values are out of date the canvas is
 * marked as invalid.
 * 
 * @returns {Boolean} true, if the internal state has changed
 */
CanvasElementShiftedMap.prototype.checkState = function() {
	if (this.visState.shiftX !== this.shiftX || this.visState.shiftY !== this.shiftY
			|| this.visState.fade !== this.fade || this.visState.time !== this.time) {
		this.invalid = true;
		this.shiftX = this.visState.shiftX;
		this.shiftY = this.visState.shiftY;
		this.fade = this.visState.fade;
		this.time = this.visState.time;
	}
};

/**
 * Draws the visible portion of the map with cells. If the map is smaller than the view area it is
 * repeated in a darker shade on both sides.
 */
CanvasElementShiftedMap.prototype.draw = function() {
    var dx, dy, cutoff, winner;
	var replay = this.visState.replay;
    var mx = (this.w - this.cellsMap.w) >> 1;
	var my = (this.h - this.cellsMap.h) >> 1;
	// max allowed shift
    dx = -Math.min(0, this.w - this.cellsMap.w) >> 1;
    dy = -Math.min(0, this.h - this.cellsMap.h) >> 1;
    // correct shift if needed
    this.shiftX = Math.clamp(this.shiftX, -dx, dx);
    this.shiftY = Math.clamp(this.shiftY, -dy, dy);
    this.visState.shiftX = this.shiftX;
    this.visState.shiftY = this.shiftY;
    // draw map
	mx += this.shiftX;
	my += this.shiftY;
    this.ctx.fillStyle = '#fff';
    this.ctx.fillRect(0,0,this.w,this.h);
	this.ctx.drawImage(this.cellsMap.canvas, mx, my);
	// fade out
	if (this.fade) {
		this.ctx.fillStyle = this.fade;
		this.ctx.fillRect(mx, my, this.cellsMap.w, this.cellsMap.h);
	}
	// game cut-off reason
	cutoff = replay.meta['replaydata']['cutoff'];
	if (this.time > this.visState.replay.duration - 1 && cutoff) {
        if (cutoff === 'rankstabilized') {
            winner = replay.meta['rank'][0];
            cutoff = replay.meta['playernames'][winner] + '   won';
        } else if (cutoff === 'turnlimitreached') {
            cutoff = "Draw";
        } else {
            cutoff = '"' + cutoff + '"';
        }
		this.ctx.font = FONT;
		dx = 0.5 * (this.w - this.ctx.measureText(cutoff).width);
		dy = this.h - 5;
		this.ctx.lineWidth = 4;
		this.ctx.strokeStyle = '#000';
		this.ctx.strokeText(cutoff, dx, dy);
		this.ctx.fillStyle = '#fff';
		this.ctx.fillText(cutoff, dx, dy);
	}
};

/**
 * @class A canvas element for statistical time graphs.
 * @extends CanvasElement
 * @constructor
 * @param {AppState} appState
 *        the application state for reference
 * @param {VisState} visState
 *        the visualizer state for reference
 * @param {String} stats
 *        name of the stats to query from the visualizer
 */
function CanvasElementGraph(appState, visState, stats) {
	this.upper();
	this.appState = appState;
	this.visState = visState;
	this.stats = stats;
	this.duration = 0;
}
CanvasElementGraph.extend(CanvasElement);

/**
 * Tries to replace the given player's status at the end of the match with a Unicode glyph. This is
 * basically to reduce the noise caused by the longer textual descriptions.
 * 
 * @private
 * @param {Number} i
 *        the zero-based player index
 *
 * @returns {String} Returns a well supported Unicode glyph for some known status, or the original status
 *          text otherwise.
 */
CanvasElementGraph.prototype.statusToGlyph = function(i) {
	var status_i = this.visState.replay.meta['status'][i];
	if (status_i === 'survived') {
		return '\u2713';
	} else if (status_i === 'eliminated') {
		return '\u2717';
	}
	return status_i;
};

/**
 * Causes a comparison of the relevant values that make up the visible content of this canvas
 * between the visualizer and cached values. If the cached values are out of date the canvas is
 * marked as invalid.
 * 
 * @returns {Boolean} true, if the internal state has changed
 */
CanvasElementGraph.prototype.checkState = function() {
	if (this.duration !== this.visState.replay.duration && this.h > 0) {
		this.invalid = true;
		this.duration = this.visState.replay.duration;
	}
};

/**
 * Renders a timeline of the statistical values. The graphs are annotated by the player's state in
 * it's last turn.
 */
CanvasElementGraph.prototype.draw = function() {
	var min, max, i, k, t, scaleX, scaleY, txt, x, y, tw, tx;
	var w = this.w - 1;
	var h = this.h - 1;
	var replay = this.visState.replay;
	var values = this.getStats(this.stats).values;
	// Fixes the bug where the values would be scaled iteratively on every screen update in the live
	// visualizer
	var scaleFn = Math.sqrt;
	this.ctx.fillStyle = SAND_COLOR;
	this.ctx.fillRect(0, 0, this.w, this.h);
	this.ctx.font = '10px Arial,Sans';

	// find lowest and highest value
	min = 0;
	max = -Infinity;
	for (i = 0; i <= this.duration; i++) {
		for (k = 0; k < values[i].length; k++) {
			if (max < scaleFn(values[i][k])) {
				max = scaleFn(values[i][k]);
			}
		}
	}

	// draw ticks
	scaleX = (this.duration === 0) ? 0 : w / this.duration;
	this.ctx.strokeStyle = 'rgba(0,0,0,0.5)';
	this.ctx.beginPath();
	for (k = 1; k * scaleX < 2;) {
		k *= 10;
	}
	for (i = k - 1; i <= this.duration + 1; i += k) {
		t = ((i + 1) % (100 * k) ? (i + 1) % (10 * k) ? 3 : 7 : 11);
		this.ctx.moveTo(0.5 + scaleX * i, h - t);
		this.ctx.lineTo(0.5 + scaleX * i, h + 1);
	}
	this.ctx.moveTo(0.5 + 0, h + 0.5);
	this.ctx.lineTo(0.5 + scaleX * (this.duration + 1), h + 0.5);
	this.ctx.stroke();
    
    // draw game phaze divider
    x = scaleX * (this.visState.replay.gamePhaseDuration) - scaleX;
    this.ctx.lineWidth = 1;
    this.ctx.beginPath();
    this.ctx.moveTo(x, 0);
    this.ctx.lineTo(x, 32.5 + h);
    this.ctx.strokeStyle = '#DF0101'; // red
    this.ctx.stroke();
    
    scaleY = h / Math.max(max - min, 1);
	// time line
	this.ctx.textAlign = 'left';
	for (i = values[0].length - 1; i >= 0; i--) {
		this.ctx.strokeStyle = rgb_to_hex(DEFAULT_CELL_COLOR);
		this.ctx.beginPath();
		this.ctx.moveTo(0.5, 0.5 + scaleY * (max - scaleFn(values[0][i])));
		for (k = 1; k <= this.duration; k++) {
			this.ctx.lineTo(0.5 + scaleX * k, 0.5 + scaleY * (max - scaleFn(values[k][i])));
		}
		this.ctx.stroke();
	}
	if (!this.appState.isStreaming && replay.meta['status']) {
		for (i = replay.players - 1; i >= 0; i--) {
			k = replay.meta['playerturns'][i];
			this.ctx.beginPath();
			x = 0.5 + k * scaleX;
			y = 0.5 + scaleY * max;
			this.ctx.moveTo(x, y);
			txt = this.statusToGlyph(i);
			tw = this.ctx.measureText(txt).width;
			tx = Math.min(x, w - tw);
			this.ctx.fillStyle = replay.htmlPlayerColors[i];
			this.ctx.strokeStyle = replay.htmlPlayerColors[i];
			if (y < 30) {
				y = ((y + 12) | 0) + 0.5;
				this.ctx.lineTo(x, y - 8);
				this.ctx.moveTo(tx, y - 8);
				this.ctx.lineTo(tx + tw, y - 8);
				this.ctx.fillText(txt, tx, y);
			} else {
				y = ((y - 7) | 0) + 0.5;
				this.ctx.lineTo(x, y + 2);
				this.ctx.moveTo(tx, y + 2);
				this.ctx.lineTo(tx + tw, y + 2);
				this.ctx.fillText(txt, tx, y);
			}
			this.ctx.stroke();
		}
	}
};

/**
 * Helper function that returns a replay property with the given name, that should refer to a
 * statistics array. If the name is 'scores' the replay is also checked for the end game bonus.
 * 
 * @param {String} name
 *        The property name to be queried.
 *
 * @returns {Stats} the statistics set for the given item name.
 */
CanvasElementGraph.prototype.getStats = function(name) {
	var values = this.visState.replay[name];
	var bonus;
	if (name === 'counts') {
		bonus = this.visState.replay['scores'];
	} else {
		bonus = new Array(values.length);
		if (name === 'scores' && this.turn === this.visState.replay.duration) {
			bonus[values.length - 1] = this.visState.replay.meta['replaydata']['bonus'];
		}
	}
	return new Stats(values, bonus);
};

/**
 * @class A canvas element for statistics. It makes use of {@link CanvasElementGraph}.
 * @extends CanvasElement
 * @constructor
 * @param {AppState} appState
 *        the application state for reference
 * @param {VisState} visState
 *        the visualizer state for reference
 * @param {String} caption
 *        the caption that is show to the left of the bar graph
 * @param {String} stats
 *        name of the stats to query from the visualizer
 * @param {String} bonusText
 *        Title over bonus section in the graph.
 */
function CanvasElementStats(appState, visState, caption, stats, bonusText) {
	this.upper();
	this.appState = appState;
    this.visState = visState;
    this.caption = caption;
	this.turn = 0;
	this.time = 0;
	this.label = false;
	this.bonusText = bonusText;
	this.graph = new CanvasElementGraph(appState, visState, stats);
	this.dependsOn(this.graph);
}
CanvasElementStats.extend(CanvasElement);

/**
 * Size without timeline.
 */
CanvasElementStats.MIN_HEIGHT = 30;
/**
 * Size with timeline.
 */
CanvasElementStats.MAX_HEIGHT = CanvasElementStats.MIN_HEIGHT + 70;

/**
 * Sets the size of this CanvasElementStats and the contained {@link CanvasElementGraph} and
 * invalidates both, if an actual change is detected.
 * 
 * @param {Number} width
 *        the new width
 * @param {Number} height
 *        the new height
 * @see CanvasElement#setSize
 */
CanvasElementStats.prototype.setSize = function(width, height) {
	CanvasElement.prototype.setSize.call(this, width, height);
	this.graph.x = this.x;
	this.graph.y = this.y + 32;
	this.graph.setSize(width - 4, Math.max(0, height - 32));
	this.showGraph = this.graph.h > 0;
};

/**
 * Causes a comparison of the relevant values that make up the visible content of this canvas
 * between the visualizer and cached values. If the cached values are out of date the canvas is
 * marked as invalid.
 * 
 * @returns {Boolean} true, if the internal state has changed
 */
CanvasElementStats.prototype.checkState = function() {
	if ((this.showGraph && this.time !== this.visState.time) || this.time !== (this.visState.time | 0)
			|| this.label !== (this.appState.config['label'] === 1)) {
		this.invalid = true;
		this.time = this.visState.time;
		this.turn = this.time | 0;
		this.label = this.appState.config['label'] === 1;
	}
};

/**
 * Daws a bar graph for the current turn and - if enabled - the contained time line.
 * 
 * @param resized
 *        {Boolean} Indicates weather the canvas has been resized and even static elements of the
 *        display have to be redrawn.
 */
CanvasElementStats.prototype.draw = function(resized) {
	var stats, text, x;
	if (resized) {
		this.ctx.fillStyle = BACK_COLOR;
		// this.ctx.fillRect(0, 0, this.w, this.h);

		// outlines
		this.ctx.strokeStyle = STAT_COLOR;
		this.ctx.lineWidth = 2;
		Shape.roundedRect(this.ctx, 0, 0, this.w, this.h, 1, 5);
		if (this.showGraph) {
			this.ctx.moveTo(0, 29);
			this.ctx.lineTo(this.w, 29);
		}
		this.ctx.fill();
		this.ctx.stroke();

		// text
		this.ctx.font = FONT;
		this.ctx.textAlign = 'left';
		this.ctx.textBaseline = 'middle';
		this.ctx.fillStyle = TEXT_COLOR;
		this.ctx.fillText(this.caption, 4, 14);
	}

	// draw scores
	stats = this.getStats(this.graph.stats, this.turn);
	this.drawColorBar(95, 2, this.w - 97, 26, stats, this.bonusText);

	// graph
	if (this.showGraph) {
		this.ctx.fillStyle = TEXT_GRAPH_COLOR;
		this.ctx.drawImage(this.graph.canvas, 2, 30);
		// time indicator
		x = (this.graph.w - 1) * this.time / this.graph.duration;
		this.ctx.lineWidth = 1;
		this.ctx.beginPath();
		this.ctx.moveTo(x, 32.5);
		this.ctx.lineTo(x, 32.5 + this.graph.h - 1);
		this.ctx.stroke();
		text = this.caption + ' | ';
		if (this.turn === this.graph.duration && !this.appState.isStreaming) {
			text += 'end / ' + this.graph.duration;
		} else {
			text += 'turn ' + this.turn + '/' + this.graph.duration;
		}
		this.ctx.fillText(text, 4, 44);
	}
};

/**
 * Helper function that returns a replay property with the given name, that should refer to a
 * statistics array. If the name is 'scores' the replay is also checked for the end game bonus.
 * 
 * @param {String} name
 *        The property name to be queried.
 * @param {Number} turn
 *        The turn for which to fetch the stats
 * @returns {Stats} the statistics set for the given item name.
 */
CanvasElementStats.prototype.getStats = function(name, turn) {
	var values = this.visState.replay[name][turn];
	var bonus = undefined;
	if (name === 'scores' && this.turn === this.appState.replay.duration) {
		bonus = this.visState.replay.meta['replaydata']['bonus'];
	} else if (name === 'counts') {
		bonus = this.visState.replay['stores'][turn];
	}
	return new Stats(values, bonus);
};

/**
 * Renders a horizontal 'stacked' bar graph.
 * 
 * @private
 * @param {Number} x
 *        the left coordinate
 * @param {Number} y
 *        the top coordinate
 * @param {Number} w
 *        the width
 * @param {Number} h
 *        the height
 * @param {Stats} stats
 *        The values and boni to display. The bonus field can be undefined or contain
 *        undefined values.
 * @param {String} bonusText
 *        Title over bonus section.
 */
CanvasElementStats.prototype.drawColorBar = function(x, y, w, h, stats, bonusText) {
	var i, idx, wUsable, xNegSep, text;
	var showBoni = false;
	var boni = new Array(stats.values.length);
	var boniList = new Array(stats.values.length);
	var negatives = [];
	var positives = [];
	var sumBoni = 0;
	var sumNegative = 0;
	var sumPositive = 0;
	var sumValues, sum;
	var xOffset = x;
	var drawPart = function(ctx, pixels, div, list, values, appState, visState, arrow, label) {
		var k, kIdx, wBarRaw, wBar, textWidth;
		ctx.save();
		for (k = 0; k < list.length; k++) {
			kIdx = appState.order[list[k]];
			ctx.fillStyle = rgb_to_hex(DEFAULT_CELL_COLOR);
			ctx.strokeStyle = STAT_COLOR;
			ctx.lineWidth = 0.5;
			if (div) {
				wBarRaw = Math.abs(values[kIdx]) * pixels / div;
			} else {
				wBarRaw = pixels / values.length;
			}
			if (wBarRaw !== 0) {
				// always draw a full width pixel to avoid aliasing
				wBar = Math.ceil(xOffset + wBarRaw) - xOffset;
				wBar = Math.min(x + w - xOffset, wBar);
				if (arrow) {
					ctx.beginPath();
					if (values[kIdx] >= 0) {
						ctx.moveTo(xOffset, y);
						ctx.lineTo(xOffset + wBar, y + h / 2);
						ctx.lineTo(xOffset, y + h);
						ctx.closePath();
					} else {
						ctx.moveTo(xOffset + wBar, y);
						ctx.lineTo(xOffset, y + h / 2);
						ctx.lineTo(xOffset + wBar, y + h);
						ctx.closePath();
					}
					ctx.fill();
					ctx.stroke();
				} else {
					ctx.fillRect(xOffset, y, wBar, h);
				}
				ctx.textBaseline = 'middle';
				ctx.font = 'bold 16px Monospace';
				ctx.fillStyle = TEXT_COLOR; // '#fff';
				ctx.lineWidth = 0.5;
				text = values[kIdx];
				if (label) {
					text = PLAYER_SYMBOLS[k] + ' ' + text;
					if (ctx.measureText(text).width + 4 > wBar) {
						text = PLAYER_SYMBOLS[k];
					}
				}
				textWidth = ctx.measureText(text).width + 4;
				if (textWidth <= wBar) {
					if (values[kIdx] >= 0) {
						ctx.textAlign = 'left';
						ctx.fillText(text, xOffset + 2, y + h / 2);
					} else {
						ctx.textAlign = 'right';
						ctx.fillText(text, xOffset + wBarRaw - 2, y + h / 2);
					}
				}
				xOffset += wBarRaw;
			}
		}
		ctx.restore();
	};
	this.ctx.save();
	this.ctx.fillStyle = BACK_COLOR;
	this.ctx.beginPath();
	this.ctx.rect(x, y, w, h);
	this.ctx.fill();
	// will we show a separate bonus section?
	for (i = 0; i < stats.values.length; i++) {
		if (stats.bonus !== undefined && stats.bonus[i]) {
			boni[i] = stats.bonus[i];
			sumBoni += boni[i];
			showBoni = true;
		} else {
			boni[i] = 0;
		}
		boniList[i] = i;
	}
	wUsable = showBoni ? w : w;
	// sum up absolutes of all values to determine width
	for (i = 0; i < stats.values.length; i++) {
		idx = this.appState.order[i];
		if (stats.values[idx] >= 0) {
			positives.push(i);
			sumPositive += stats.values[idx];
		} else {
			negatives.push(i);
			sumNegative -= stats.values[idx];
		}
	}
	sumValues = sumNegative + sumPositive;
	sum = sumValues + sumBoni;
	// show negative scores
	if (negatives.length) {
		drawPart(this.ctx, wUsable, sum, negatives, stats.values, this.appState, this.visState, true, this.label);
	}
	xNegSep = (x + sumNegative * wUsable / sum) | 0;
	// show positive scores
	drawPart(this.ctx, wUsable, sum, positives, stats.values, this.appState, this.visState,false, this.label);
	this.ctx.lineWidth = 2;
	this.ctx.strokeStyle = STAT_COLOR;
	this.ctx.beginPath();
	if (showBoni) {
		xOffset = Math.ceil(xOffset) + 1;
		this.ctx.moveTo(xOffset, y);
		this.ctx.lineTo(xOffset, y + h);
	}
	if (negatives.length) {
		this.ctx.moveTo(xNegSep, y + 2);
		this.ctx.lineTo(xNegSep, y + h - 2);
	}
	this.ctx.stroke();
	this.ctx.fillStyle = TEXT_COLOR;
	this.ctx.strokeStyle = '#fff';
	this.ctx.font = 'bold 12px Monospace';
	this.ctx.textBaseline = 'top';
	// draw boni
	if (showBoni) {
		xOffset += 1;
		drawPart(this.ctx, wUsable, sum, boniList, boni, this.appState, this.visState, true, this.label);
		this.ctx.textAlign = 'right';
		this.ctx.strokeText(bonusText, x + w - 2, y);
		this.ctx.fillText(bonusText, x + w - 2, y);
	}
	this.ctx.restore();
};

/**
 * @class A helper class to transfer statistical values inside {@link CanvasElement} descendants.
 * @constructor
 * @param values
 *        {Array} Statistical values for every player and turn.
 * @param bonus
 *        {Array} The bonus that will be added to each player's values at the end of the replay. Can
 *        be undefined and is used for the 'scores' statistical item.
 * @property values {Array}
 * @property bonus {Array}
 */
function Stats(values, bonus) {
	this.values = values;
	this.bonus = bonus;
}
