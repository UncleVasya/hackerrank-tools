/**
 * @class The visualizer object that handles replay drawing and playback: map, graphs, playback controls.
 *
 * @constructor
 * @param {Object}
 *        app main application object
 */
Visu = function(app) {
    this.app = app;

    this.x = 0;
    this.y = 0;
    this.w = 0;
    this.h = 0;

    this.replay = undefined;

    /** @private */
    this.state = new VisState();
    /** @private */
    this.map = undefined;
    /** @private */
    this.antsMap = undefined;
    /** @private */
    this.shiftedMap = undefined;
    /** @private */
    this.miniMap = undefined;
    /** @private */
    this.counts = undefined;
    /** @private */
    this.turns = undefined;
    /** @private */
    this.resizing = false;
    /** @private */
    if (app.state.options['decorated']) {
        /** @private */
        this.btnMgr = new ButtonManager(null);

    }
    /** @private */
    this.director = new Director(this);
    /** @private */
    this.mouseX = -1;
    /** @private */
    this.mouseY = -1;
    /** @private */
    this.mouseDown = 0;
    /**
     * the main canvas
     *
     * @private
     */
    this.main = {};
    /**
     * a hint text overlay
     *
     * @private
     */
    this.hint = '';
};

/**
 * Resets the visualizer and associated objects to an initial state.
 *
 * @private
 */
Visu.prototype.cleanUp = function() {
	this.director.cleanUp();
    this.state.cleanUp();

    this.replay = undefined;

    this.map = undefined;
    this.antsMap = undefined;
    this.shiftedMap = undefined;
    this.miniMap = undefined;
    this.counts = undefined;
};

/**
 * This calculates the playback speed from the configuration values {@link Config#duration},
 * {@link Config#speedSlowest}, {@link Config#speedFastest} and {@link Config#speedFactor}. The
 * latter can be controlled by the speed buttons.
 *
 * @private
 */
Visu.prototype.calculateReplaySpeed = function() {
    var state = this.app.state;
	var speed = this.director.duration / state.config['duration'];
	speed = Math.max(speed, state.config['speedSlowest']);
	speed = Math.min(speed, state.config['speedFastest']);
	this.director.defaultSpeed = speed * Math.pow(1.5, state.config['speedFactor']);
	if (this.director.speed !== 0) {
		this.director.speed = this.director.defaultSpeed;
	}
};

/**
 * Creates all different objects needed (canvas layers, director object)
 * and prepares them for visualizing provided replay.
 *
 * @private
 * @param {Object}
 *        replay replay to visualize
 */
Visu.prototype.init = function(replay) {
    this.state.replay = replay;

    this.map = new CanvasElementMap(this.app.state, this.state);
    this.antsMap = new CanvasElementAntsMap(this.app.state, this.state, this.map);
    this.shiftedMap = new CanvasElementShiftedMap(this.app.state, this.state, this.antsMap);
    this.miniMap = new CanvasElementMiniMap(this.app.state, this.state);
    if (this.app.state.options['decorated']) {
        this.counts = new CanvasElementStats(this.app.state, this.state, '# of cells', 'counts', '500 steps');
    }

    // calculate speed from duration and config settings
    this.director.duration = this.state.replay.duration;
    this.calculateReplaySpeed();

    var options = this.app.state.options;
    if (options['interactive'] && options['decorated']) {
        this.btnMgr.ctx = this.app.main.ctx;
        this.addPlaybackPanel();

        var vis = this;
        this.director.onState = function () {
            // add visual effect to the Play button
            var btn = vis.btnMgr.groups['playback'].buttons[4];
            btn.offset = (this.playing() ? 7 : 4) * vis.app.imgMgr.get('playback').height;
            if (btn === vis.btnMgr.pinned) {
                vis.btnMgr.pinned = null;
            }
            btn.down = 0;
            btn.draw();
        };
    }
};

