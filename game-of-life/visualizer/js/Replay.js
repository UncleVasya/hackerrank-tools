/**
 * @fileOverview Classes for loading replays and maps into the visualizer.
 * @author <a href="mailto:marco.leise@gmx.de">Marco Leise</a>
 */

/**
 * Loads a replay or map in text form. The streaming format is not supported directly, but can by
 * loaded by the Java wrapper. In the visualizer, ants are unique objects, that are mostly a list of
 * animation key-frames that are interpolated for any given time to produce a "tick-less" animation.<br>
 * <b>Called by the Java streaming visualizer.</b>
 * 
 * @class The replay class loads a replay or map in string form and prepares it for playback. All
 *        per turn data is lazily evaluated to avoid long load times. The Java wrapper has some
 *        extensions to load streaming replays. Make sure changes here don't break it.
 *
 * @constructor
 * @param {String} params.replay
 *        The replay or map text.
 * @param {Boolean} params.debug
 *        If true, then partially corrupt replays are loaded instead of throwing an error.
 * @param {String} params.highlightUser
 *        The user with this ID (usually a database index) in the replay will get the first
 *        color in the player colors array.
 * @see Options#user
 * @see #addMissingMetaData
 * @see Cell
 */
function Replay(params) {
	var i, highlightPlayer, n, p;
	/**
	 * @private
	 */
	this.debug = params.debug || false;
	if (!params.replay && !params.meta) {
		// This code path is taken by the Java wrapper for streaming replay and initializes only the
		// basics. Most of the rest is faster done in native Java, than through Rhino.
		this.meta = {};
		this.meta['challenge'] = 'lifegame';
		this.meta['replayformat'] = format;
		this.meta['replaydata'] = {
			'map' : {},
			'cells' : []
		};
		this.duration = -1;
		this.hasDuration = true;
		this.aniCells = [];
	} else {
        if (params.replay) {
            this.parseReplay(params.replay);
        } else { // we have starting cells for simulation
            this.meta = params.meta;

            this.players = this.meta['replaydata']['players'];
            this.rows = this.meta['replaydata']['map']['rows'];
            this.cols = this.meta['replaydata']['map']['cols'];
			this.duration = 0;
            this.gamePhaseDuration = 0;

			this.meta['status'] = Object.create(this.meta.status);
            for (p = 0; p < this.players; ++p) {
                this.meta['status'][p] = 'survived';
            }

            this.meta['playerturns'] = Object.create(this.meta['playerturns']);
            for (p = 0; p < this.players; ++p) {
                this.meta['playerturns'][p] = 0;
            }
        }

        var cells = this.meta['replaydata']['cells'];

        // initialize cells dying turn
        for (n = 0; n < cells.length; n++) {
            cells[n][4] = this.duration + LifeSimulator.SIM_LENGTH + 1;
        }

        // simulate universe
        var active_players = 0;
        for (p = 0; p < this.players; ++p) {
            if (this.meta['status'][p] === 'survived') {
                ++active_players;
            }
        }
        if (active_players > 1 || params.meta) {
			new LifeSimulator(cells, this.rows, this.cols, this.duration).simulate();
            this.duration += LifeSimulator.SIM_LENGTH;
        }

        // prepare score and count lists
        this['scores'] = new Array(this.duration + 1);
        this['counts'] = new Array(this.duration + 1);
        this['stores'] = new Array(this.duration + 1);
        for (n = 0; n <= this.duration + 1; n++) {
            this['scores'][n] = new Array(this.players);
            for (i = 0; i < this.players; i++)
                this['scores'][n][i] = 0;

            this['counts'][n] = new Array(this.players);
            for (i = 0; i < this.players; i++)
                this['counts'][n][i] = 0;

            this['stores'][n] = new Array(this.players);
            for (i = 0; i < this.players; i++)
                this['stores'][n][i] = 0;
        }

        // calculate cell counts per turn per player
        for (i = 0; i < cells.length; i++) {
            for (n = cells[i][2]; n < cells[i][4]; n++) {
                this['counts'][n][cells[i][3]]++;
            }
        }

        // correct data about bots elimination turn
        if (active_players > 1) {
            for (var turn = this.gamePhaseDuration + 1; turn <= this.duration; ++turn) {
                for (var player = 0; player < this.players; ++player) {
                    if (this['counts'][turn][player] > 0) {
                        ++this.meta['playerturns'][player];
                    }
                }
            }
            // set appropriate status for bots eliminated during simulation
            for (player = 0; player < this.players; ++player) {
                if (this.meta['status'][player] === 'survived'
                    && this.meta['playerturns'][player] < this.duration-1)
                {
                    this.meta['status'][player] = 'eliminated';
                }
            }
        }
         // prepare caches
        this.aniCells =  new Array(cells.length);
        this.turns = new Array(this.duration + 1);
        this.aliveCells = new Array(this.duration + 1);
        this.simReplays = new Array(this.gamePhaseDuration + 1);
        this.replayCacheMisses = 0;
        this.replayCacheSuccess = 0;
    }
    this.hasDuration = this.duration > 0 || this.meta['replaydata']['turns'] > 0;

    // add missing meta data
    highlightPlayer = undefined;
    if (this.meta['user_ids']) {
        highlightPlayer = this.meta['user_ids'].indexOf(params.highlightUser, 0);
        if (highlightPlayer === -1) highlightPlayer = undefined;
    }
    this.addMissingMetaData(highlightPlayer);
}

