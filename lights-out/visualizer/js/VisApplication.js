/**
 * @namespace Enum for the different states, the visualizer can be in.
 */
LoadingState = {
	/**
	 * The visualizer is not currently loading a replay or map.
	 *
	 * @const
	 */
	IDLE : 0,
	/**
	 * The visualizer is loading a replay or map and cannot take any load requests.
	 *
	 * @const
	 */
	LOADING : 1,
	/**
	 * The visualizer is currently cleaning up.
	 *
	 * @const
	 * @see VisApplication#cleanUp
	 */
	CLEANUP : 2
};

/**
 * @class The main 'application' object that provides all necessary methods for the use in a web
 *        page. Usually you just construct an instance and then call
 *        {@link VisApplication#loadReplayData} or {@link VisApplication#loadReplayDataFromURI}.
 *
 * @constructor
 * @param {Node} container
 *        the HTML element, that the visualizer will embed into
 * @param {Options} options
 *        Adds immutable options. These can be overridden via URL parameters. The visualizer
 *        will not copy this {@link Options} instance, but instead use it directly. Modifications to
 *        the object at a later point will result in undefined behavior.
 * @param {Number} w
 *        an optional maximum width or undefined
 * @param {Number} h
 *        an optional maximum height or undefined
 * @param {Object} configOverrides
 *        an optional configuration; each field overrides the respective value in
 *        the user's configuration or the default; see {@link Config} for possible options
 */
VisApplication = function(container, options, w, h, configOverrides) {
	var parameters, equalPos, value, i, text, imgDir;
	var key = undefined;
	var app = this;
	/** @private */
	this.loading = LoadingState.LOADING;
	/*
	 * First of all get our logging up and running, so we can print possible error messages.
	 */
	/** @private */
	this.container = container;
	while (container.hasChildNodes()) {
		container.removeChild(container.lastChild);
	}
	/** @private */
	this.log = document.createElement('div');
	this.container.appendChild(this.log);

	// proceed with initialization
	try {
		this.state = new AppState();
		/** @private */
		this.w = w;
		/** @private */
		this.h = h;
		/** @private */
		this.resizing = false;
		if (configOverrides) this.state.config.overrideFrom(configOverrides);
		/** @private */
		this.state.options = options;
		// read URL parameters and store them in the parameters object
		parameters = window.location.href;
		if ((i = parameters.indexOf('?')) !== -1) {
			parameters = parameters.substr(i + 1).split('#')[0].split('&');
			for (i = 0; i < parameters.length; i++) {
				equalPos = parameters[i].indexOf('=');
				key = parameters[i].substr(0, equalPos);
				value = parameters[i].substr(equalPos + 1);
				switch (key) {
				case 'debug':
					this.state.options['debug'] = Options.toBool(value);
					break;
				case 'interactive':
					this.state.options['interactive'] = Options.toBool(value);
					break;
				case 'profile':
					this.state.options['profile'] = Options.toBool(value);
					break;
				case 'decorated':
					this.state.options['decorated'] = Options.toBool(value);
					break;
				case 'col':
					this.state.options['col'] = parseInt(value);
					break;
				case 'row':
					this.state.options['row'] = parseInt(value);
					break;
				case 'turn':
					this.state.options['turn'] = parseInt(value);
					break;
				case 'data_dir':
					this.state.options['data_dir'] = value;
					break;
				case 'game':
					this.state.options['game'] = value;
					break;
				case 'user':
					this.state.options['user'] = value;
					break;
				case 'config':
					this.state.config.overrideFrom(JSON.parse(unescape(value)));
				}
			}
		}
		// set default zoom to max if we are going to zoom in on a square
		if (!isNaN(this.state.options['row']) && !isNaN(this.state.options['col'])) {
			this.state.config['zoom'] = 1 << Math.ceil(Math.log(ZOOM_SCALE) / Math.LN2);
		}
		imgDir = (this.state.options['data_dir'] || '') + 'img/';
		/** @private */
		this.imgMgr = new ImageManager(imgDir, new Delegate(this, this.completedImages));
		if (this.state.options['decorated']) {
			this.imgMgr.add('playback.png', 'playback');
            this.imgMgr.add('toolbarLeft.png', 'toolbarLeft');
            this.imgMgr.add('toolbarRight.png', 'toolbarRight');
			/** @private */
			this.btnMgr = new ButtonManager(null);
		}
		this.mainVis = new VisContainer(this);
        if (this.state.config['helperVisEnabled']) {
            this.helperVis = new VisContainer(this);
        }
		/** @private */
		this.mouseX = -1;
		/** @private */
		this.mouseY = -1;
		/** @private */
		this.mouseDown = 0;
		/** @private */
		this.progressList = [];

		// print out the configuration
		text = 'Loading visualizer...';
		text += Html.table(function() {
			var table = '';
			var key = undefined;
			for (key in app.options) {
				var value = app.options[key];
				table += Html.tr(function() {
					return Html.td(function() {
						return Html.bold(key);
					}) + Html.td(value) + Html.td(function() {
						var result = '<i>';
						if (key === 'data_dir') result += '(Image directory)';
						return result + '</i>';
					});
				});
			}
			return table;
		});
		this.log.innerHTML = text;

		/** @private */
		this.replayStr = undefined;
		/** @private */
		this.replayReq = undefined;
		/**
		 * the main canvas
		 *
		 * @private
		 */
		this.main = {};

		// start loading images in the background and wait
		this.loading = LoadingState.IDLE;
		this.imgMgr.startRequests();
	} catch (error) {
		this.exceptionOut(error, false);
		throw error;
	}
};


/**
 * Prints a message on the screen and then executes a function. Usually the screen is not updated
 * until the current thread of execution has finished. To work around that limitation, this method
 * adds the function to be called to the browser's timer queue. Additionally any thrown errors are
 * also printed.
 * 
 * @private
 * @param {String} log
 *        a message to be logged before executing the function
 * @param {Function} func
 *        a function to be called after displaying the message
 * @param {String} id
 *        An identification of the progress that will be used to filter duplicates in the queue.
 */
