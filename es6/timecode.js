import {range, enumerate, assertEquals, assertEqualsObject} from './core.js'


export function parse_timesigniture(timesigniture_string) {
    const [beats, bar] = timesigniture_string.split(':').map(Number);
    return {'beats': beats, 'bar': bar};
}
assertEqualsObject([
    [
        parse_timesigniture('4:4'),
        {beats: 4, bar: 4}
    ],
]);


export function timecode_to_beat(timecode, timesigniture=parse_timesigniture('4:4')) {
    if (typeof(timecode) == 'string') {
        timecode = timecode.split('.').map(Number)
    }
    return [...enumerate(timecode)]
        .map(([index, timecode_component]) => timecode_component/Math.pow(timesigniture.bar, index))
        .reduce((acc, value) => acc + value)
    ;
}
assertEquals([
    [timecode_to_beat('4'), 4.0],
    [timecode_to_beat('4.0.0'), 4.0],
    [timecode_to_beat('4.1.0'), 4.25],
    [timecode_to_beat('4.2.0'), 4.5],
    [timecode_to_beat('4.2.2'), 4.625],
    [timecode_to_beat('4.6.0', parse_timesigniture('4:8')), 4.75],
]);


export function beat_to_timecode(beat, timesigniture=parse_timesigniture('4:4')) {
    function quotient(a, b) {return Math.floor(a/b);}
    function remainder(a, b) {return a % b;}
    const beat_number = quotient(beat, 1);
    const beat_remainder = remainder(beat, 1);
    return [beat_number].concat(
        [...range(2)].map((i)=>
            quotient(
                remainder(beat_remainder, 1/Math.pow(timesigniture.bar, i)),
                1/Math.pow(timesigniture.bar, i+1)
            )
        ))
        .join('.')
    ;
}
assertEquals([
    [beat_to_timecode(4.0), '4.0.0'],
    [beat_to_timecode(4.25), '4.1.0'],
    [beat_to_timecode(4.5), '4.2.0'],
    [beat_to_timecode(4.625), '4.2.2'],
    [beat_to_timecode(4.75, parse_timesigniture('4:8')), '4.6.0'],
]);


export function get_beat(time_current, bpm, time_start=0.0) {
    return Math.max(0.0, ((time_current - time_start) / 60) * bpm)
}


export function get_time(timecode, timesigniture, bpm) {
    return (timecode_to_beat(timecode, timesigniture) / bpm) * 60
}
assertEquals([
    [get_time('1.0.0', parse_timesigniture('4:4'), 10), 6.0],
    [get_time('10.0.0', parse_timesigniture('4:4'), 10), 60.0],
    [get_time('11.0.0', parse_timesigniture('4:4'), 10), 66.0],
    [get_time('15.0.0', parse_timesigniture('4:4'), 60), 15.0],
]);



export default {
    parse_timesigniture,
    timecode_to_beat,
    beat_to_timecode,
    get_beat,
    get_time,
}