/**
 * Adds panel with buttons to control playback (play, stop, etc).
 *
 * @private
 */
Visu.prototype.addPlaybackPanel = function() {
    bg = this.btnMgr.addImageGroup('playback', this.app.imgMgr.get('playback'),
        ImageButtonGroup.HORIZONTAL, ButtonGroup.MODE_NORMAL, 2, 0);

    dlg = new Delegate(this, function() {
        this.director.gotoTick(0);
    });
    bg.addButton(3, dlg, 'jump to start of first turn');
    bg.addSpace(32);

    dlg = new Delegate(this, function() {
        var stop = Math.ceil(this.state.time) - 1;
        this.director.slowmoTo(stop);
    });
    bg.addButton(5, dlg, 'play one move/attack phase backwards');
    bg.addSpace(64);

    dlg = new Delegate(this.director, this.director.playStop);
    bg.addButton(4, dlg, 'play/stop the game');
    bg.addSpace(64);

    dlg = new Delegate(this, function() {
        var stop = Math.floor(this.state.time) + 1;
        this.director.slowmoTo(stop);
    });
    bg.addButton(6, dlg, 'play one move/attack phase');
    bg.addSpace(32);

    dlg = new Delegate(this, function() {
        this.director.gotoTick(this.director.duration);
    });
    bg.addButton(2, dlg, 'jump to end of the last turn');
};

/**
 * Redraws the map display and it's overlays. It is called by the {@link Director} and resembles the
 * core of the visualization.
*/
Visu.prototype.draw = function() {
    var w, h, mx, my, x, y;
    var loc = this.shiftedMap;
    var ctx = this.app.main.ctx;

    // map
    this.shiftedMap.validate();
    ctx.drawImage(this.shiftedMap.canvas, loc.x, loc.y);

    // mouse cursor (super complicated position calculation)
    if (this.state.mouseOverVis) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(loc.x, loc.y, loc.w, loc.h);
        ctx.clip();
        mx = this.app.mouseX - this.map.x - this.state.shiftX;
        my = this.app.mouseY - this.map.y - this.state.shiftY;
        mx = Math.floor(mx / this.app.state.scale) * this.app.state.scale + this.map.x + this.state.shiftX;
        my = Math.floor(my / this.app.state.scale) * this.app.state.scale + this.map.y + this.state.shiftY;
        ctx.strokeStyle = '#0';
        ctx.beginPath();
        ctx.rect(mx + 0.5, my + 0.5, this.app.state.scale - 1, this.app.state.scale - 1);
        ctx.stroke();
        ctx.restore();
    }

    // minimap
    if (this.app.state.config['zoom'] !== 1 && this.miniMap.h + 4 <= loc.h
        && this.miniMap.w + 4 <= loc.w) {
        this.miniMap.validate();
        ctx.save();
        // border
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.rect(this.miniMap.x - 1, this.miniMap.y - 1, this.miniMap.w + 2, this.miniMap.h + 2);
        ctx.stroke();
        // map
        ctx.drawImage(this.miniMap.canvas, this.miniMap.x, this.miniMap.y);
        // position indicator
        ctx.beginPath();
        ctx.rect(this.miniMap.x, this.miniMap.y, this.miniMap.w, this.miniMap.h);
        ctx.clip();
        w = loc.w / this.app.state.scale;
        h = loc.h / this.app.state.scale;
        x = this.state.replay.cols / 2 - this.state.shiftX / this.app.state.scale - w / 2;
        y = this.state.replay.rows / 2 - this.state.shiftY / this.app.state.scale - h / 2;
        x -= Math.floor(x / this.state.replay.cols) * this.state.replay.cols;
        y -= Math.floor(y / this.state.replay.rows) * this.state.replay.rows;
        ctx.beginPath();
        ctx.rect(this.miniMap.x + x, this.miniMap.y + y, w, h);
        ctx.rect(this.miniMap.x + x - this.state.replay.cols, this.miniMap.y + y, w, h);
        ctx.rect(this.miniMap.x + x, this.miniMap.y + y - this.state.replay.rows, w, h);
        ctx.rect(this.miniMap.x + x - this.state.replay.cols, this.miniMap.y + y
        - this.state.replay.rows, w, h);
        ctx.stroke();
        ctx.restore();
    }

    if (this.state.replay.hasDuration && this.app.state.options['decorated']) {
        if (this.counts.validate() || this.app.resizing) {
            ctx.drawImage(this.counts.canvas, this.counts.x, this.counts.y);
        }
    }

    if (this.app.hint) {
        var hint_part_x = Math.max(this.app.hint_x, this.x);
        var available_w = this.x + this.w - hint_part_x; // available space for hint in this visualizer
        var required_w = this.app.hint_w - (hint_part_x - this.app.hint_x); // space required to draw rest of the hint
        var hint_part_w = Math.min(required_w, available_w);

        this.app.drawHintPart(hint_part_x, hint_part_w);
    }

	if (this.app.state.isStreaming) {
		// we were able to draw a frame, the engine may send us the next turn
		var vis = this;
		window.setTimeout(function() {
			if (vis.app.state.isStreaming) vis.app.streamingStart();
		}, 0);
	} else if (this.director.fixedFpt !== undefined) {
		// store frame
		video.captureFrame(this.director.time, this.director.duration);
	}
};

