import {range} from './core.js'

// Human readable input/output -------------------------------------------------

const LOOKUP_NOTE_STR = {
    0: 'C',
    1: 'C#',
    2: 'D',
    3: 'D#',
    4: 'E',
    5: 'F',
    6: 'F#',
    7: 'G',
    8: 'G#',
    9: 'A',
    10: 'A#',
    11: 'B',
}
const LOOKUP_STR_NOTE = _.mapObject(_.invert(LOOKUP_NOTE_STR), function(val, key){return Number(val)});
const NUM_NOTES_IN_OCTAVE = LOOKUP_NOTE_STR.keys().length;
const OFFSET_FROM_C0 = NUM_NOTES_IN_OCTAVE * 2;

export function note_to_text(note, format='%NOTE_LETTER_WITH_SHARP%%OCTAVE%') {
    // TODO: Add string format default arg. eg: format='%NOTE% %OCTAVE%'
    // use something like "".replace('%NOTE%', note)

    //>>> note_to_text(0)
    //'C-2'
    //>>> note_to_text(24)
    //'C0'
    //>>> note_to_text(60)
    //'C3'
    //>>> note_to_text(61)
    //'C#3'
    //>>> note_to_text(0, format='%NOTE_LETTER_WITH_SHARP%')
    //'C'
    //>>> note_to_text(0, format='%OCTAVE%')
    //'-2'
    //>>> note_to_text(1, format='%NOTE_LETTER_WITH_SHARP%')
    //'C#'
    //>>> note_to_text(1, format='%NOTE_LETTER_WITH_FLAT%')
    //'Db'
    return format.replace(
        '%NOTE_LETTER_WITH_SHARP%', LOOKUP_NOTE_STR[note % NUM_NOTES_IN_OCTAVE]
    ).replace(
        '%OCTAVE%', Math.floor((note - OFFSET_FROM_C0)/NUM_NOTES_IN_OCTAVE)
    );
}

export function text_to_note(item) {
    /*
    >>> text_to_note('C-2')
    0
    >>> text_to_note('C0')
    24
    >>> text_to_note('C3')
    60
    >>> text_to_note('C#3')
    61
    >>> text_to_note('60')
    60
    >>> text_to_note(60)
    60
    >>> text_to_note('C')
    24
    >>> text_to_note('No!')
    null
    */
    if (!isNaN(Number(item))) {
        return Number(item);
    }
    const regex_match = item.toUpperCase().match(/([ABCDEFG]#?)(-?\d{1,2})/);
    if (!regex_match) {
        console.warn("Unable to parse note", item);
        return null;
    }
    const note_str = regex_match[1];
    const octave = Number(regex_match[2] || 0);
    return LOOKUP_STR_NOTE[note_str] + (octave * NUM_NOTES_IN_OCTAVE) + OFFSET_FROM_C0;
}

const MIDI_STATUS_LOOKUP = {
    0x8: 'note_off',
    0x9: 'note_on',
    0xA: 'polyphonic_aftertouch',
    0xB: 'control_change',
    0xC: 'program_change',
    0xD: 'channel_aftertouch',
    0xE: 'pitch_wheel',
};

export function midi_status(status_byte) {
    var status_code = Math.floor(status_byte/16);
    return {
        code: status_code,
        name:MIDI_STATUS_LOOKUP[status_code],
        channel: status_byte % 16,
    };
}

export function normalize_octave(note) {
    // >>> normalize_octave(0)
    // 0
    // >>> normalize_octave(24)
    // 0
    // >>> normalize_octave(25)
    // 1
    return note % NUM_NOTES_IN_OCTAVE;
}

export function* circle_of_fifths_notes(starting_note=0) {
    // >>> circle_of_fiths_notes()
    // [0, 8, 2, ... TODO]
    const _fifth_interval_in_semitones = 8;
    const _starting_note = text_to_note(starting_note);
    yield* range(NUM_NOTES_IN_OCTAVE).map(
        note => normalize_octave(_starting_note + (note * _fifth_interval_in_semitones))
    );
}

export function* circle_of_fifths_text(starting_note=0) {
    // Convenience method. For passing 'format' use .map() yourself
    // >>> circle_of_fifths_text()
    // ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F']
    yield* circle_of_fifths_notes(starting_note).map(note_to_text);
}

export default {
    midi_status,
    note_to_text,
    text_to_note,
    normalize_octave,
    circle_of_fifths_notes,
    circle_of_fifths_text,
}
