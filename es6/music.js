import {range, zip, buildMapFromObject, invertMap, MapDefaultGet, assertEquals, assertEqualsObject} from './core.js'

// Human readable input/output -------------------------------------------------

const NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
export const NUM_NOTES_IN_OCTAVE = NOTES.length;
const LOOKUP_STR_NOTE = new Map(zip(NOTES, range(NUM_NOTES_IN_OCTAVE)));
const LOOKUP_NOTE_STR = invertMap(LOOKUP_STR_NOTE);
const NOTE_ALIAS = new Map([['C#', 'Db'], ['D#', 'Eb'], ['F#', 'Gb'], ['G#', 'Ab'], ['A#', 'Bb']]);
for (let [note, note_alias] of NOTE_ALIAS.entries()) {
    LOOKUP_STR_NOTE.set(note_alias, LOOKUP_STR_NOTE.get(note));
}

const OFFSET_FROM_C0 = NUM_NOTES_IN_OCTAVE * 2;

export function note_to_text(note, {format='%NOTE_LETTER_WITH_SHARP%%OCTAVE%'}={}) {
    return format.replace(
        '%NOTE_LETTER_WITH_SHARP%', LOOKUP_NOTE_STR.get(note % NUM_NOTES_IN_OCTAVE)
    ).replace(
        '%OCTAVE%', Math.floor((note - OFFSET_FROM_C0)/NUM_NOTES_IN_OCTAVE)
    ).replace(
        '%NOTE_LETTER_WITH_FLAT%', NOTE_ALIAS.get(LOOKUP_NOTE_STR.get(note % NUM_NOTES_IN_OCTAVE))
    );
}
assertEquals([
    [note_to_text(0), 'C-2'],
    [note_to_text(24), 'C0'],
    [note_to_text(60), 'C3'],
    [note_to_text(61), 'C#3'],
    [note_to_text(0, {format:'%NOTE_LETTER_WITH_SHARP%'}), 'C'],
    [note_to_text(0, {format:'%OCTAVE%'}), '-2'],
    [note_to_text(1, {format:'%NOTE_LETTER_WITH_SHARP%'}), 'C#'],
    [note_to_text(1, {format:'%NOTE_LETTER_WITH_FLAT%'}), 'Db'],
]);