/**
 * Called upon window size or visualiser size changes to layout the visualizer elements.
 */
Visu.prototype.resize = function() {
    var y = this.y;
    //this.resizing = true;

    // 1. timeline placement
    if (this.state.replay.hasDuration && this.app.state.options['decorated']) {
        // time line
        this.counts.x = this.x;
        this.counts.y = y;
        this.counts.setSize(this.w, CanvasElementStats.MAX_HEIGHT);
        y += this.counts.h;
    }

    // 2. visualizer placement
    if (this.app.state.options['interactive'] && this.app.state.options['decorated']) {
        if (this.state.replay.hasDuration) {
            this.shiftedMap.x = Math.max(this.x, LEFT_PANEL_W);
            this.shiftedMap.y = y;
            var width = this.w - (this.shiftedMap.x - this.x);
            width = Math.min(width, this.app.main.canvas.width - RIGHT_PANEL_W - this.shiftedMap.x);
            this.shiftedMap.setSize(width, this.h - this.counts.h - BOTTOM_PANEL_H);

            // playback buttons are center, unless they would exceed the right border of the map
            var bg = this.btnMgr.groups['playback'];
            var w = 8 * 64;
            bg.x = this.x + ((this.w - w) / 2) | 0;
            bg.x = Math.min(bg.x, this.shiftedMap.x + this.shiftedMap.w - w);
            bg.x = Math.max(bg.x, 0);
            bg.y = this.shiftedMap.y + this.shiftedMap.h;
            bg.w = this.shiftedMap.x + this.shiftedMap.w - bg.x;
        } else {
            this.shiftedMap.x = 0;
            this.shiftedMap.y = y;
            this.shiftedMap.setSize(this.w - - LEFT_PANEL_W - RIGHT_PANEL_W, this.h - y);
        }
    } else {
        this.shiftedMap.x = 0;
        this.shiftedMap.y = y;
        this.shiftedMap.setSize(this.w, this.h - y);
    }
    this.setZoom(this.app.state.config['zoom']);
    this.miniMap.x = this.shiftedMap.x + this.shiftedMap.w - 2 - this.state.replay.cols;
    this.miniMap.y = this.shiftedMap.y + 2;
    this.miniMap.setSize(this.state.replay.cols, this.state.replay.rows);
    // redraw everything
    this.director.draw(true);
    this.btnMgr.draw();
    //this.resizing = false;
};