VisApplication.prototype.progress = function(log, func, id) {
	var i;
	if (this.loading !== LoadingState.LOADING) return;
	for (i = 0; i < this.progressList.length; i++) {
		if (id === this.progressList[i]) return;
	}
	this.progressList.push(id);
	var app = this;
	if (log) this.logOut(log);
	window.setTimeout(function() {
		var k;
		try {
			func();
			for (k = 0; k < app.progressList.length; k++) {
				if (id === app.progressList[k]) {
					app.progressList.splice(k, 1);
					break;
				}
			}
		} catch (error) {
			app.exceptionOut(error, true);
			var selectedPosX = 0;
			var selectedPosY = 0;
			var obj = app.log;
			if (obj.offsetParent) do {
				selectedPosX += obj.offsetLeft;
				selectedPosY += obj.offsetTop;
			} while ((obj = obj.offsetParent));
			window.scrollTo(selectedPosX, selectedPosY);
		}
	}, 50);
};

/**
 * Places a paragraph with a message in the visualizer DOM element.
 * 
 * @private
 * @param {String} text
 *        the message text
 */
VisApplication.prototype.logOut = function(text) {
	this.log.innerHTML += text.replace(/\n/g, '<br>') + '<br>';
};

/**
 * Stops loading, cleans up the instance and calls {@link VisApplication#logOut} with the text in red.
 * 
 * @private
 * @param {string} text
 *        the error message text
 * @param {Boolean} cleanUp
 *        whether the visualizer should try to reset itself; this is only useful if the
 *        error is not coming from the constructor.
 */
VisApplication.prototype.errorOut = function(text, cleanUp) {
	this.logOut('<font style="color:red">' + text + '</font>');
	if (cleanUp) this.cleanUp();
};

/**
 * Converts a JavaScript Error into a HTML formatted string representation and prints that on the
 * web page.
 * 
 * @private
 * @param {Error|String} error
 *        a thrown error or string
 * @param {Boolean} cleanUp
 *        whether the visualizer should try to reset itself; this is only useful if the
 *        error is not coming from the constructor.
 */
VisApplication.prototype.exceptionOut = function(error, cleanUp) {
	var msg;
	var key = undefined;
	if (typeof error == 'string') {
		this.exceptionOut({
			message : error
		}, cleanUp);
		return;
	}
	msg = '<h4><u>' + (error.name ? error.name : 'Error') + '</u></h4>';
	msg += Html.table(function() {
		var escaped;
		var table = '';
		for (key in error) {
			if (key !== 'name') {
				try {
					escaped = String(error[key]);
					escaped = escaped.replace('&', '&amp;');
					escaped = escaped.replace('<', '&lt;');
					escaped = escaped.replace('>', '&gt;');
					table += Html.tr(function() {
						return Html.td(function() {
							return Html.bold(key);
						}) + Html.td(escaped);
					});
				} catch (e) {
					// catch FireFox UnknownClass-wrapper errors silently
				}
			}
		}
		return table;
	});
	this.errorOut(msg, cleanUp);
};

/**
 * Resets the visualizer and associated objects to an initial state. This method is also called in
 * case of an error.
 * 
 * @private
 */
VisApplication.prototype.cleanUp = function() {
	this.loading = LoadingState.CLEANUP;
	if (this.replayReq) this.replayReq.abort();
	if (this.state.options['decorated']) {
        this.imgMgr.cleanUp();
    }
    this.mainVis.cleanUp();
    if (this.helperVis) {
        this.helperVis.cleanUp();
    }
	this.state.cleanUp();
	this.replayStr = undefined;
	this.replayReq = undefined;
	if (this.main.canvas) {
		if (this.container.firstChild === this.main.canvas) {
			this.container.removeChild(this.main.canvas);
		}
	}
	this.resizing = false;
	document.onkeydown = null;
	document.onkeyup = null;
	document.onkeypress = null;
	window.onresize = null;
	this.log.style.display = 'block';
};

/**
 * This is called before a replay or map is loaded to ensure the visualizer is in an idle state at
 * that time. It then sets the state to {@link LoadingState}.LOADING.
 * 
 * @private
 * @returns {Boolean} true, if the visualizer was idle.
 */
VisApplication.prototype.preload = function() {
	if (this.loading !== LoadingState.IDLE) return true;
	this.cleanUp();
	this.loading = LoadingState.LOADING;
	return false;
};

/**
 * Loads a replay or map file located on the same server using a XMLHttpRequest.
 * 
 * @param {string} file
 *        the relative file name
 */
VisApplication.prototype.loadReplayDataFromURI = function(file) {
	if (this.preload()) return;
	var app = this;
	this.progress('Fetching replay from: ' + Html.italic(String(file)) + '...', function() {
		var request = new XMLHttpRequest();
		app.replayReq = request;
		/** @ignore */
		request.onreadystatechange = function() {
			if (request.readyState === 4) {
				if (app.loading === LoadingState.LOADING) {
					if (request.status === 200) {
						app.replayStr = '' + request.responseText;
						app.replayReq = undefined;
						app.loadParseReplay();
					} else {
						app.errorOut('Status ' + request.status + ': ' + request.statusText, true);
					}
				}
			}
		};
		request.open("GET", file);
		if (app.state.options['debug']) {
			request.setRequestHeader('Cache-Control', 'no-cache');
		}
		request.send();
		app.loadCanvas();
	}, "FETCH");
};

/**
 * Loads a replay string directly.
 * 
 * @param {string} data
 *        the replay string
 */
VisApplication.prototype.loadReplayData = function(data) {
	if (this.preload()) return;
	this.replayStr = data;
	this.loadCanvas();
};