Replay.prototype.parseReplay = function(replay) {
    var format = 'json';
	replay = JSON.parse(replay);

	// check if we have meta data or just replay data
	if (replay['challenge'] === undefined) {
		this.meta = {};
		this.meta['challenge'] = 'lifegame';
		this.meta['replayformat'] = format;
		this.meta['replaydata'] = replay;
	} else {
		this.meta = replay;
		replay = this.meta['replaydata'];
	}
	// validate meta data
	if (this.meta['challenge'] !== 'lifegame') {
		throw new Error('This visualizer is for the Game of Life challenge,' + ' but a "'
				+ this.meta['challenge'] + '" replay was loaded.');
	} else if (this.meta['replayformat'] !== format) {
		throw new Error('Replays in the format "' + this.meta['replayformat']
				+ '" are not supported.');
	}
	if (!replay) {
		throw new Error('replay meta data is no object notation');
	}

	// start validation process
	this.duration = 0;
	var that = this;

	// set up helper functions
	var stack = [];
	var keyEq = function(obj, key, val) {
		if (obj[key] !== val && !that.debug) {
			throw new Error(stack.join('.') + '.' + key + ' should be ' + val
					+ ', but was found to be ' + obj[key] + '!');
		}
	};
	var keyRange = function(obj, key, min, max) {
		if (!(obj[key] >= min && (obj[key] <= max || max === undefined)) && !that.debug) {
			throw new Error(stack.join('.') + '.' + key + ' should be within [' + min
					+ ' .. ' + max + '], but was found to be ' + obj[key] + '!');
		}
	};
	var keyIsArr = function(obj, key, minlen, maxlen) {
		if (!(obj[key] instanceof Array)) {
			throw new Error(stack.join('.') + '.' + key
					+ ' should be an array, but was found to be of type ' + typeof obj[key]
					+ '!');
		}
		stack.push(key);
		keyRange(obj[key], 'length', minlen, maxlen);
		stack.pop();
	};
	var keyIsStr = function(obj, key, minlen, maxlen) {
		if (typeof obj[key] !== 'string') {
			throw new Error(stack.join('.') + '.' + key
					+ ' should be a string, but was found to be of type ' + typeof obj[key]
					+ '!');
		}
		stack.push(key);
		keyRange(obj[key], 'length', minlen, maxlen);
		stack.pop();
	};
	var keyOption = function(obj, key, func, params) {
		if (obj[key] !== undefined) {
			func.apply(undefined, [ obj, key ].concat(params));
		}
	};
	var keyDefault = function(obj, key, def, func, params) {
		if (obj[key] === undefined) {
			obj[key] = def;
		}
		func.apply(undefined, [ obj, key ].concat(params));
	};
	var enterObj = function(obj, key) {
		if (!(obj[key] instanceof Object)) {
			throw new Error(stack.join('.') + '.' + key
					+ ' should be an object, but was found to be of type '
					+ typeof obj[key] + '!');
		}
		stack.push(key);
		return obj[key];
	};
	var durationSetter = null;
	var setReplayDuration = function(duration, fixed) {
		if (durationSetter) {
			if (!fixed && that.duration < duration || fixed && that.duration !== duration
					&& !that.debug) {
				throw new Error('Replay duration was previously set to ' + that.duration
						+ ' by "' + durationSetter + '" and is now redefined to be '
						+ duration + ' by "' + obj + '"');
			}
		} else {
			that.duration = Math.max(that.duration, duration);
			if (fixed) durationSetter = obj;
		}
	};

	// options
	enterObj(this.meta, 'replaydata');
	keyRange(replay, 'revision', 1, 1);
	this.revision = replay['revision'];
	keyRange(replay, 'players', 1, 2);
	this.players = replay['players'];

	// map
	var map = enterObj(replay, 'map');
	keyIsArr(map, 'data', 1, undefined);
	stack.push('data');
	keyIsStr(map['data'], 0, 1, undefined);
	stack.pop();
	keyDefault(map, 'rows', map['data'].length, keyEq, [ map['data'].length ]);
	this.rows = map['rows'];
	keyDefault(map, 'cols', map['data'][0].length, keyEq, [ map['data'][0].length ]);
	this.cols = map['cols'];
	var mapdata = enterObj(map, 'data');
	var regex = /[^-wbz]/;
	for (var r = 0; r < mapdata.length; r++) {
		keyIsStr(mapdata, r, map['cols'], map['cols']);
		var maprow = String(mapdata[r]);
        var i;
		if ((i = maprow.search(regex)) !== -1 && !this.debug) {
			throw new Error('Invalid character "' + maprow.charAt(i)
					+ '" in map. Zero based row/col: ' + r + '/' + i);
		}
	}
	stack.pop(); // pop 'data'
	stack.pop(); // pop 'map'

	// cells
	// TODO: parse cells into dictionary so I can replace cell[1] with cell.col
	keyIsArr(replay, 'cells', 0, undefined);
	stack.push('cells');
	var cells = replay['cells'];
	for (var n = 0; n < cells.length; n++) {
		keyIsArr(cells, n, 4, 4);
		stack.push(n);
		var obj = cells[n];
		// row must be within map height
		keyRange(obj, 0, 0, map['rows'] - 1);
		// col must be within map width
		keyRange(obj, 1, 0, map['cols'] - 1);
		// start must be >= 0
		keyRange(obj, 2, 0, undefined);
		// owner index must match player count
		keyRange(obj, 3, 0, this.players - 1);
		stack.pop();

        //obj.row = obj[0];
        //obj.col = obj[1];
        //obj.spawn = obj[2];
        //obj.owner = obj[3];
	}
	stack.pop();

    this.duration = this.gamePhaseDuration = cells.length;
};