/**
 * Sets a new map zoom. At zoom level 1, the map is displayed such that
 * <ul>
 * <li>it has at least a border of 10 pixels on each side</li>
 * <li>map squares are displayed at an integer size</li>
 * <li>map squares are at least 1 pixel in size</li>
 * </ul>
 * This value is then multiplied by the zoom given to this function and ultimately clamped to a
 * range of [1..20].
 *
 * @private
 * @param zoom
 *        {Number} The new zoom level in pixels. Map squares will be scaled to this value. It will
 *        be clamped to the range [1..20].
 */
Visu.prototype.setZoom = function(zoom) {
    var state = this.app.state;
	var oldScale = state.scale;
	if (this.director.fixedFpt === undefined) {
		state.scale = Math.max(1, Math.min((this.shiftedMap.w - 20) / this.state.replay.cols,
				(this.shiftedMap.h - 20) / this.state.replay.rows)) | 0;
		state.scale = Math.min(ZOOM_SCALE, state.scale * zoom);
	} else {
		state.scale = Math.max(1, Math.min(this.shiftedMap.w / this.state.replay.cols,
				this.shiftedMap.h / this.state.replay.rows)) | 0;
		state.scale = Math.pow(2, (Math.log(state.scale) / Math.LN2) | 0);
	}
	if (oldScale) {
		this.state.shiftX = (this.state.shiftX * state.scale / oldScale) | 0;
		this.state.shiftY = (this.state.shiftY * state.scale / oldScale) | 0;
	}
	this.app.calculateMapCenter(state.scale);
	this.map.setSize(state.scale * this.state.replay.cols, state.scale * this.state.replay.rows);
	this.map.x = (((this.shiftedMap.w - this.map.w) >> 1) + this.shiftedMap.x) | 0;
	this.map.y = (((this.shiftedMap.h - this.map.h) >> 1) + this.shiftedMap.y) | 0;
	this.antsMap.setSize(this.map.w, this.map.h);
};

/**
 * Centers the map drawn by this visualizer.
 *
 */
Visu.prototype.centerMap = function() {
    this.state.shiftX = this.app.mapCenterX;
	this.state.shiftY = this.app.mapCenterY;
    this.director.draw();
};

/**
 * Internal wrapper around mouse move events.
 *
 * @private
 * @param mx
 *        {Number} the X coordinate of the mouse relative to the upper-left corner of the
 *        visualizer.
 * @param my
 *        {Number} the Y coordinate of the mouse relative to the upper-left corner of the
 *        visualizer.
 */
Visu.prototype.mouseMoved = function(mx, my) {
	var tick;
	var deltaX = mx - this.mouseX;
	var deltaY = my - this.mouseY;
	var btn = null;
	this.mouseX = mx;
	this.mouseY = my;

    this.state.mouseCol = (mx - this.map.x - this.state.shiftX) / this.app.state.scale | 0;
	this.state.mouseRow = (my - this.map.y - this.state.shiftY) / this.app.state.scale | 0;

    this.app.hint = '';
	if (this.app.state.options['interactive']) {
        this.state.mouseOverVis = this.map.contains(mx, my);
		if (this.state.mouseOverVis && this.shiftedMap.contains(mx, my)) {
		    this.app.hint = 'row ' + this.state.mouseRow + ' | col ' + this.state.mouseCol;
		}
		if (this.mouseDown === 1 && this.counts.graph.contains(this.mouseX, this.mouseY)) {
			tick = this.mouseX - this.counts.graph.x;
			tick /= (this.counts.graph.w - 1);
			tick = Math.round(tick * this.state.replay.duration);
			this.director.gotoTick(tick);
		} else if (this.mouseDown === 2
				|| (this.mouseDown === 3 && this.miniMap.contains(this.mouseX, this.mouseY))) {
			if (this.mouseDown === 2) {
				this.state.shiftX += deltaX;
				this.state.shiftY += deltaY;
			} else {
				this.state.shiftX = (this.state.replay.cols / 2 - (this.mouseX - this.miniMap.x))
						* this.app.state.scale;
				this.state.shiftY = (this.state.replay.rows / 2 - (this.mouseY - this.miniMap.y))
						* this.app.state.scale;
			}
			if (this.app.state.options['decorated']) {
				var centerBtn = this.app.btnMgr.groups['toolbarRight'].getButton(4);
				centerBtn.enabled = this.state.shiftX !== 0 || this.state.shiftY !== 0;
				centerBtn.draw();
			}
			this.director.draw();
		} else if (this.app.state.options['decorated']) {
			btn = this.btnMgr.mouseMove(mx, my);
		}
	} else if (this.app.state.options['decorated']) {
		btn = this.btnMgr.mouseMove(mx, my);
	}

	if (btn && btn.hint) {
		this.app.hint = btn.hint;
	}
};