/**
 * This initializes the visualizer to accept data pushed to it from the Java wrapper. For
 * performance reasons native Java code in Stream.java will incrementally fill up the replay. Since
 * visualizer is really slow in some situations, it used to be unresponsive when streaming at a high
 * rate. To avoid that it now requests a single new turn from the wrapper for every rendered frame.<br>
 * <b>Called by the Java streaming visualizer.</b>
 * 
 * @returns {Replay} the replay object is exposed to the Java wrapper
 */
VisApplication.prototype.streamingInit = function() {
	this.preload();
	this.state.isStreaming = true;
	return this.state.replay = new Replay();
};

/**
 * This is called internally by {@link VisApplication#draw} to request the next turn after a rendered
 * frame (throttling the data stream) and as a one-time, asynchronous call from Stream.java, where
 * it is issued after the Java wrapper has set up a global 'stream' variable in the JavaScript
 * context that refers to the Java Stream instance. First the visualizer will request new data from
 * the wrapper and set state.isStreaming to false if the game ended. Then, if the visualizer has not
 * finished loading yet, it will fully initialize itself based on the replay data or start/resume
 * playback.<br>
 * <b>Called by the Java streaming visualizer.</b>
 */
VisApplication.prototype.streamingStart = function() {
	this.state.isStreaming = stream.visualizerReady();
	if (this.loading === LoadingState.LOADING) {
		if (this.state.replay.hasDuration) {
			// set CPU to 100%, we need it
			this.mainVis.director.cpu = 1;
			this.loadCanvas();
		}
	} else {
		// call resize() in forced mode to update the GUI (graphs)
		this.resize(true);
		// resume playback if we are at the end
		var resume = !this.mainVis.director.playing() && (this.mainVis.state.time === this.mainVis.director.duration);
		if (this.mainVis.director.stopAt === this.mainVis.director.duration) {
			this.mainVis.director.stopAt = this.state.replay.duration;
		}
		this.mainVis.director.duration = this.state.replay.duration;
        if (this.helperVis) {
            this.helperVis.director.duration = this.state.replay.duration;
        }
		if (resume) {
			this.mainVis.director.play();
		}
	}
};

/**
 * Makes the visualizer output video frames at a fixed rate
 * 
 * @param {Number}
 *        fpt the number of frames per turn
 */
VisApplication.prototype.javaVideoOutput = function(fpt) {
	this.mainVis.director.fixedFpt = fpt;
};

/**
 * In this method the replay string that has been passed directly or downloaded is parsed into a
 * {@link Replay}. Afterwards an attempt is made to start the visualization ({@link VisApplication#tryStart}).
 * 
 * @private
 */
VisApplication.prototype.loadParseReplay = function() {
	var app = this;
	this.progress('Parsing the replay...', function() {
		var debug = app.state.options['debug'];
		var user = app.state.options['user'];
		if (user === '') user = undefined;
		if (app.replayStr) {
			app.state.replay = new Replay({replay: app.replayStr, debug: debug, highlightUser: user});
			app.replayStr = undefined;
		} else if (app.loading !== LoadingState.CLEANUP) {
			throw new Error('Replay is undefined.');
		}
		app.tryStart();
	}, "PARSE");
};

/**
 * Creates the main canvas element and insert it into the web page. An attempt is made to start the
 * visualization ({@link VisApplication#tryStart}).
 * 
 * @private
 */
VisApplication.prototype.loadCanvas = function() {
	var app = this;
	this.progress('Creating canvas...', function() {
		if (!app.main.canvas) {
			app.main.canvas = document.createElement('canvas');
			app.main.canvas.style.display = 'none';
		}
		var c = app.main.canvas;
		app.main.ctx = c.getContext('2d');
		if (app.container.firstChild !== c) {
			app.container.insertBefore(c, app.log);
		}
		app.tryStart();
	}, "CANVAS");
};

/**
 * Called by the ImageManager when no more images are loading. Since image loading is a background
 * operation, an attempt is made to start the visualization ({@link VisApplication#tryStart}). If some
 * images didn't load, the visualizer is stopped with an error message.
 * 
 * @param error
 *        {String} Contains the error message for images that didn't load or is empty.
 */
VisApplication.prototype.completedImages = function(error) {
	if (error) {
		this.errorOut(error, true);
	} else {
		this.tryStart();
	}
};

/**
 * Checks if we have a drawing context (canvas/applet), the images and the replay. If all components
 * are loaded, some remaining items that depend on them are created and playback is started.
 * tryStart() is called after any long during action that runs in the background, like downloading
 * images and the replay to check if that was the last missing component.
 * 
 * @private
 */
