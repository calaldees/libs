import {enumerate, assertEquals, assertEqualsObject} from './core.js'


export function parse_timesignature(value) {
    if (typeof(value) == "string") {
        const [beats_in_bar, one_beat] = value.split(':').map(Number);
        return {'beats_in_bar': beats_in_bar, 'one_beat': one_beat};
    }
    return value;
}
assertEqualsObject([
    [parse_timesignature('4:4'), {beats_in_bar: 4, one_beat: 4}],
    [parse_timesignature('3:4'), {beats_in_bar: 3, one_beat: 4}],
    [parse_timesignature(parse_timesignature('4:8')), {beats_in_bar: 4, one_beat: 8}],
]);


export function timecode_to_beatcount(timecode, timesignature=parse_timesignature('4:4')) {
    timesignature = parse_timesignature(timesignature);
    if (typeof(timecode) == 'string') {
        timecode = timecode.split('.').map(Number)
    }
    return [...enumerate(timecode)]
        .map(([index, timecode_component]) => (timecode_component - 1) / Math.pow(timesignature.beats_in_bar, index - 1))
        .reduce((acc, value) => acc + value)
    ;
}
assertEquals([
    [timecode_to_beatcount('1.1.1'), 0.00],
    [timecode_to_beatcount('1.1.2'), 0.25],
    [timecode_to_beatcount('1.1.3'), 0.50],
    [timecode_to_beatcount('1.2.1'), 1.00],
    [timecode_to_beatcount('1.3.1'), 2.00],
    [timecode_to_beatcount('1.4.1'), 3.00],
    [timecode_to_beatcount('2.1.1'), 4.00],
    [timecode_to_beatcount('2.1.1', '3:4'), 3.00],
    [timecode_to_beatcount('3.1.1', '3:4'), 6.00],
    [timecode_to_beatcount('21.1.1', '3:4'), 60.0],
    [timecode_to_beatcount('2.1.1', '8:4'), 8.0],
    [timecode_to_beatcount('1.5.1', '8:4'), 4.0],
    [timecode_to_beatcount('8.5.1', '8:4'), 60.0],
    [timecode_to_beatcount('16.1.1', '4:4'), 60.0],
]);

export function beatcount_to_timecode(beat, timesignature=parse_timesignature('4:4'), slices=3) {
    timesignature = parse_timesignature(timesignature);
    function quotient(a, b) {return Math.floor(a/b);}
    function _pop_beat(accumulator, value) {
        const value_slice = quotient(value, timesignature.beats_in_bar);
        accumulator.push(1 + value_slice);
        if (accumulator.length < slices) {
            _pop_beat(accumulator, (value - (value_slice * timesignature.beats_in_bar)) * timesignature.beats_in_bar);
        }
        return accumulator
    }
    return _pop_beat([], beat).join('.');
}
assertEquals([
    [beatcount_to_timecode(5.25), '2.2.2'],
    [beatcount_to_timecode(2.0), '1.3.1'],
    [beatcount_to_timecode(0), '1.1.1'],
    [beatcount_to_timecode(4.0), '2.1.1'],
    [beatcount_to_timecode(60.0), '16.1.1'],
    [beatcount_to_timecode(2.0), '1.3.1'],
    [beatcount_to_timecode(0.25), '1.1.2'],
    [beatcount_to_timecode(3, '3:4'), '2.1.1'],
]);


// TODO: Reimplement?
//export function seconds_to_beatcount(time_current, bpm, time_start=0.0) {
//    return Math.max(0.0, ((time_current - time_start) / 60) * bpm)
//}

//export function timestamp_to_timecode(timestamp, bpm, timesigniture=parse_timesigniture('4:4')) {
//    return beat_to_timecode(get_beat(timestamp, bpm), timesigniture);
//}

export function timecode_to_seconds(timecode, bpm, timesignature=parse_timesignature('4:4')) {
    timesignature = parse_timesignature(timesignature);
    return timecode_to_beatcount(timecode, timesignature) * (60 / bpm) * (4 / timesignature.one_beat);
}
assertEquals([
    [timecode_to_seconds('1.1.1', 60, '4:4'), 0.0],
    [timecode_to_seconds('1.2.1', 60, '4:4'), 1.0],
    [timecode_to_seconds('1.3.1', 60, '4:4'), 2.0],
    [timecode_to_seconds('2.1.1', 60, '4:4'), 4.0],
    [timecode_to_seconds('16.1.1', 60, '4:4'), 60.0],
    [timecode_to_seconds('2.1.1', 60, '4:8'), 2.0],
    [timecode_to_seconds('31.1.1', 60, '4:8'), 60.0],
    [timecode_to_seconds('2.1.1', 60, '8:4'), 8.0],
    [timecode_to_seconds('8.5.1', 60, '8:4'), 60.0],
    [timecode_to_seconds('2.1.1', 30, '4:8'), 4.0],
    [timecode_to_seconds('2.1.1', 30, '8:4'), 16.0],
    [timecode_to_seconds('2.1.1', 60, '3:4'), 3.0],
    [timecode_to_seconds('21.1.1', 60, '3:4'), 60.0],
    [timecode_to_seconds('5.1.1', 60, '3:4'), 12.0],
    [timecode_to_seconds('14.3.3', 134, '3:4').toFixed(3), 18.657],
    [timecode_to_seconds('11.2.3.1', 134).toFixed(3), 18.582],
]);

export function seconds_to_timecode(seconds, bpm, timesignature=parse_timesignature('4:4')) {
    timesignature = parse_timesignature(timesignature);
    return beatcount_to_timecode(seconds / (60 / bpm) / (4 / timesignature.one_beat), timesignature);
}
assertEquals([
    [seconds_to_timecode(0.0, 60, '4:4'), '1.1.1'],
    [seconds_to_timecode(4.0, 60, '4:4'), '2.1.1'],
    [seconds_to_timecode(3.0, 60, '3:4'), '2.1.1'],
    [seconds_to_timecode(60.0, 60, '8:4'), '8.5.1'],
    [seconds_to_timecode(60.0, 60, '4:8'), '31.1.1'],
]);



export function next_frame_from_timecode(timecode, frame_rate) {
    return Math.ceil(timecode * frame_rate);
}

export function nearest_timecode_to_next_frame(timecode, frame_rate) {
    return next_frame_from_timecode(timecode, frame_rate) / frame_rate;
}
assertEquals([
    [nearest_timecode_to_next_frame(11.0, 1), 11.0],
    [nearest_timecode_to_next_frame(11.1, 1), 12.0],
    [nearest_timecode_to_next_frame(11.0, 4), 11.0],
    [nearest_timecode_to_next_frame(11.72, 4), 11.75],
    [nearest_timecode_to_next_frame(11.1, 4), 11.25],
]);


export default {
    parse_timesignature,
    timecode_to_beatcount,
    beatcount_to_timecode,
    //seconds_to_beatcount,
    //timestamp_to_timecode,
    timecode_to_seconds,
    seconds_to_timecode,
    next_frame_from_timecode,
    nearest_timecode_to_next_frame,
}