/**
 * Adds optional meta data to the replay as required. This includes default player names and colors.
 * 
 * @private
 * @param {Number} highlightPlayer
 *        The index of a player who's default color should be exchanged with the first
 *        player's color. This is useful to identify a selected player by its color (the first one
 *        in the PĹAYER_COLORS array).
 */
Replay.prototype.addMissingMetaData = function(highlightPlayer) {
	var i;
	if (!(this.meta['playernames'] instanceof Array)) {
		if (this.meta['players'] instanceof Array) {
			// move players to playernames in old replays
			this.meta['playernames'] = this.meta['players'];
			delete this.meta['players'];
		} else {
			this.meta['playernames'] = new Array(this.players);
		}
	}
	if (!(this.meta['playercolors'] instanceof Array)) {
		this.meta['playercolors'] = new Array(this.players);
	}
	if (!(this.meta['playerturns'] instanceof Array)) {
		this.meta['playerturns'] = new Array(this.players);
	}
	// setup player colors
	var rank;
    var rank_sorted;
	if (this.meta['challenge_rank']) {
        rank = this.meta['challenge_rank'].slice();
	}
    var COLOR_MAP;
	if (highlightPlayer !== undefined) {
		COLOR_MAP = COLOR_MAPS[this.players-1];
        rank.splice(highlightPlayer, 1);
	} else {
		COLOR_MAP = COLOR_MAPS[this.players];
	}
    if (rank) {
        rank_sorted = rank.slice().sort(function (a, b) { return a - b; });
    }
    var adjust = 0;
	for (i = 0; i < this.players; i++) {
		if (!this.meta['playernames'][i]) {
			this.meta['playernames'][i] = 'player ' + (i + 1);
		}
		if (this.meta['replaydata']['scores'] && !this.meta['playerturns'][i]) {
			this.meta['playerturns'][i] = this.meta['replaydata']['scores'][i].length - 1;
		}
		if (!(this.meta['playercolors'][i] instanceof Array)) {
            var color;
            if (highlightPlayer !== undefined && i === highlightPlayer) {
                color = PLAYER_COLORS[COLOR_MAPS[0]];
                adjust = 1;
            } else {
                if (rank) {
                    var rank_i = rank_sorted.indexOf(rank[i - adjust]);
                    color = PLAYER_COLORS[COLOR_MAP[rank_i]];
                    rank_sorted[rank_i] = null;
                    
                } else {
                    color = PLAYER_COLORS[COLOR_MAP[i]];
                }
            }
            this.meta['playercolors'][i] = color = hsl_to_rgb(color);
		}
	}
	this.htmlPlayerColors = new Array(this.players);
	for (i = 0; i < this.players; i++) {
		this.htmlPlayerColors[i] = '#';
		this.htmlPlayerColors[i] += INT_TO_HEX[this.meta['playercolors'][i][0]];
		this.htmlPlayerColors[i] += INT_TO_HEX[this.meta['playercolors'][i][1]];
		this.htmlPlayerColors[i] += INT_TO_HEX[this.meta['playercolors'][i][2]];
	}
};