VisApplication.prototype.tryStart = function() {
	var i, k, scores;
	var app = this;
	// we need to parse the replay, unless it has been parsed by the
	// XmlHttpRequest callback
	if (this.state.replay) {
		if (!this.main.ctx) return;
		if (this.imgMgr.pending !== 0) return;
		// add GUI
		if (this.state.options['decorated']) {
            if (this.imgMgr.error) return;
            if (this.imgMgr.pending) return;
            this.btnMgr.ctx = this.main.ctx;
            // calculate player order
            if (this.state.replay.meta['replaydata']['bonus']) {
                scores = new Array(this.state.replay.players);
                for (i = 0; i < this.state.replay.players; i++) {
                    scores[i] = this.state.replay['scores'][this.state.replay.duration][i];
                    scores[i] += this.state.replay.meta['replaydata']['bonus'][i];
                }
            } else {
                scores = this.state.replay['scores'][this.state.replay.duration];
            }
            this.state.ranks = new Array(scores.length);
            this.state.order = new Array(scores.length);
            for (i = 0; i < scores.length; i++) {
                this.state.ranks[i] = 1;
                for (k = 0; k < scores.length; k++) {
                    if (scores[i] < scores[k]) {
                        this.state.ranks[i]++;
                    }
                }
                k = this.state.ranks[i] - 1;
                while (this.state.order[k] !== undefined)
                    k++;
                this.state.order[k] = i;
            }
            // add player buttons
            if (this.state.replay.hasDuration) {
                this.addPlayerButtons();
            }
            // add static buttons
            if (this.state.options['interactive']) {
                this.addLeftPanel();
                this.addRightPanel();
            }
        }

        this.mainVis.init(this.state.replay);
        if (this.helperVis) {
            this.helperVis.init(app.state.replay);
        }

		if (this.state.options['interactive']) {
			// this will fire once in FireFox when a key is held down
			/**
			 * @ignore
			 * @param event
			 *        The input event.
			 * @returns {Boolean} True, if the browser should handle the event.
			 */
			document.onkeydown = function(event) {
				if (!(event.shiftKey || event.ctrlKey || event.altKey || event.metaKey || (document.activeElement || {}).tagName == "INPUT")) {
					if (VisApplication.focused.keyPressed(event.keyCode)) {
						if (event.preventDefault)
							event.preventDefault();
						else
							event.returnValue = false;
						return false;
					}
				}
				return true;
			};
		}
		// setup mouse handlers
		/**
		 * @ignore
		 * @param event
		 *        The input event.
		 */
		this.main.canvas.onmousemove = function(event) {
			var mx = 0;
			var my = 0;
			var obj = this;
			if (this.offsetParent) do {
				mx += obj.offsetLeft;
				my += obj.offsetTop;
			} while ((obj = obj.offsetParent));
			mx = event.clientX
					- mx
					+ ((window.scrollX == null) ? (document.body.parentNode.scrollLeft != null) ? document.body.parentNode.scrollLeft
							: document.body.scrollLeft
							: window.scrollX);
			my = event.clientY
					- my
					+ ((window.scrollY == null) ? (document.body.parentNode.scrollTop != null) ? document.body.parentNode.scrollTop
							: document.body.scrollTop
							: window.scrollY);
			app.mouseMoved(mx, my);
		};
		/** @ignore */
		this.main.canvas.onmouseout = function() {
			app.mouseExited();
		};
		/**
		 * @ignore
		 * @param event
		 *        The input event.
		 */
		this.main.canvas.onmousedown = function(event) {
			if (event.which === 1) {
				VisApplication.focused = app;
				app.mousePressed();
			}
		};
		/**
		 * @ignore
		 * @param event
		 *        The input event.
		 */
		this.main.canvas.onmouseup = function(event) {
			if (event.which === 1) {
				app.mouseReleased();
			}
		};
		/**
		 * @ignore
		 */
		this.main.canvas.ondblclick = function() {
			if (app.shiftedMap.contains(app.mouseX, app.mouseY)) app.centerMap();
		};
		/** @ignore */
		window.onresize = function() {
			app.resize();
		};
        this.setSpeedButtonsHints();
        this.setZoomButtonsState();
		VisApplication.focused = this;
		// move to a specific row and col
		this.calculateMapCenter(ZOOM_SCALE);
		this.mainVis.state.shiftX = this.mapCenterX; //TODO: find a better place for this
		this.mainVis.state.shiftY = this.mapCenterY;
        if (this.helperVis) {
            this.helperVis.state.shiftX = this.mapCenterX; //TODO: find a better place for this
            this.helperVis.state.shiftY = this.mapCenterY;
        }

		this.log.style.display = 'none';
		this.main.canvas.style.display = 'inline';
		this.loading = LoadingState.IDLE;
		this.setFullscreen(this.state.config['fullscreen']);
		if (this.state.replay.hasDuration) {
			if (!isNaN(this.state.options['turn'])) {
				this.mainVis.director.gotoTick(this.state.options['turn'] - 1);
                //this.helperVis.director.gotoTick(this.state.options['turn'] - 1);
			} else {
				this.mainVis.director.play();
			}
		}
	} else if (this.replayStr) {
		this.loadParseReplay();
	}
};

/**
 * Centers map drawn by visualizers and disables CenterMap button.
 *
 * @protected
 */
VisApplication.prototype.centerMap = function() {
	if (this.state.options['decorated']) {
		var btn = this.btnMgr.groups['toolbarRight'].getButton(4);
		btn.enabled = false;
		btn.draw();
	}
    this.mainVis.centerMap();
    if (this.helperVis) this.helperVis.centerMap();
};

/**
 * Changes the replay speed.
 * 
 * @private
 * @param {Number} modifier
 *        {@link Config#speedFactor} is changed by this amount.
 */
VisApplication.prototype.modifySpeed = function(modifier) {
	this.state.config['speedFactor'] += modifier;
	this.mainVis.calculateReplaySpeed();
    this.setSpeedButtonsHints();
};

/**
 * Updates hints on speed change buttons according to the current speed.
 *
 * @private
 */
VisApplication.prototype.setSpeedButtonsHints = function() {
    var hintText = function(base) {
		return 'set speed modifier to ' + ((base > 0) ? '+' + base : base);
	};
    var state = this.state;
    if (state.options['interactive'] && state.options['decorated']
			&& state.replay.hasDuration) {
		var speedUpBtn = this.btnMgr.groups['toolbarRight'].getButton(6);
		speedUpBtn.hint = hintText(state.config['speedFactor'] + 1);
		var slowDownBtn = this.btnMgr.groups['toolbarRight'].getButton(7);
		slowDownBtn.hint = hintText(state.config['speedFactor'] - 1);
	}
};

/**
 * Calculates the position that the map should be moved to if it is centered. The map is centered
 * once at the start and on a click of the center button. The center is usually (0;0), unless
 * {@link Options#row} and {@link Options#col} are set.
 * 
 * @private
 * @param scale
 *        {Number} Since the position is in pixels, it depends on the map scale.
 */
VisApplication.prototype.calculateMapCenter = function(scale) {
	var options = this.state.options;
	var cols = this.state.replay.cols;
	var rows = this.state.replay.rows;
	if (!isNaN(options.row) && !isNaN(options.col)) {
		this.mapCenterX = scale * (0.5 * cols - 0.5 - options.col % cols);
		this.mapCenterY = scale * (0.5 * rows - 0.5 - options.row % rows);
	} else {
		this.mapCenterX = 0;
		this.mapCenterY = 0;
	}
};