export function text_to_note(item) {
    if (!isNaN(Number(item))) {
        return Number(item);
    }
    item = `${item[0].toUpperCase()}${item.substr(1)}`;
    const regex_match = item.match(/([ABCDEFG][#b]?)(-?\d{1,2})?/);
    // const regex_match = item.toUpperCase().match(/([ABCDEFG]#?)(-?\d{1,2})/);
    if (!regex_match) {
        //console.warn("Unable to parse note", item);
        return null;
    }
    const note_str = regex_match[1];
    const octave = Number(regex_match[2] || 0);
    return LOOKUP_STR_NOTE.get(note_str) + (octave * NUM_NOTES_IN_OCTAVE) + OFFSET_FROM_C0;
}
assertEquals([
    [text_to_note('C-2'), 0],
    [text_to_note('C0'), 24],
    [text_to_note('C3'), 60],
    [text_to_note('C#3'), 61],
    [text_to_note('Db3'), 61],
    [text_to_note('60'), 60],
    [text_to_note(60), 60],
    [text_to_note('C'), 24],
    [text_to_note('No!'), null],
]);


export function normalize_octave(note) {
    return note % NUM_NOTES_IN_OCTAVE;
}
assertEquals([
    [normalize_octave(0), 0],
    [normalize_octave(24), 0],
    [normalize_octave(25), 1],
]);


export function* circle_of_fifths_notes(starting_note=0) {
    // >>> circle_of_fiths_notes()
    // [0, 8, 2, ... TODO]
    const _fifth_interval_in_semitones = 7;
    const _starting_note = text_to_note(starting_note);
    yield* [...range(NUM_NOTES_IN_OCTAVE)].map(
        note => normalize_octave(_starting_note + (note * _fifth_interval_in_semitones))
    );
}

export function* circle_of_fifths_text(starting_note=0) {
    // Convenience method. For passing 'format' use .map() yourself
    yield* [...circle_of_fifths_notes(starting_note)].map(note => note_to_text(note, {format:'%NOTE_LETTER_WITH_SHARP%'}));
}
assertEquals([
    [`${[...circle_of_fifths_text()]}`, ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F']],  // I have no fucking idea how this comparison works. It's madness! Try it in a console! `1,2,3` == [1,2,3]
]);


function normalize_notes_to_bitmask(notes) {
    return ([...notes]
        .map(text_to_note)
        .map(normalize_octave)
        .reduce((accumulator, note) => accumulator | 1 << note, 0)
    );
}
assertEquals([
    [normalize_notes_to_bitmask([]), 0],
    [normalize_notes_to_bitmask(['C']), 1],
    [normalize_notes_to_bitmask(['C#']), 2],
    [normalize_notes_to_bitmask(['D']), 4],
    [normalize_notes_to_bitmask(['D#']), 8],
    [normalize_notes_to_bitmask(['C', 'C#']), 3],
]);


// http://jjensen.org/CircleOf5thsFun.html
const CHORD_NAMES_RELATIVE_TO_C = buildMapFromObject({
    'major': ['C', 'E', 'G'],
    'minor': ['C', 'D#', 'G'],
    '5': ['C', 'G'],
    'major7': ['C', 'E', 'G', 'B'],
    'major7(add9)': ['C', 'E', 'G', 'B', 'D'],
    'major7(add13)': ['C', 'E', 'G', 'B', 'A'],
    'dom7': ['C', 'E', 'G', 'A#'], // C7
    'dom7(add9)': ['C', 'E', 'G', 'A#', 'D'], //C9
    'dom7(add13)': ['C', 'E', 'G', 'A#', 'A'], //C13 C7(add6)
    'minor7': ['C', 'D#', 'G', 'A#'], //Cm7
    'minor7(add9)': ['C', 'D#', 'G', 'A#', 'D'], //Cm9
    'minor7(add13)': ['C', 'D#', 'G', 'A#', 'A'], //Cm13
    'minor7(add11)': ['C', 'D#', 'G', 'A#', 'F'], //Cm7
    'minor(add7)': ['C', 'D#', 'G', 'B'], //Cm7
    'major9': ['C', 'E', 'G', 'A#', 'D'], // C9
    '7sus': ['C' ,'F', 'G', 'A#'],
    'dim': ['C', 'D#', 'F#'],
    'dim7': ['C', 'D#', 'F#', 'A'],
    'dim6': ['C', 'A', 'F#', 'D#'],
    'aug':  ['C', 'E', 'G#'], // C7#5
    'sus4': ['C', 'F', 'G'], // Csus
    'sus2': ['C', 'D', 'G'],
    'major6': ['C', 'E', 'G', 'A'], // C6
    'minor6': ['C', 'D#', 'G', 'A'], // Cm6
    'major6(add9)': ['C', 'D', 'E', 'G', 'A'],
});
const NOTE_BITMASK_CHORD_LOOKUP = function(){
    const chord_lookup = new Map();
    const chord_lookup_get_names = MapDefaultGet(chord_lookup, Array);
    for (let [chord_type_name, notes] of CHORD_NAMES_RELATIVE_TO_C.entries()) {
        notes = notes.map(text_to_note);
        for (let root_note of range(NUM_NOTES_IN_OCTAVE)) {
            const root_note_letter = note_to_text(root_note, {format:'%NOTE_LETTER_WITH_SHARP%'})
            const chord_name_full = `${root_note_letter}${chord_type_name}`;
            const notes_in_chord = notes.map(note => note + root_note);
            chord_lookup_get_names(
                normalize_notes_to_bitmask(notes_in_chord)
            ).push(chord_name_full);
        }
    }
    return chord_lookup;
}();
export function identify_chord(notes) {
    const notes_bitmask = normalize_notes_to_bitmask(notes);
    return NOTE_BITMASK_CHORD_LOOKUP.get(notes_bitmask)
    //notes = normalize_to_sorted_notes_as_single_octave(notes);
    //const [chord_name, root_index] = CHORD_LOOKUP[
    //    normalize_sorted_single_octave_to_interval_pattern_string(notes)
    //];
    //const root_note_text = note_to_text(
    //    notes[root_index],
    //    format='%NOTE_LETTER_WITH_SHARP%',
    //);
    //return `{root_note_text}{chord_type}`;
}
assertEquals([
    [identify_chord(['C', 'E', 'G'].map(text_to_note)), 'Cmajor'],
    [identify_chord(['C2', 'D#2', 'G1'].map(text_to_note)), 'Cminor'],
    [identify_chord(['C', 'G'].map(text_to_note)), 'C5'],
    [identify_chord(['G', 'C'].map(text_to_note)), 'C5'],
    [identify_chord(['D', 'A'].map(text_to_note)), 'D5'],
    [identify_chord(['C', 'D#', 'G', 'A#'].map(text_to_note)), 'Cminor7,D#major6'],
]);


// System ----------------------------------------------------------------------

const MIDI_STATUS_LOOKUP = {
    0x8: 'note_off',
    0x9: 'note_on',
    0xA: 'polyphonic_aftertouch',
    0xB: 'control_change',
    0xC: 'program_change',
    0xD: 'channel_aftertouch',
    0xE: 'pitch_wheel',
};
function midi_status(status_byte) {
    var status_code = Math.floor(status_byte/16);
    return {
        code: status_code,
        name: MIDI_STATUS_LOOKUP[status_code],
        channel: status_byte % 16,
    };
}
export function normalize_javascript_midi_msg(msg) {
    const midiMsg = {
        status: midi_status(msg.data[0]),
        note: msg.data[1],
        velocity: msg.data[2],
    }
    // Normalize note_off status
    if (midiMsg.status.name == 'note_on' && midiMsg.velocity == 0) {
        midiMsg.status.code = 0x8;
        midiMsg.status.name = 'note_off';
    }
    return midiMsg;
}
assertEqualsObject([
    [
        normalize_javascript_midi_msg({data:[0x9 * 16, 24, 8]}),
        {status: {code: 0x9, name: 'note_on', channel: 0}, note: 24, velocity: 8}
    ],
]);

// Exports ---------------------------------------------------------------------

export default {
    NUM_NOTES_IN_OCTAVE,
    midi_status,
    note_to_text,
    text_to_note,
    normalize_octave,
    circle_of_fifths_notes,
    circle_of_fifths_text,
    identify_chord,
    normalize_javascript_midi_msg,
}