/**
 * Computes a list of visible ants for a given turn. This list is then used to render the
 * visualization.
 * <ul>
 * <li>The turns are computed on reqest.</li>
 * <li>The result is cached.</li>
 * <li>Turns are calculated iteratively so there is no quick random access to turn 1000.</li>
 * </ul>
 * 
 * @param {Number} n
 *        The requested turn.
 * @returns {Cell[]} The array of visible ants.
 */
Replay.prototype.getTurn = function(n) {
	var i, turn, cells, cell, aniCell, dead;
	if (this.turns[n] === undefined) {
		if (n !== 0) this.getTurn(n - 1);
		turn = this.turns[n] = [];
		// generate cells & keyframes
		cells = this.meta['replaydata']['cells'];
		for (i = 0; i < cells.length; i++) {
			cell = cells[i];
            var spawnTurn = cell[2];
			if (spawnTurn === n + 1 || n === 0 && spawnTurn === 0) {
				// spawn this cell
				aniCell = this.spawnCell(i, cell[0], cell[1], cell[2], cell[3]);
			} else if (this.aniCells[i]) {
				// load existing state
				aniCell = this.aniCells[i];
			} else {
				// continue with next cell
				continue;
			}

            // TODO: GoL is an easy game and maybe I can avoid need to pre-calculate previous turns.
            //       1) Rearrange check below to first check if we need to show this cell
            //       2) Add   if (!aniCell) this.SpawnCell(). So we don't rely on cell presence from prev. turns
            //       3) Original call to this.spawnCell() replace with    aniCell = this.aniCells[i] || this.spawnCell()

			dead = cell[4];
			if (dead === n + 1) {
				// end of life
				this.killCell(aniCell, dead);
			}
			if (dead > n || dead < 0) {
				// assign cell to display list
				turn.push(aniCell);
			}
		}
	}
	return this.turns[n];
};