/**
 * Adds the game and player link buttons at the top of the display.
 * 
 * @private
 */
VisApplication.prototype.addPlayerButtons = function() {
    var bg, dlg;
	var i;
    var app = this;

    bg = this.btnMgr.addTextGroup('players', ButtonGroup.MODE_NORMAL, 2);
	dlg = undefined;
	var gameId = this.state.replay.meta['game_id'];
	if (gameId === undefined && this.state.options['game']) {
		gameId = this.state.options['game'];
	}
	if (gameId === undefined) {
		bg.addButton('Players:', '#000', undefined);
	} else {
		if (this.state.replay.meta['game_url']) {
			dlg = new Delegate(this, function() {
				window.location.href = this.state.replay.meta['game_url'].replace('~', gameId);
			});
		}
		bg.addButton('Game #' + gameId + ':', '#000', dlg);
	}
	var buttonAdder = function(idx) {
		var color = app.state.replay.htmlPlayerColors[idx];
		var dlg = undefined;
		if (app.state.replay.meta['user_url'] && app.state.replay.meta['user_ids']
				&& app.state.replay.meta['user_ids'][idx] !== undefined) {
			dlg = new Delegate(app, function() {
				window.location.href = this.state.replay.meta['user_url'].replace('~',
						this.state.replay.meta['user_ids'][idx]);
			});
		}
		bg.addButton('', color, dlg);
	};
	for (i = 0; i < this.state.replay.players; i++) {
		buttonAdder(this.state.order[i]);
	}
	this.updatePlayerButtonText();
};


/**
 * Adds left panel with buttons related to the current game.
 * 
 * @private
 */
VisApplication.prototype.addLeftPanel = function() {
    var bg, dlg;

    bg = this.btnMgr.addImageGroup('toolbarLeft', this.imgMgr.get('toolbarLeft'),
        ImageButtonGroup.VERTICAL, ButtonGroup.MODE_NORMAL, 2, 0);

    dlg = new Delegate(this, function() {
        var shape = this.state.config['cellShape'];
        this.state.config['cellShape'] = (shape + 1) % 2;
        this.mainVis.director.draw();
        if (this.helperVis) {
            this.helperVis.director.draw();
        }
    });
    bg.addButton(0, dlg, 'cell shape: 1. rectangles, 2. circles');
    
    dlg = new Delegate(this, function() {
        var animLevel = this.state.config['animLevel'];
        this.state.config['animLevel'] = (animLevel + 1) % 3;
    });
    bg.addButton(1, dlg, 'animation: 1. none, 2. limited, 3. full');

    dlg = new Delegate(this, function() {
        var enabled = this.state.config['helperVisEnabled'];
        if (enabled) { // disable helper vis
            this.helperVis.cleanUp();
            this.helperVis = null;

        } else { // enable helper vis
            this.helperVis = new VisContainer(this);
            this.helperVis.init(this.state.replay);
            // pre-calculate helper replays for the first and last turns
            this.state.replay.getSimReplay(0);
            this.state.replay.getSimReplay(this.state.replay.gamePhaseDuration);
        }
        this.resize(true);
        // synchronize helper vis and main vis
        this.mainVis.director.onTurnChange(this.mainVis.director.time);
        this.state.config['helperVisEnabled'] = !enabled;
    });
    bg.addButton(2, dlg, 'show/hide prognosis');
};

/**
 * Adds right panel with buttons common for all games.
 * 
 * @private
 */
VisApplication.prototype.addRightPanel = function() {
    var bg, dlg;

    bg = this.btnMgr.addImageGroup('toolbarRight', this.imgMgr.get('toolbarRight'),
    ImageButtonGroup.VERTICAL, ButtonGroup.MODE_NORMAL, 2, 0);

    if (this.state.config.hasLocalStorage()) {
        dlg = new Delegate(this, function() {
            this.state.config.save();
        });
        bg.addButton(0, dlg, 'save and reuse the current settings');
    }

    if (!this.state.options['embedded']) {
        dlg = new Delegate(this, function() {
            var fs = this.state.config['fullscreen'];
            this.setFullscreen(!fs);
        });
        bg.addButton(1, dlg, 'toggle fullscreen mode');
    }

    dlg = new Delegate(this, function() {
        this.setZoom(2 * this.state.config['zoom']);

    });
    bg.addButton(2, dlg, 'zoom in');

    dlg = new Delegate(this, function() {
        var oldScale = this.state.scale;
        do {
            this.setZoom(0.5 * this.state.config['zoom']);
        } while (this.state.scale === oldScale && this.state.config['zoom'] > 1);
    });
    bg.addButton(3, dlg, 'zoom out');

    dlg = new Delegate(this, this.centerMap);
    bg.addButton(4, dlg, 'center the map').enabled = false;

    dlg = new Delegate(this, function() {
        var lbl = this.state.config['label'];
        this.setCellsLabels((lbl + 1) % 3);
    });
    bg.addButton(5, dlg, 'toggles: 1. player letters on cells, 2. global ids on cells');

    if (this.state.replay.hasDuration) {
        dlg = new Delegate(this, this.modifySpeed, [ +1 ]);
        bg.addButton(6, dlg);

        dlg = new Delegate(this, this.modifySpeed, [ -1 ]);
        bg.addButton(7, dlg);

        dlg = new Delegate(this, this.generateBotInput);
        bg.addButton(8, dlg, 'regenerates bot input from this replay');
    }
};


/**
 * Calculates the visualizer display size depending on the constructor arguments and whether
 * fullscreen mode is supported and enabled.
 * 
 * @private
 * @returns {Size} the size the visualizer should have
 */
VisApplication.prototype.calculateCanvasSize = function() {
	var width, height;
	var embed = this.state.options['embedded'];
	embed = embed || !this.state.config['fullscreen'];
	width = (this.w && embed) ? this.w : window.innerWidth;
	height = (this.h && embed) ? this.h : window.innerHeight;
	return new Size(width, height);
};

