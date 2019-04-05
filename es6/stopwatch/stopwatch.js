const TEST = 'hello';

console.log(TEST);


export class StopWatch {

    constructor() {
        this.start = this.start.bind(this);
        this.pause = this.pause.bind(this);
        this.reset = this.reset.bind(this);
        this.reset();
    }

    get time_milliseconds() {
        if (this.pause_milliseconds) {return this.pause_milliseconds;}
        return this.timestamp_start ? Date.now() - this.timestamp_start : 0;
    }
    get date() {
        return new Date(this.time_milliseconds);
    }
    get text() {
        const date = this.date;
        return `${String(date.getHours()-1).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}:${String(Math.floor(date.getMilliseconds()/10)).padStart(2, '0')}`;
    }
    get pause_milliseconds() {
        return this.timestamp_start && this.timestamp_paused ? this.timestamp_paused - this.timestamp_start : 0;
    }

    start() {
        if (this.pause_milliseconds) {
            this.timestamp_start = Date.now() - this.pause_milliseconds;
        } else {
            this.timestamp_start = Date.now();
        }
        this.timestamp_paused = 0;
    }

    pause() {
        if (!this.timestamp_paused) {
            this.timestamp_paused = Date.now();
        }
    }

    reset() {
        this.timestamp_start = 0;
        this.timestamp_end = 0;
    }
}


export class StopWatchLapManager {
    constructor({stopwatch, laps, function_persist_data}) {
        console.assert(stopwatch.text, 'stopwatch must be provided');
        console.assert(typeof(function_persist_data) == 'function', 'no persistent data-store function provided to StopWatchLapManager');

        this.stopwatch = stopwatch;
        this.function_persist_data = function_persist_data;
        this._laps = laps || [];

        this.lap = this.lap.bind(this);
        this.clear_lap_history = this.clear_lap_history.bind(this);
    }

    get laps() {
        return this._laps;
    }

    lap() {
        this._laps.push(this.stopwatch.text);
        this.function_persist_data(this._laps);
    }

    clear_lap_history() {
        this._laps = [];
        this.function_persist_data(this._laps);
    }
}

export default {
    StopWatch,
    StopWatchLapManager,
}