/**
 * Spawns a new ant.
 * 
 * @param {Number} id
 *        Global ant id, an auto-incrementing number for each new ant. See {@link Config#label}
 * @param {Number} row
 *        Map row to spawn the ant on.
 * @param {Number} col
 *        Map column to spawn the ant on.
 * @param {Number} spawn
 *        Turn to spawn the ant at.
 * @param {Number} owner
 *        the owning player index
 * @returns {Cell} The new animation ant object.
 */
Replay.prototype.spawnCell = function(id, row, col, spawn, owner) {
	var aniCell = this.aniCells[id] = new Cell(id, spawn - 0.8);
	var color = this.meta['playercolors'][owner];
	var f = aniCell.frameAt(spawn - 0.8);
	aniCell.owner = owner;
	f['x'] = col;
	f['y'] = row;
	f['owner'] = owner;
	f['r'] = color[0];
	f['g'] = color[1];
	f['b'] = color[2];
	if (spawn !== 0) {
		f = aniCell.frameAt(spawn);
	}
	f['size'] = 1.0;
	return aniCell;
};

/**
 * Animates an ant's death.<br>
 * <b>Called by the Java streaming visualizer.</b>
 * 
 * @private
 * @param {Cell} aniCell
 *        The ant to be worked on.
 * @param {Number} death
 *        The zero-based turn, that the ant died in.
 */
Replay.prototype.killCell = function(aniCell, death) {
	aniCell.fade('size', 0.0, death - 0.8, death);
	aniCell.death = death;
};

Replay.prototype.getAliveCells = function(turn) {
    if (!this.aliveCells[turn]) {
        this.aliveCells[turn] = [];
        this.meta['replaydata']['cells'].forEach(function(cell) {
			if (cell[2] <= turn && cell[4] > turn) {
                this.aliveCells[turn].push(cell);
            }
		}, this);
    }
    return this.aliveCells[turn];
};

Replay.prototype.getSimReplay = function(turn, callback) {
    if (this.simReplays[turn]) {
        ++this.replayCacheSuccess;
        if (callback) callback(this.simReplays[turn]);
    } else {
        ++this.replayCacheMisses;

        // copy alive cells data and set spawn turns to be 0
        var aliveCells = this.getAliveCells(turn).map(function (cell) {
            return [cell[0], cell[1], 0, cell[3]];
        });

        var meta = deep_copy(this.meta);
        meta['replaydata']['cells'] = aliveCells;

        if (!this.webWorker) {
            this.webWorker = new WebWorker(function () {
                onmessage = function (event) {
                    var msg = event.data;
                    msg.data = new Replay(msg.data);
                    postMessage(msg);
                };
            });
        }

        var self = this;
        var data = {meta: meta, debug: this.debug, highlightUser: this.highlightUser};
        this.webWorker.sendMessage(data, function (replay) {
            self.simReplays[turn] = replay;
            replay.__proto__ = Replay.prototype;
            if (callback) callback(replay);
        });
    }
};
    
/**
 * This method will try and recreate the bot input generated by the engine as seen by a particular
 * player in this replay.<br>
 * 
 * @param {Number} player
 *        The index of the participating player.
 * @param {Number} min
 *        The first turn.
 * @param {Number} max
 *        The last turn.
 *
 * @returns {String} The bot input text.
 */
Replay.prototype.generateBotInput = function(player, min, max) {
	var botInput = 'turn 0\n';
	return botInput;
};