/**
 * Enables or disables fullscreen mode. In fullscreen mode the &lt;body&gt; element is replaced with
 * a new one that contains only the visualizer. For the Java/Rhino version a special setFullscreen()
 * method on the window object is called.
 * 
 * @private
 * @param enable
 *        {Boolean} If true, the visualizer will switch to fullscreen mode if supported.
 */
VisApplication.prototype.setFullscreen = function(enable) {
	if (!this.state.options['embedded']) {
		if (window.setFullscreen) {
			this.state.config['fullscreen'] = window.setFullscreen(enable);
		} else {
			this.state.config['fullscreen'] = enable;
			if (enable || this.savedBody) {
				var html = document.getElementsByTagName('html')[0];
				if (enable) {
					this.container.removeChild(this.main.canvas);
					this.savedOverflow = html.style.overflow;
					html.style.overflow = 'hidden';
					var tempBody = document.createElement('body');
					tempBody.appendChild(this.main.canvas);
					this.savedBody = html.replaceChild(tempBody, document.body);
				} else if (this.savedBody) {
					document.body.removeChild(this.main.canvas);
					this.container.appendChild(this.main.canvas);
					html.replaceChild(this.savedBody, document.body);
					html.style.overflow = this.savedOverflow;
					delete this.savedBody;
				}
			}
		}
	}
	this.resize(true);
};



/**
 * Sets the cell label display mode to a new value.
 * 
 * @private
 * @param mode
 *        {Number} 0 = no display, 1 = letters, 2 = global cells ids
 */
VisApplication.prototype.setCellsLabels = function(mode) {
	var hasDuration = this.state.replay.hasDuration;
	var recap = hasDuration && (mode === 1) !== (this.state.config['label'] === 1);
	this.state.config['label'] = mode;
	if (recap) {
		this.updatePlayerButtonText();
		this.main.ctx.fillStyle = '#fff';
		this.main.ctx.fillRect(0, 0, this.main.canvas.width, this.main.canvas.height);
		this.resize(true);
	} else {
        this.mainVis.director.draw();
        if (this.helperVis) {
            this.helperVis.director.draw();
        }
    }
};

/**
 * Updates the captions of player link buttons.
 * 
 * @private
 */
VisApplication.prototype.updatePlayerButtonText = function() {
	var i, idx, caption;
	var btnGrp = this.btnMgr.getGroup('players');
	for (i = 0; i < this.state.replay.players; i++) {
		idx = this.state.order[i];
		caption = this.state.replay.meta['playernames'][idx];
		if (this.state.config['label'] === 1) {
			caption = PLAYER_SYMBOLS[i] + ' ' + caption;
		} else {
			caption = this.state.ranks[idx] + '. ' + caption;
		}
		btnGrp.buttons[i + 1].setText(caption);
	}
};

/**
 * Called upon window size changes to layout the application main elements.
 * 
 * @private
 * @param forced
 *        {Boolean} If true, the layouting and redrawing is performed even if no size change can be
 *        detected. This is useful on startup or if the canvas content has been invalidated.
 */
VisApplication.prototype.resize = function(forced) {
	var y;
	var olds = new Size(this.main.canvas.width, this.main.canvas.height);
	var newSize = this.calculateCanvasSize();
	var resizing = newSize.w != olds.w || newSize.h != olds.h;
	if (resizing || forced) {
		var canvas = this.main.canvas;
		var ctx = this.main.ctx;
        canvas.width = newSize.w;
        canvas.height = newSize.h;
        ctx.fillStyle = '#fff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
		this.resizing = true;
		if (this.state.replay.hasDuration && this.state.options['decorated']) {
			y = this.btnMgr.groups['players'].cascade(newSize.w) + 4;
		} else {
			y = 0;
		}
		if (this.state.options['interactive'] && this.state.options['decorated']) {
            var bg = this.btnMgr.groups['toolbarLeft'];
            bg.x = 0;
			bg.y = y + CanvasElementStats.MAX_HEIGHT + 8;
            bg.h = newSize.h - bg.y;

            bg = this.btnMgr.groups['toolbarRight'];
			bg.x = newSize.w - RIGHT_PANEL_W;
			bg.y = y + CanvasElementStats.MAX_HEIGHT + 8;
            bg.h = newSize.h - bg.y;
		}
		// redraw button panels
		if (this.state.options['decorated']) {
            this.btnMgr.draw();
        }

        this.mainVis.x = 0;
        this.mainVis.y = y;
        this.mainVis.w = this.helperVis? newSize.w / 2 - 10: newSize.w;
        this.mainVis.h = newSize.h - y;
        if (this.helperVis) {
            this.helperVis.x = newSize.w / 2 + 10;
            this.helperVis.y = y;
            this.helperVis.w = newSize.w / 2 - 10;
            this.helperVis.h = newSize.h - y;
        }

        this.updateHint();
        this.mainVis.resize();
        if (this.helperVis) {
            this.helperVis.resize();
        }

        this.resizing = false;
	}
};

/**
 * Changes zoom level of visualizers and updates zoom buttons.
 *
 * @private
 * @param zoom
 *        {Number} New zoom level. Values less than 1 are set to 1.
 */
VisApplication.prototype.setZoom = function(zoom) {
    zoom = Math.max(1, zoom);
    if (this.mainVis.director.fixedFpt === undefined) {
        this.state.config['zoom'] = zoom;
    }

    this.mainVis.setZoom(zoom);
    this.mainVis.director.draw();

    if (this.helperVis) {
        this.helperVis.setZoom(zoom);
        this.helperVis.director.draw();
    }

    this.setZoomButtonsState();
};

/**
 * Updates availability of zoom buttons:
 * - IncreaseZoom button disabled if zoom level is at max already;
 * - DecreaseZoom button disabled if zoom level is at min already;
 *
 * @private
 */
