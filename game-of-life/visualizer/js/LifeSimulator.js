/**
 * @class This class used for simulating Game of Life universe.
 *
 * @constructor
 * @param {Array} cells
 *        List of cells representing starting position of universe.
 *        During simulation this list is updated with new info (marking death times, adding new cells).
 * @param {Number} rows
 *        Map height.
 * @param {Number} cols
 *        Map width.
 * @param {Number} startTurn
 *        The turn number from when simulation starts.
 */
function LifeSimulator(cells, rows, cols, startTurn) {
    this.cells = cells;
    this.rows = rows;
    this.cols = cols;
    this.startTurn = startTurn;
}

LifeSimulator.SIM_LENGTH = 500;

/**
 * Launches Game of Life simulations.
 *
 * @protected
 */
LifeSimulator.prototype.simulate = function() {
    var map = new Array(this.rows);
    for (var row = 0; row < this.rows; ++row) {
        map[row] = new Array(this.cols);
    }

    var aliveCells = [];
    for (var i = 0; i < this.cells.length; ++i) {
        var cell = this.cells[i];
        map[cell[0]][cell[1]] = cell;
        aliveCells.push({row: cell[0], col: cell[1]});
    }

    this.simStep(map, aliveCells, LifeSimulator.SIM_LENGTH);
};

/**
 * Calculates next step of simulation
 *
 * @private
 * @param {Array} map
 *        Current state of universe.
 * @param {Array} aliveCells
 *        A list of living cells. Having it besides map allows to optimize simulation.
 * @param {Number} totalSteps
 *        Total amount of steps that should be simulated.
 * @param {Number} stepsDone
 *        Amount of steps that was already simulated.
 */
LifeSimulator.prototype.simStep = function(map, aliveCells, totalSteps, stepsDone) {
    stepsDone = stepsDone || 0;
    if (stepsDone >= totalSteps) return;

    var row, col, cell, owner;
    var neighsCnt = this.calcNeighsCnt(map, aliveCells);

    // calc next state
    aliveCells = [];
    for (row = 0; row < this.rows; ++row) {
        for (col = 0; col < this.cols; ++col) {
            var neighs = neighsCnt[row][col];
            var sumNeighs = neighs[0] + neighs[1];

            if (map[row][col]) { // cell was alive
                if (sumNeighs < 2 || sumNeighs > 3) { // cell dies
                    cell = map[row][col];
                    cell[4] = this.startTurn + stepsDone + 1; // remember dying turn
                    map[row][col] = null;
                } else { // cell stays alive
                    aliveCells.push({row: row, col: col});
                }
            } else if (sumNeighs === 3) { // cell was dead and new cell spawns
                owner = neighs[0] > neighs[1]? 0: 1; // owner of most neighs
                cell = [row, col, this.startTurn + stepsDone + 1, owner, this.startTurn + totalSteps + 1];
                map[row][col] = cell;
                aliveCells.push({row: row, col: col});
                this.cells.push(cell);
            }
        }
    }
    this.simStep(map, aliveCells, totalSteps, stepsDone+1);
};

/**
 * Calculates grid of neighbours counts around living cells.
 *
 * @private
 * @param {Array} map
 *        Current state of universe.
 * @param {Array} aliveCells
 *        A list of living cells. Having it besides map allows to optimize simulation.
 *
 * @returns Returns a grid representing neighbours counts around living cells.
 */
LifeSimulator.prototype.calcNeighsCnt = function(map, aliveCells) {
    var row, col, cell, owner, i;
    var cntNeighs = this.initNeighsCnt();

    // calc neighs count around alive cells
    for (i=0; i < aliveCells.length; ++i) {
        var coords = aliveCells[i];
        cell = map[coords.row][coords.col];

        for (var dx = -1; dx <= 1; ++dx) {
            row = coords.row + dx;
            for (var dy = -1; dy <= 1; ++dy) {
                col = coords.col + dy;

                var inBounds = row >= 0 && row < this.rows &&
                    col >= 0 && col < this.cols;
                var isOriginal = (row === coords.row && col === coords.col); // original cell is skipped

                if (!inBounds || isOriginal) continue;

                owner = cell[3];
                ++cntNeighs[row][col][owner];
            }
        }
    }
    return cntNeighs
};

/**
 * Initializes new neighbours-count grid.
 *
 * @private
 * @reruns Returns a neighbours-count grid filled with 0.
 */
LifeSimulator.prototype.initNeighsCnt = function() {
    var row, col;

    // init neighbours count array
    var cntNeighs = new Array(this.rows);
    for (row = 0; row < this.rows; ++row) {
        cntNeighs[row] = new Array(this.cols);
        for (col = 0; col < this.cols; ++col) {
            cntNeighs[row][col] = [0, 0]; // for 2 players
        }
    }
    return cntNeighs;
};