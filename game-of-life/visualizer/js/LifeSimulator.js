function LifeSimulator(cells, rows, cols, players, start_turn) {
    this.SIMULATION_LENGTH = 500;

    this.cells = cells;
    this.rows = rows;
    this.cols = cols;
    this.players = players;
    this.start_turn = start_turn;
}

LifeSimulator.prototype.simulate = function() {
    var map = new Array(this.rows);
    for (var row = 0; row < this.rows; ++row) {
        map[row] = new Array(this.cols);
    }

    for (var i = 0; i < this.cells.length; ++i) {
        var cell = this.cells[i]
        map[cell[0]][cell[1]] = cell;
    }

    this.simStep(map, this.SIMULATION_LENGTH);
};

LifeSimulator.prototype.simStep = function(map, total_steps, steps_done) {
    steps_done = steps_done || 0;

    if (steps_done >= total_steps)
        return;

    var to_kill = [], to_spawn = [];
    var cntNeighs, sumNeighs;
    var cell, owner, data;
    for (var row = 0; row < this.rows; ++row) {
        for (var col = 0; col < this.cols; ++col) {
            cntNeighs = this.cntNeighs(map, row, col); // alive neighs per player
            sumNeighs = cntNeighs[0] + cntNeighs[1];
            cell = map[row][col];

            // alive cells to kill
            if (cell && (sumNeighs < 2 || sumNeighs > 3)) {
                to_kill.push({row: row, col: col});
            }
            // new cells to born
            else if (!cell && sumNeighs === 3) {
                owner = cntNeighs.indexOf(Math.max.apply(Math, cntNeighs)); // owner of most neighs
                to_spawn.push({row: row, col: col, owner: owner})
            }
        }
    }
    // apply changes
    for (var i = 0; i < to_kill.length; ++i) {
        data = to_kill[i];
        cell = map[data.row][data.col];
        cell[4] = this.start_turn + steps_done + 1; // remember dying turn
        map[data.row][data.col] = null;
    }
    for (i = 0; i < to_spawn.length; ++i) {
        data = to_spawn[i];
        cell = [data.row, data.col, this.start_turn + steps_done + 1, data.owner, this.start_turn + total_steps + 1];
        this.cells.push(cell);
        map[data.row][data.col] = cell;
    }
    this.simStep(map, total_steps, steps_done+1);
};

LifeSimulator.prototype.cntNeighs = function(map, aRow, aCol) {
    var cntNeighs = new Array(this.players);
    for (var i = 0; i < this.players; i++)
        cntNeighs[i] = 0;

    var dx, dy;
    var row, col, owner, inBounds, isOriginal, cell;
    for (dx = -1; dx <= 1; ++dx) {
        row = aRow + dx;
        for (dy = -1; dy <= 1; ++dy) {
            col = aCol + dy;
            
            inBounds = row >= 0 && row < this.rows &&
                       col >= 0 && col < this.cols;
            isOriginal = (row == aRow && col == aCol); // original cell is skipped

            if (!inBounds || isOriginal)
                continue;

            cell = map[row][col];
            if (cell) {
                owner = map[row][col][3];
                ++cntNeighs[owner];
            }
        }
    }
    return cntNeighs;
};