VisApplication.prototype.setZoomButtonsState = function() {
    if (this.state.options['interactive'] && this.state.options['decorated']) {
		var zoomInBtn = this.btnMgr.groups['toolbarRight'].getButton(2);
		zoomInBtn.enabled = !(this.state.scale === ZOOM_SCALE);
		zoomInBtn.draw();
		var zoomOutBtn = this.btnMgr.groups['toolbarRight'].getButton(3);
		zoomOutBtn.enabled = !(this.state.config['zoom'] === 1);
		zoomOutBtn.draw();
	}
};

/**
 * Updates hint message for buttons, map position, etc.
 * Handles case with 2 visualizers: draws hint part lying between visualizers.
 *
 * @private
 */
VisApplication.prototype.updateHint = function() {
	var ctx = this.main.ctx;
    var hint = this.hint;

    ctx.font = FONT;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';

    if (ctx.measureText(hint).width > ctx.canvas.width) {
        do {
            hint = hint.substr(0, hint.length - 1);
        } while (hint && ctx.measureText(hint + '...').width > ctx.canvas.width);
        if (hint) hint += '...';
    }
    this.hint_w = ctx.measureText(hint).width;
    this.hint_x = (ctx.canvas.width - this.hint_w) >> 1;

    if (this.helperVis) {
        // clean up space between visualizers
        var x = this.mainVis.x + this.mainVis.w;
        var w = this.helperVis.x - x;
        var hint_y = this.mainVis.shiftedMap.y;

        ctx.fillStyle = '#fff';
        ctx.fillRect(x, hint_y, w, HINT_HEIGHT);

        // draw hint part between visualizers
        var hint_part_x = Math.max(this.hint_x, x);
        var hint_part_w = Math.min(this.hint_w, w);

        this.drawHintPart(hint_part_x, hint_part_w);
    }
};

/**
 * Draws specific part of hint message.
 *
 * @private
 * @param x
 *        {Number} Starting position of hint part.
 * @param w
 *        {Number} Weight of hint part.
 */
VisApplication.prototype.drawHintPart = function(x, w) {
    var ctx = this.main.ctx;

    var hint_y = this.mainVis.shiftedMap.y;

    ctx.save();
    ctx.beginPath();
    ctx.rect(x, hint_y, w, hint_y + HINT_HEIGHT);
    ctx.clip();

    ctx.fillStyle = 'rgba(0,0,0,0.3)';
    ctx.fillRect(x, hint_y, w, HINT_HEIGHT);
    ctx.fillStyle = '#fff';
    ctx.fillText(this.hint, this.hint_x, hint_y + 10);
    ctx.restore();
};

/**
 * Internal wrapper around mouse move events.
 * 
 * @public
 * @param mx
 *        {Number} the X coordinate of the mouse relative to the upper-left corner of the
 *        visualizer.
 * @param my
 *        {Number} the Y coordinate of the mouse relative to the upper-left corner of the
 *        visualizer.
 */
VisApplication.prototype.mouseMoved = function(mx, my) {
	var oldHint = this.hint;
	var btn = null;
	this.mouseX = mx;
	this.mouseY = my;
	this.hint = '';
	if (this.state.options['interactive']) {
        if (this.mainVis.contains(this.mouseX, this.mouseY)) {
            this.mainVis.mouseMoved(mx, my);
        } else if (this.helperVis && this.helperVis.contains(this.mouseX, this.mouseY)) {
            this.helperVis.mouseMoved(mx, my);
        }
        if (this.state.options['decorated']) {
			btn = this.btnMgr.mouseMove(mx, my);
		}
	} else if (this.state.options['decorated']) {
		btn = this.btnMgr.mouseMove(mx, my);
	}
	if (btn && btn.hint) {
        this.hint = btn.hint;
	}
	if (oldHint !== this.hint) {
        this.updateHint();
        this.mainVis.director.draw();
        if (this.helperVis) {
            this.helperVis.director.draw();
        }
	}
};

/**
 * Internal wrapper around mouse down events.
 * 
 * @protected
 */
VisApplication.prototype.mousePressed = function() {
	if (this.state.options['interactive']) {
		if (this.mainVis.contains(this.mouseX, this.mouseY)) {
            this.mainVis.mousePressed();
        } else if (this.helperVis && this.helperVis.contains(this.mouseX, this.mouseY)) {
            this.helperVis.mousePressed();
        }
		this.btnMgr.mouseDown();
		this.mouseMoved(this.mouseX, this.mouseY); // TODO: find out why do we need this
	} else if (this.state.options['decorated']) {
		// handle game/player links if in non-interactive mode
		this.btnMgr.mouseDown();
	}
};

/**
 * Internal wrapper around mouse button release events.
 * 
 * @protected
 */
VisApplication.prototype.mouseReleased = function() {
	this.mouseDown = 0;
	if (this.state.options['decorated']) {
		this.btnMgr.mouseUp();
	}
    this.mainVis.mouseReleased();
    if (this.helperVis) {
        this.helperVis.mouseReleased();
    }
	this.mouseMoved(this.mouseX, this.mouseY);
};

/**
 * Internal wrapper around mouse exit window events.
 * 
 * @protected
 */
VisApplication.prototype.mouseExited = function() {
	if (this.state.options['decorated']) {
		this.btnMgr.mouseMove(-1, -1);
		this.btnMgr.mouseUp();
	}
	this.mouseDown = 0;
};

/**
 * Internal wrapper around key press events.
 * 
 * @private
 * @param key
 *        A key code for the pressed button.
 * @returns {Boolean} false, if the browser should handle this key and true, if the visualizer
 *          handled the key
 */