/**
 * Internal wrapper around mouse down events.
 *
 * @private
 */
Visu.prototype.mousePressed = function() {
	if (this.app.state.options['interactive']) {
		if (this.state.replay.hasDuration
				&& this.app.state.options['decorated']
				&& this.counts.graph.contains(this.mouseX, this.mouseY)) {
			this.mouseDown = 1;
		} else if (this.app.state.config['zoom'] !== 1
				&& this.miniMap.contains(this.mouseX, this.mouseY)) {
			this.mouseDown = 3;
		} else if (this.shiftedMap.contains(this.mouseX, this.mouseY)) {
			this.mouseDown = 2;
		} else {
			this.btnMgr.mouseDown();
			return;
		}
		this.mouseMoved(this.mouseX, this.mouseY); // TODO: find out why do we need this
	} else if (this.app.state.options['decorated']) {
		// handle game/player links if in non-interactive mode
		this.btnMgr.mouseDown();
	}
};

/**
 * Internal wrapper around mouse button release events.
 *
 * @private
 */
Visu.prototype.mouseReleased = function() {
	this.mouseDown = 0;
	if (this.app.state.options['decorated']) {
		this.btnMgr.mouseUp();
	}
};

/**
 * Checks if a coordinate pair is within the canvas area. The canvas' x and y properties are used as
 * it's offset.
 *
 * @param {Number}
 *        x the x coordinate in question
 * @param {Number}
 *        y the y coordinate in question
 * @returns {Boolean} true, if the coordinates are contained within the canvas area
 */
Visu.prototype.contains = function(x, y) {
	return (x >= this.x && x < this.x + this.w && y >= this.y && y < this.y + this.h);
};


/**
 * @class Holds public variables that need to be accessed from multiple modules of the visualizer.
 * @constructor
 * @property {Number} time The current visualizer time or position in turns, starting with 0 at the
 *           start of 'turn 1'.
 * @property {Number} shiftX X coordinate displacement of the map.
 * @property {Number} shiftY Y coordinate displacement of the map.
 * @property {Boolean} mouseOverVis True, if the mouse is currently in the active area of the map.
 *           This is used to quickly check if mouse-over effects need to be drawn.
 * @property {Number} mouseCol The current wrapped map column, the mouse is hovering over. This
 *           value is only valid when {@link State#mouseOverVis} is true.
 * @property {Number} mouseRow The current wrapped map row, the mouse is hovering over. This value
 *           is only valid when {@link State#mouseOverVis} is true.
 * @property fade Undefined, unless a fade out/in effect is to be drawn. Then this is set to a
 *           rgba() fill style.
 * @property {Replay} replay The currently loaded replay.
 */
function VisState() {
	this.cleanUp();
}

/**
 * Resets the state to initial values.
 */
VisState.prototype.cleanUp = function() {
	this.time = 0;
	this.shiftX = 0;
	this.shiftY = 0;
	this.mouseOverVis = false;
	this.mouseCol = undefined;
	this.mouseRow = undefined;
	this.fade = undefined;
};