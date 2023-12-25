from anki import hooks
from aqt import mw

import re

debug = False

def convert_kanjium_to_javdejong(kanjium_string):
    is_kanjium_pitch = re.search(r'currentColor', kanjium_string)
    if not is_kanjium_pitch:
        return kanjium_string

    # Split the input string into pitch accent descriptions
    pitch_accent_descriptions = kanjium_string.split('・')

    # Initialize a list to store the converted pitch accent descriptions
    javdejong_descriptions = []

    # Iterate through each pitch accent description
    for pitch_accent_description in pitch_accent_descriptions:
        if debug:
            print('pitch_accent_description', pitch_accent_description)
        all_kana = []
        all_kana_def = {}
        
        # Find all kana characters
        all_kana_matches = re.findall(r'[ぁ-んァ-ン]', pitch_accent_description)
        if all_kana_matches:
            for kana_match in all_kana_matches:
                all_kana.append(kana_match)
                all_kana_def[kana_match] = {'overline': False, 'down': False}

        if debug:
            print(all_kana)

        # Find characters that have an overline
        overline_kana_matches = re.findall(r'<span style="display:inline-block;position:relative;"><span style="display:inline;">([ぁ-んァ-ン]*?)<\/span><span style="border-color:currentColor;display:block;user-select:none;pointer-events:none;position:absolute;top:0.1em;left:0;right:0;height:0;border-top-width:0.1em;border-top-style:solid;"><\/span><\/span>', pitch_accent_description)
        if overline_kana_matches:
            for overline_kana in overline_kana_matches:
                if debug:
                    print('overline_match', overline_kana);
                all_kana_def[overline_kana]['overline'] = True

        # Find characters that have an overline and downpitch notch
        downpitch_matches = re.findall(r'<span style="display:inline-block;position:relative;padding-right:0.1em;margin-right:0.1em;"><span style="display:inline;">([ぁ-んァ-ン]*?)<\/span><span style="border-color:currentColor;display:block;user-select:none;pointer-events:none;position:absolute;top:0.1em;left:0;right:0;height:0;border-top-width:0.1em;border-top-style:solid;right:-0.1em;height:0.4em;border-right-width:0.1em;border-right-style:solid;"><\/span><\/span>', pitch_accent_description)
        if downpitch_matches:
            for downpitch_kana in downpitch_matches:
                if debug:
                    print('downpitch_kana', downpitch_kana)
                all_kana_def[overline_kana]['overline'] = True
                all_kana_def[overline_kana]['down'] = True

        result = ''
        started_overline = False
        ended_overline = False
        for overline_kana in all_kana:
            overline, down = all_kana_def[overline_kana]['overline'], all_kana_def[overline_kana]['down']
            if overline and not started_overline:
                result += '<span style="text-decoration:overline;">'
                started_overline = True
            result += overline_kana
            if down:
                result += '</span>&#42780;'
                ended_overline = True
            elif started_overline and not overline:
                result += '</span>'
                ended_overline = True

        if not ended_overline:
            result += '</span>'

        if debug:
            print('result', result)

        javdejong_descriptions.append(result)

    # Join the converted pitch accent descriptions with the separator ・
    javdejong_result = '・'.join(javdejong_descriptions)

    return javdejong_result


# Function to be executed when the add_cards_did_add_note hook is triggered
def on_add_card_convert_pitch_accent_notation(_col, note, _deck_id):
    # Check if the note has the 'vocab-pitch-pattern' field
    if 'vocab-pitch-pattern' in note:
        if debug:
            print('note has pitch-pattern')
        # Get the value of the 'vocab-pitch-pattern' field
        pitch_pattern = note['vocab-pitch-pattern']
        if debug:
            print('pitch_pattern',pitch_pattern)

        # Check if the value is non-empty
        if pitch_pattern:
            # Modify the pitch pattern using the Kanjium to Javdejong converter function
            modified_pitch_pattern = convert_kanjium_to_javdejong(pitch_pattern)

            # Update the note with the modified 'vocab-pitch-pattern' value
            note['vocab-pitch-pattern'] = modified_pitch_pattern

# Register to hook
hooks.note_will_be_added.append(on_add_card_convert_pitch_accent_notation)