VisApplication.prototype.keyPressed = function(key) {
	var d = this.director;
	var tryOthers = true;
	if (!this.state.options['embedded']) {
		tryOthers = false;
		switch (key) {
		case Key.PGUP:
			d.gotoTick(Math.ceil(this.state.time) - 10);
			break;
		case Key.PGDOWN:
			d.gotoTick(Math.floor(this.state.time) + 10);
			break;
		case Key.HOME:
			d.gotoTick(0);
			break;
		case Key.END:
			d.gotoTick(d.duration);
			break;
		default:
			tryOthers = true;
		}
	}
	if (tryOthers) {
		switch (key) {
		case Key.SPACE:
			d.playStop();
			break;
		case Key.LEFT:
			d.gotoTick(Math.ceil(this.state.time) - 1);
			break;
		case Key.RIGHT:
			d.gotoTick(Math.floor(this.state.time) + 1);
			break;
		case Key.PLUS:
		case Key.PLUS_OPERA:
		case Key.PLUS_JAVA:
			this.modifySpeed(+1);
			break;
		case Key.MINUS:
		case Key.MINUS_JAVA:
			this.modifySpeed(-1);
			break;
		default:
			switch (String.fromCharCode(key)) {
			case 'F':
				this.setFullscreen(!this.state.config['fullscreen']);
				break;
			case 'C':
				this.centerMap();
				break;
			case 'I':
				this.generateBotInput();
				break;
			default:
				return false;
			}
		}
	}
	return true;
};

/**
 * This method will ask the user for some input to convert the replay into a bot input string for
 * debugging.
 */
VisApplication.prototype.generateBotInput = function() {
    alert('Not implemented for this game. Ping me if you need it.');
};

/**
 * @class This class defines startup options that are enabling debugging features or set immutable
 *        configuration items for the visualizer instance. The available options are listed in the
 *        field summary and can be set by appending them as a parameter to the URL. For example
 *        '...?game=1&turn=20' will display game 1 and jump to turn 20 immediately. For boolean
 *        values 'true' or '1' are interpreted as true, everything else as false. Be aware that it
 *        is also possible to add a parameter named 'config' to the URL that will be handled
 *        specially by {@link VisApplication} to override {@link Config} settings. Also note that any
 *        additional options should have an initial value that makes it clear wether the setting is
 *        a number, a boolean or a string, because options are passed as strings to the Java applet
 *        and it will parse these strings to the data type it finds in the Options object.
 * @constructor
 * @property {String} data_dir The directory that contains the 'img' directory as a relative or
 *           absolute path. You will get an error message if you forget the tailing '/'.
 * @property {Boolean} interactive Set this to false to disable mouse and keyboard input and hide
 *           the buttons from view.
 * @property {Boolean} decorated Set this to false to hide buttons and statistics. This results in a
 *           'naked' visualizer suitable for small embedded sample maps.
 * @property {Boolean} debug Set this to true, to enable loading of some kinds of partially corrupt
 *           replays and display an FPS counter in the title bar.
 * @property {Boolean} profile Set this to true, to enable rendering code profiling though
 *           'console.profile()' in execution environments that support it.
 * @property {Boolean} embedded Set this to true, to disable the fullscreen option.
 * @property {String} game This is the game number that is used by the game link button for display
 *           and as to create the link URL.
 * @property {Number} col If row and col are both set, the visualizer will draw a marker around this
 *           location on the map and zoom in on it. The value is automatically wrapped around to
 *           match the map dimensions.
 * @property {Number} row See {@link Options#col}.
 * @property {Number} turn If this is set, the visualizer will jump to this turn when playback
 *           starts and stop there. This is often used with {@link Options#col} and
 *           {@link Options#row} to jump to a specific event.
 * @property {String} user If set, the replay will give this user id the first color in the list so
 *           it can easily be identified on the map.
 * @property {Boolean} loop If set, the replay will fade out and start again at the end.
 */
Options = function() {
	this['data_dir'] = '';
	this['interactive'] = true;
	this['decorated'] = true;
	this['debug'] = false;
	this['profile'] = false;
	this['embedded'] = false;
	this['game'] = '';
	this['col'] = NaN;
	this['row'] = NaN;
	this['turn'] = NaN;
	this['user'] = '';
	this['loop'] = true;
};

/**
 * Converts a string parameter in the URL to a boolean value.
 * 
 * @param value
 *        {String} the parameter
 * @returns {Boolean} true, if the parameter is either '1' or 'true'
 */
Options.toBool = function(value) {
	return value == '1' || value == 'true';
};

/**
 * @class Holds public variables that need to be accessed from multiple modules of the visualizer.
 *
 * @constructor
 * @property {Number} scale The size of map squares in pixels.
 * @property {Array} ranks Stores the rank of each player.
 * @property {Array} order Stores the ranking order of each player.
 * @property {Replay} replay The currently loaded replay.
 * @property {Number} time The current visualizer time or position in turns, starting with 0 at the
 *           start of 'turn 1'.
 * @property {Number} shiftX X coordinate displacement of the map.
 * @property {Number} shiftY Y coordinate displacement of the map.
 * @property {Boolean} mouseOverVis True, if the mouse is currently in the active area of the map.
 *           This is used to quickly check if mouse-over effects need to be drawn.
 * @property {Number} mouseCol The current wrapped map column, the mouse is hovering over. This
 *           value is only valid when {@link AppState#mouseOverVis} is true.
 * @property {Number} mouseRow The current wrapped map row, the mouse is hovering over. This value
 *           is only valid when {@link AppState#mouseOverVis} is true.
 * @property {Boolean} isStreaming This should be true as long as the visualizer is receiving data
 *           from a game in progress and be set to false when the last turn has been sent as
 *           indicated by the result of Stream.visualizerReady() in Stream.java.
 * @property fade Undefined, unless a fade out/in effect is to be drawn. Then this is set to a
 *           rgba() fill style.
 */
function AppState() {
	this.cleanUp();
	this.options = null;
	this.config = new Config();
}

/**
 * Resets the state to initial values.
 *
 * @public
 */
AppState.prototype.cleanUp = function() {
	this.scale = NaN;
	this.ranks = null;
	this.order = null;
	this.replay = null;
	this.isStreaming = false;
};
