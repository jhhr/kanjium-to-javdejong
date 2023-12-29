from anki import hooks
from aqt import mw
from aqt.browser import Browser
from anki.notes import Note, NoteId
from aqt import gui_hooks
from aqt.qt import QAction, qconnect
from aqt.operations import CollectionOp
from aqt.utils import showInfo


from collections.abc import Sequence

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
        
        # Find all kana characters
        all_kana_matches = re.findall(r'[ぁ-んァ-ンゞ゛゜ー]', pitch_accent_description)
        if all_kana_matches:
            for (i, kana_match) in enumerate(all_kana_matches):
                all_kana.append({'kana': kana_match, 'index': i, 'overline': False, 'down': False})

        if debug:
            print(all_kana)

        kana_iter = iter(all_kana)
        
        # Find characters that have an overline
        overline_kana_matches = re.findall(r'<span style="display:inline-block;position:relative;padding-right:0.1em;margin-right:0.1em;"><span style="display:inline;">([ぁ-んァ-ンゞ゛゜ー]*?)<\/span>(?!<span style="border-color:currentColor;display:block;user-select:none;pointer-events:none;position:absolute;top:0.1em;left:0;right:0;height:0;border-top-width:0.1em;border-top-style:solid;right:-0.1em;height:0.4em;border-right-width:0.1em;border-right-style:solid;"></span>)|<span style="display:inline;">([ぁ-んァ-ンゞ゛゜ー]*?)<\/span><span style="border-color:currentColor;display:block;user-select:none;pointer-events:none;position:absolute;top:0.1em;left:0;right:0;height:0;border-top-width:0.1em;border-top-style:solid;"><\/span>', pitch_accent_description)
        if overline_kana_matches:
            for overline_match in overline_kana_matches:
                if debug:
                    print('overline_match', overline_match)
                
                # Get the first or second match group
                overline_kana = overline_match[0] or overline_match[1]

                kana_def = next(kana_iter)
                while kana_def['kana'] != overline_kana:
                    kana_def = next(kana_iter)
                
                kana_def['overline'] = True

        # Find characters that have an overline and downpitch notch
        downpitch_matches = re.findall(r'<span style="display:inline;">([ぁ-んァ-ンゞ゛゜ー]*?)<\/span><span style="border-color:currentColor;display:block;user-select:none;pointer-events:none;position:absolute;top:0.1em;left:0;right:0;height:0;border-top-width:0.1em;border-top-style:solid;right:-0.1em;height:0.4em;border-right-width:0.1em;border-right-style:solid;"><\/span>', pitch_accent_description)
        if downpitch_matches:
            for downpitch_kana in downpitch_matches:
                if debug:
                    print('downpitch_kana', downpitch_kana)
                
                kana_def = next(kana_iter)
                while kana_def['kana'] != downpitch_kana:
                    kana_def = next(kana_iter)
                
                kana_def['overline'] = True
                kana_def['down'] = True

        result = ''
        started_overline = False
        ended_overline = False
        for kana_def in all_kana:
            if kana_def['overline'] and not started_overline:
                result += '<span style="text-decoration:overline;">'
                started_overline = True
            result += kana_def['kana']
            if kana_def['down']:
                result += '</span>&#42780;'
                ended_overline = True
            elif started_overline and not kana_def['overline']:
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
def convert_pitch_accent_notation_in_note(note: Note):
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

def bulk_convert_notes_op(col, notes: Sequence[Note]):
    pos = col.add_custom_undo_entry(f"Convert pitch accent notation for {len(notes)} notes.")
    for note in notes:
        convert_pitch_accent_notation_in_note(note)
    col.update_notes(notes)
    return col.merge_undo_entries(pos)


# Function to be executed when the "Convert Pitch Accent Notation" menu action is triggered
def convert_selected_notes(nids: Sequence[NoteId], parent: Browser):
       CollectionOp(
        parent=parent, op=lambda col: bulk_convert_notes_op(col, notes=[mw.col.get_note(nid) for nid in nids])
    ).success(
        lambda out: showInfo(
            parent=parent,
            title="Conversion done",
            textFormat="rich",
            text=f"Converted pitch accent notation in {len(nids)} selected notes."
        )
    ).run_in_background()


# Function to be executed when the browser menus are initialized
def on_browser_menus_did_init(browser: Browser):
    # Create a new action for the browser menu
    action = QAction("Convert Pitch Accent Notation", mw)
    # Connect the action to the convert_selected_notes function
    qconnect(action.triggered, lambda: convert_selected_notes(browser.selectedNotes(), parent=browser))
    # Add the action to the browser's card context menu
    browser.form.menuEdit.addAction(action)

# Register to card adding hook
hooks.note_will_be_added.append(lambda _col, note, _deck_id: convert_pitch_accent_notation_in_note(note))

# Register to browser menu initialization hook
gui_hooks.browser_menus_did_init.append(on_browser_menus_did_init)