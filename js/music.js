var music = {};

(function(external){


	// Human readable input/output -------------------------------------------------
	
	var LOOKUP_NOTE_STR = {
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
	var LOOKUP_STR_NOTE = _.mapObject(_.invert(LOOKUP_NOTE_STR), function(val, key){return Number(val)});
	var NUM_NOTES_IN_OCTAVE = _.keys(LOOKUP_NOTE_STR).length;
	var OFFSET_FROM_C0 = NUM_NOTES_IN_OCTAVE * 2;

	function note_to_text(note) {
		//>>> note_to_text(0)
		//'C-2'
		//>>> note_to_text(24)
		//'C0'
		//>>> note_to_text(60)
		//'C3'
		//>>> note_to_text(61)
		//'C#3'
		return "" + LOOKUP_NOTE_STR[note % NUM_NOTES_IN_OCTAVE] +""+ Math.floor((note - OFFSET_FROM_C0)/NUM_NOTES_IN_OCTAVE);
	}

	function parse_note(item) {
		/*
		>>> parse_note('C-2')
		0
		>>> parse_note('C0')
		24
		>>> parse_note('C3')
		60
		>>> parse_note('C#3')
		61
		>>> parse_note('60')
		60
		>>> parse_note(60)
		60
		*/
		if (!isNaN(Number(item))) {
			return Number(item);
		}
		var regex_match = item.toUpperCase().match(/([ABCDEFG]#?)(-?\d{1,2})/);
		if (!regex_match) {
			console.warn("Unable to parse note", item);
		}
		var note_str = regex_match[1];
		var octave = Number(regex_match[2]);
		return LOOKUP_STR_NOTE[note_str] + (octave * NUM_NOTES_IN_OCTAVE) + OFFSET_FROM_C0;
	}

	var MIDI_STATUS_LOOKUP = {
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
			name:MIDI_STATUS_LOOKUP[status_code],
			channel: status_byte % 16,
		};
	}
	
	_.extendOwn(external, {
		'midi_status': midi_status,
		'note_to_text': note_to_text,
		'parse_note': parse_note,
	});

}(music));