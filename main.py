#sometimes its kinda relaxing to write bad code
#and actually make things happen
#(Though I should really write a proper TUI framework one day)

from blessed import Terminal
from json import dumps, loads
from dataclasses import dataclass, field, asdict
from random import shuffle, randint, choice
from rapidfuzz import process
import webbrowser as wb
import datetime as dt
import os as os
import wave
from piper import PiperVoice, SynthesisConfig
import subprocess

DECKS = "/Users/ajayvallurupalli/the-playground/work/deutsch/saves/decks.json"
TIMES = "/Users/ajayvallurupalli/the-playground/work/deutsch/saves/times"
VOICE = "/Users/ajayvallurupalli/the-playground/work/deutsch/saves/voices"
AUDIO = "/Users/ajayvallurupalli/the-playground/work/deutsch/saves/audio"

#for typing stuff
valid_characters = "qwertyuiopasdfghjklzxcvbnm,./;'\"*QWERTYUAISODPFLGKJHCBXZNVMBüÜäÄöÖ 1234567890"

class Part_Of_Speech:
    Noun = 1
    Verb = 2
    Adjective = 3
    Adverb = 4
    Preposition = 5
    Phrase = 6

speech_map = {"Noun": Part_Of_Speech.Noun, "Verb": Part_Of_Speech.Verb, "Adjective": Part_Of_Speech.Adjective,
                "Adverb": Part_Of_Speech.Adverb, "Preposition": Part_Of_Speech.Preposition, "Phrase": Part_Of_Speech.Phrase}
parse_speech = lambda x: speech_map[x]
show_speech = lambda x: {value: key for key, value in speech_map.items()}[x]

verb_modes = ["Present", "Preterite", "Past Perfect", "Reflexive"]
parse_mode = lambda x: {"Present": Verb_Modes.Present, "Preterite": Verb_Modes.Preterite, "Past Perfect": Verb_Modes.Past_Perfect,
                        "Reflexive": Verb_Modes.Reflexive}[x]

syn_config = SynthesisConfig(
    length_scale=1.5,  # a little slower
)

@dataclass
class Tag:
    tag: str 
    refs: int

    def __eq__(self, other):
        return isinstance(other, Tag) and self.tag == other.tag

    def __hash__(self):
        return hash(self.tag)

class Verb_Modes:
    Present = 1
    Preterite = 2
    Past_Perfect = 3
    Reflexive = 4

@dataclass
class Word:
    german: str
    english: str
    part_of_speech: int
    tags: list[str]
    deck: int = 0
    deck_name: str = ""
    times_played: int = 0
    def play_audio(self, voice: PiperVoice):
        if not os.path.exists(f"{AUDIO}/{self.deck_name.replace("/", ".")}"):
            os.mkdir(f"{AUDIO}/{self.deck_name.replace("/", ".")}")
        if f"{self.german}.wav" not in os.listdir(f"{AUDIO}/{self.deck_name.replace("/", ".")}"):
            with wave.open(f"{AUDIO}/{self.deck_name.replace("/", ".")}/{self.german}.wav", "wb") as wav_file:
                voice.synthesize_wav(f"{self.german}", wav_file, syn_config=syn_config)
        subprocess.run(["ffplay", "-nodisp", "-autoexit", f"{AUDIO}/{self.deck_name.replace("/", ".")}/{self.german}.wav"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@dataclass
class Noun(Word):
    plural: str = None
    gender: str = None #i cant be bothered to make an enum

    def play_audio(self, voice: PiperVoice):
        if not os.path.exists(f"{AUDIO}/{self.deck_name.replace("/", ".")}"):
            os.mkdir(f"{AUDIO}/{self.deck_name.replace("/", ".")}")
        articles = {"Female": "Die", "Male": "Der", "Neuter": "Das"}
        if f"{self.german}.wav" not in os.listdir(f"{AUDIO}/{self.deck_name.replace("/", ".")}"):
            with wave.open(f"{AUDIO}/{self.deck_name.replace("/", ".")}/{self.german}.wav", "wb") as wav_file:
                if "No Plural" in self.tags: voice.synthesize_wav(f"{articles[self.gender]} {self.german}", wav_file, syn_config=syn_config)
                else: voice.synthesize_wav(f"{articles[self.gender]} {self.german}, die {self.plural}", wav_file, syn_config=syn_config)
        subprocess.run(["ffplay", "-nodisp", "-autoexit", f"{AUDIO}/{self.deck_name.replace("/", ".")}/{self.german}.wav"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@dataclass
class Verb(Word):
    mode: int = None

@dataclass 
class Deck:
    name: str 
    times_played: int = 0
    words: list[Word | Noun | Verb] = field(default_factory=list)

@dataclass
class PlayTime:
    day: int 
    time: int #seconds

#Type aliases in python????
type Progress = dict[int, dict[str, dict[int, PlayTime]]]


def deserialize(d: dict[str, str]): 
    result = []
    for item in d["words"]:
        if item["part_of_speech"] == 1: result.append(Noun(**item))
        elif item["part_of_speech"] == 2: result.append(Verb(**item))
        else: result.append(Word(**item))

    return Deck(d["name"], d["times_played"], result)

def option(options: list[str], after: list[str] = None, lpadding: int = 2, rpadding: int = 3, style: str = "", sp_style: str = None, shortcuts: dict[int, str] = {}, range_: int = None, start_index = None):
    sp_style = sp_style if sp_style != None else style
    range_ = term.height // 2 - 5 if range_ == None else range_
    after = [] if after == None else after
    after += [""] * (len(options) - len(after))
    selected_index = 0 if start_index == None else start_index
    unpadded_options = options.copy()
    options = options.copy()
    max_length = max(map(len, options))
    for i, x in enumerate(options): options[i] = x.ljust(max_length + rpadding)
    for i, _ in enumerate(options): options[i] = options[i] + after[i]
    while True:
        print(style)
        if selected_index <= range_:
            bottom = 0
            ranged_options = options[bottom:selected_index] + options[selected_index:min(range_ + range_ + 1, len(options))]
        elif selected_index + range_ >= len(options):
            bottom = max(0, len(options) - (range_ + range_ + 1))
            ranged_options = options[bottom:selected_index] + options[selected_index:len(options)]
        else:
            bottom = selected_index - range_
            ranged_options = options[bottom:min(len(options), selected_index + range_ + 1)]
        for index, option in enumerate(ranged_options):
            if index == (selected_index - bottom):
                print(term.bold + term.black_on_paleturquoise1(' ' * lpadding + f"{option}")) # Highlight selected option
            else:
                print(' ' * lpadding + f"{option}")

        with term.cbreak(), term.hidden_cursor():
            key = term.inkey()

        if key.code == term.KEY_UP or key == "w":
            selected_index -= 1
            selected_index += len(options)
            selected_index %= len(options)
        elif key.code == term.KEY_DOWN or key == "s":
            selected_index += 1
            selected_index %= len(options)
        elif key.code == term.KEY_RIGHT or key == "d":
            selected_index += range_
            selected_index %= len(options)
        elif key.code == term.KEY_LEFT or key == "a":
            selected_index -= range_
            selected_index += len(options)
            selected_index %= len(options)
        elif key == ' ' or key.code == term.KEY_ENTER: 
            return {"choice": unpadded_options[selected_index], "index": selected_index}
        elif key == "+" and shortcuts != {}:
            print(term.clear)
            print(sp_style)
            for key, value in shortcuts.items():
                if key != "+": print(term.black_on_plum1(term.center(f"[{key}]: {value:>30}")))
            

            print()
            print()
            print()
            print(term.black_on_plum1(term.center(f"Press any key to go back")))
            with term.cbreak(), term.hidden_cursor():
                _ = term.inkey()
        elif key in shortcuts:
                return {"choice": shortcuts[key], "index": selected_index}

def get_text(term: Terminal, prompt: str, starting: str = "", shortcuts: dict = {}):
    txt = starting
    umlauts = {"u":"ü", "a": 'ä', "o":"ö","U":"Ü", "A": 'Ä', "O":"Ö"}
    while True:
        print(prompt)
        print(term.black_on_plum1(term.center(txt)))
        with term.cbreak(), term.hidden_cursor():
            key = term.inkey()

        if len(txt) > 0 and (txt[-1] == "\"" and key in "uoaUOA"):
            txt = txt[0:-1]
            txt += umlauts[key]
        elif len(txt) > 0 and (key == "\"" and txt[-1] in "uoaUOA"):
            before = txt[-1]
            txt = txt[0:-1]
            txt += umlauts[before]
        elif key in valid_characters:
            txt += key 
        elif key.code == term.KEY_ENTER:
            return txt
        elif key.code == term.KEY_BACKSPACE:
            txt = txt[0:-1]
        elif key == "+" and shortcuts != {}:
            for key, value in shortcuts.items():
                if key != "+": print(term.black_on_plum1(term.center(f"[{key}]: {value:>30}")))
            with term.cbreak(), term.hidden_cursor():
                _ = term.inkey()
        elif key in shortcuts:
            return shortcuts[key]
            

def build_word(term: Terminal, prompt: str, fields: list[str], defaults: list[str] = None):
    if defaults == None: defaults = [""] * len(fields)

    results = []
    
    for index, element in enumerate(fields):
        prompt2 = prompt + term.black_on_plum(term.center("Enter " + element))
        results.append(get_text(term, prompt2, starting=defaults[index]))

    return results

def header(term: Terminal, heads: list[str]):
    start = term.clear + term.home + term.move_y(0)
    for h in heads:
        start += term.black_on_plum(term.center(h))
    return start

def down(term: Terminal) -> str:
    return term.move_y(5)

term = Terminal()
menu_style = lambda x: header(x, ["Choose an option"]) + down(x)

def init():
    print(term.home + term.clear + term.move_y(term.height // 2))
    print(term.black_on_paleturquoise1(term.center('press any key to continue.')))

    with term.cbreak(), term.hidden_cursor():
        _ = term.inkey()

def menu():
    menu_options = ['Edit Decks', 'Play', 'Stats', "Exit"]
    tags = set()
    decks = save([], tags=tags)
    times = save_time(None, None)
    selected_tag = []
    loop = True
    stack = []
    voice = PiperVoice.load(f"{VOICE}/thor-voice.onnx")
    while loop:
        shortcuts = {"n": "Save Decks"}
        if len(stack) > 0:
            shortcuts["p"] = "Pop Item Off Stack"
            shortcuts["P"] = "Pop all Items Off Stack"
            shortcuts["l"] = "Show Top of Stack"
            shortcuts["L"] = "Show all Stack"
        if selected_tag != None and len(selected_tag) == 1:
            shortcuts['t'] = "Show Selected Tag"

        choice = option(menu_options, style=menu_style(term), sp_style=(menu_style(term) + term.move_y(3)), shortcuts=shortcuts)['choice']
        if choice == menu_options[0]: decks = create_deck(term, decks, stack, tags, selected_tag, voice)
        elif choice == menu_options[1]: 
            (decks, new_time) = start_play(decks, times, stack, voice)
            if new_time != None: 
                times = save_time(times, new_time)
        elif choice == menu_options[2]:
            show_times(times)
        elif choice == menu_options[3]: loop = False
        elif choice == shortcuts['n']:
            decks = save(decks)
            print(term.clear)
            print(menu_style(term))
            print(term.black_on_plum1(term.center(f"Saved!")))
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()
        elif len(stack) > 0 and choice == shortcuts['p']:
            pop = stack.pop()
            print(term.clear)
            print(menu_style(term))
            print(term.black_on_plum1(term.center(f"Popped [{show_translation(pop["word"])}] off")))
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()
        elif len(stack) > 0 and choice== shortcuts["P"]:
            print(term.clear)
            print(menu_style(term))
            while len(stack) > 0:
                pop = stack.pop()
                print(term.black_on_plum1(term.center(f"Popped [{show_translation(pop["word"])}] off")))
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()
        elif len(stack) > 0 and choice == shortcuts['l']:
            pop = stack.pop()
            print(term.clear)
            print(menu_style(term))
            print(term.black_on_plum1(term.center(f"Top of Stack: ")))
            print(term.black_on_plum1(term.center(f"[{show_translation(pop["word"])}]")))
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()
            stack.append(pop)
        elif len(stack) > 0 and choice == shortcuts['L']:
            print(term.clear)
            print(menu_style(term))
            print(term.black_on_plum1(term.center(f"Stack: ")))
            for item in stack:
                print(term.black_on_plum1(term.center(f"[{show_translation(item["word"])}]")))
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()
        elif selected_tag != None and len(selected_tag) == 1 and choice == shortcuts['t']:
            print(term.clear)
            print(menu_style(term))
            print(term.black_on_plum1(term.center(f"Selected Tag: {selected_tag[0].tag}")))
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()

    decks = save(decks)

def show_translation(word: Word, plural=False):
    if word.part_of_speech == Part_Of_Speech.Verb:
        if word.mode == Verb_Modes.Reflexive:
            return "To " + word.english + " - " + word.german + " sich"
        else:
            return "To " + word.english + " - " + word.german
    elif word.part_of_speech == Part_Of_Speech.Noun:
        if plural:
            return word.english + " (plural) - die " + word.plural
        else:
            articles = {"Female": "Die", "Male": "Der", "Neuter": "Das"}
            return word.english + " - " + articles[word.gender] + " " + word.german
    else:
        return word.english + " - " + word.german

speech_options = ["Noun", "Verb", "Adjective", "Adverb", "Preposition", "Phrase"]
def edit_word(term: Terminal, selected_deck: Deck, deck_index: int, speech: str, defaults: list[str] = None, edit: bool = False):
    if speech == speech_options[0]:
        head = [f"Edit {speech} {defaults[0]} in {selected_deck.name}"] if edit else [f"Add {speech} to {selected_deck.name}"]
        prompt = header(term, head)
        prompt += down(term)


        gender_prompt = header(term, ["Add Noun to " + selected_deck.name, "Select Gender"])
        gender_prompt += term.move_y(2)

        read = build_word(term, prompt, ["German Singular:", "German Plural:", "English Singular:"], defaults=defaults)
        gender = option(["Male", "Female", "Neuter"], style = gender_prompt)

        return Noun(read[0], read[2], Part_Of_Speech.Noun, [], deck_index, selected_deck.name, plural=read[1],gender=gender['choice'])
    elif speech == speech_options[1]:
        head = [f"Edit {speech} {defaults[0]} in {selected_deck.name}"] if edit else [f"Add {speech} to {selected_deck.name}"]
        prompt = header(term, head)
        prompt += down(term)

        mode_prompt = header(term, ["Add Verb to " + selected_deck.name, "Select Mode"])
        mode_prompt += term.move_y(2)

        read = build_word(term, prompt, ["German:", "English:"], defaults=defaults)
        mode = option(verb_modes, style=mode_prompt)

        return Verb(read[0], read[1], Part_Of_Speech.Verb, [], deck_index, selected_deck.name, mode=parse_mode(mode['choice']))

    elif speech in speech_options[2:-1]:
        head = [f"Edit {speech} {defaults[0]} in {selected_deck.name}"] if edit else [f"Add {speech} to {selected_deck.name}"]
        prompt = header(term, head)
        prompt += down(term)

        read = build_word(term, prompt, ["German:", "English:"], defaults=defaults)

        return Word(read[0], read[1], parse_speech(speech), [], deck_index, selected_deck.name)
    else:
        print(speech)

def handle_deck(decks, deck_index, stack, tags, selected_tag, voice, jump = None): 
    selected_deck = decks[deck_index]
    extra_options = ["-------", "Add a Word", "Go Back"]
    shortcuts = {"-": "Decrement Plays", "_": "Zero Plays", "k": "Delete Word", "!": "Go Back", "o": "Push on Stack", "v": "Play Generated Pronunciation"}
    selected_index = 0
    if jump != None: 
        for index, item in enumerate(selected_deck.words):
            if item == jump:
                selected_index = index
    if selected_tag != None and len(selected_tag) == 1:
        shortcuts['T'] = "Add Selected Tag"
        shortcuts['t'] = "Show Selected Tag"
    deck_loop = True

    while deck_loop:
        #head and options need to be in the loop because they can change
        head = header(term, ["Edit " + selected_deck.name, f"Played {str(selected_deck.times_played)} times. {len(selected_deck.words)} words."])
        options = list(map(lambda x: show_translation(x), selected_deck.words)) + extra_options
        choice = option(options, style=(head + down(term)), sp_style=(head + down(term) + term.move_y(3)), shortcuts=shortcuts, start_index=selected_index)
        if choice['choice'] == options[-3]: continue
        elif choice["choice"] == options[-1]: # Go Back
            deck_loop = False
        elif choice['choice'] == options[-2]: # Add a word
            head = header(term, ["Edit " + selected_deck.name])
            choice = option(speech_options, style=(head + down(term)))

            selected_deck.words.append(edit_word(term, selected_deck, deck_index, choice['choice']))
        elif choice['choice'] == shortcuts['-']:
            selected_index = choice['index']
            selected_deck.times_played -= 1
        elif choice['choice'] == shortcuts["_"]:
            selected_index = choice['index']
            selected_deck.times_played = 0
        elif choice ['choice'] == shortcuts["k"]:
            if choice['index'] < len(selected_deck.words):
                selected_index = choice['index']
                if os.path.exists(f"{AUDIO}/{selected_deck.words[choice['index']].deck_name.replace("/", ".")}/{selected_deck.words[choice['index']].german}.wav"):
                    subprocess.run(["rm", "-f", f"{AUDIO}/{selected_deck.words[choice['index']].deck_name.replace("/", ".")}/{selected_deck.words[choice['index']].german}.wav"])
                del selected_deck.words[choice['index']]
        elif choice["choice"] == shortcuts["v"]:
            if choice['index'] < len(selected_deck.words): 
                selected_index = choice['index']
                selected_deck.words[choice['index']].play_audio(voice)

        elif choice['choice'] == shortcuts["!"]:
            deck_loop = False
        elif choice['choice'] == shortcuts["o"]:
            if choice['index'] < len(selected_deck.words):
                selected_index = choice['index']
                stack.append({"word": selected_deck.words[choice['index']], "deck": deck_index})
        elif selected_tag != None and len(selected_tag) == 1 and choice['choice'] == shortcuts['T']:
            if choice['index'] < len(selected_deck.words):
                selected_word = selected_deck.words[choice['index']]
                fake_tags = set(map(lambda x: Tag(x, 0), selected_word.tags))
                if selected_tag[0] not in fake_tags:
                    selected_tag[0].refs += 1
                    selected_word.tags.append(selected_tag[0].tag)
        elif selected_tag != None and len(selected_tag) == 1 and choice['choice'] == shortcuts['t']:
            print(term.clear)
            print(menu_style(term))
            print(term.black_on_plum1(term.center(f"Selected Tag: {selected_tag[0].tag}")))
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()
        else: #a word is selected
            word_loop = True
            selected_word = selected_deck.words[choice['index']]
            while word_loop:
                head = header(term, [
                    "Edit " + selected_deck.name, f"Played {str(selected_deck.times_played)} times. {len(selected_deck.words)} words.",
                    "Edit " + selected_word.german, f"Played {str(selected_word.times_played)} times."
                ])
                #              0          1             2           3                      4                              5                      6
                options = ["Add Tag", "Show Tags", "Edit Word", "Open Forvo", "Play Generated Pronunciation", "Delete Generated Pronunciation", "Delete", "Go Back"]

                choice = option(options, style=(head + term.move_y(5)))

                if choice["choice"] == options[3]: wb.open(f"https://forvo.com/search/{selected_word.german}/de", new=2)
                elif choice["choice"] == options[4]: selected_word.play_audio(voice)
                elif choice["choice"] == options[5]: 
                    if os.path.exists(f"{AUDIO}/{selected_word.deck_name.replace("/", ".")}/{selected_word.german}.wav"):
                        subprocess.run(["rm", "-f", f"{AUDIO}/{selected_word.deck_name.replace("/", ".")}/{selected_word.german}.wav"])
                elif choice['choice'] == options[6]: 
                    if os.path.exists(f"{AUDIO}/{selected_word.deck_name.replace("/", ".")}/{selected_word.german}.wav"):
                        subprocess.run(["rm", "-f", f"{AUDIO}/{selected_word.deck_name.replace("/", ".")}/{selected_word.german}.wav"])
                    selected_deck.words.remove(selected_word)
                elif choice['choice'] == options[0]: 
                    fake_tags = set(map(lambda x: Tag(x, 0), selected_word.tags))
                    pos_tags = tags - fake_tags
                    new_tag = show_matches(term, pos_tags, 4, style_without_down=head)
                    if new_tag != None:
                        new_tag.refs += 1
                        selected_word.tags.append(new_tag.tag)
                elif choice['choice'] == options[1]:
                    in_tags = set(filter(lambda x: x.tag in selected_word.tags, tags))
                    if len(in_tags) > 0: 
                        show_matches(term, in_tags, 4, style_without_down=head)
                    else:
                        print(term.clear)
                        print(head)
                        print(term.center(term.white_on_black("Word has no tags!")))
                        print(term.move_down(2))
                        with term.cbreak(), term.hidden_cursor():
                            _ = term.inkey()
                        



                elif choice['choice'] == options[2]:
                    if selected_word.part_of_speech == Part_Of_Speech.Noun: #why does this branch?? not even god knows
                        defaults = [selected_word.german, selected_word.plural, selected_word.english]
                        new_word = edit_word(term, selected_deck, deck_index, "Noun", defaults=defaults, edit=True)
                        new_word.times_played = selected_word.times_played
                    else:
                        defaults = [selected_word.german, selected_word.english]
                        new_word = edit_word(term, selected_deck, deck_index, show_speech(selected_word.part_of_speech), defaults=defaults, edit=True)
                        new_word.times_played = selected_word.times_played


                    selected_deck.words.remove(selected_word)
                    selected_deck.words.append(new_word)
                
                else: word_loop = False # not sure how this oculd happen
            

def choose_deck(head: str, decks: list[Deck], extra_options: list[str], head_small = None, pred = lambda x: True, shortcuts = {}, start_index=None):
    head_small = head_small if head_small != None else head
    filtered = list(filter(pred, decks))
    options = list(map(lambda x: x.name, filtered))
    after = list(map(lambda x: " | Played " + str(x.times_played) + " times.", filtered))
    return {"filtered": filtered, "option": option(options + extra_options, style=head, sp_style=head_small, after=after, shortcuts=shortcuts, start_index=start_index)}

#work!
def show_matches(term, on: set[Tag], show: int, style_without_down: str = "", add: bool = False, selected_tag=None) -> None | Tag | str:
    on2 = list(on)
    search = ""
    start_index = 0

    while True:
        print(style_without_down)
        print(term.black_on_plum(term.center("Press '!' to exit")))
        print(down(term))

        print(term.black_on_plum1(term.center(f"{"Add" if add else "Search"}: {search}")))
        print(term.move_down(1))

        selected = process.extract(search, map(lambda x: x.tag, on2))
        for index, x in enumerate(selected[start_index:show+start_index]):
            if x[0] == search: print(term.black_on_paleturquoise(f"  {index + start_index + 1}. {x[0]:<35}| Used {on2[x[2]].refs} Times"))
            else: print(term.black_on_paleturquoise1(f"  {index + start_index + 1}. {x[0]:<35}| Used {on2[x[2]].refs} Times"))

        with term.cbreak(), term.hidden_cursor():
            key = term.inkey()

        if key.code == term.KEY_UP and start_index > 0: start_index -= 1
        elif key.code == term.KEY_DOWN and start_index < show - 1: start_index += 1
        elif key.code == term.KEY_BACKSPACE: search = search[0:-1]
        elif key.code == term.KEY_ENTER: 
            if add: 
                if len(on2) == 0:
                    return search
                elif on2[selected[start_index][2]].tag == search:
                    return on2[selected[start_index][2]]
                else: return search
            else: 
                if selected_tag != None: 
                    if len(selected_tag) > 0: selected_tag.pop()
                    selected_tag.append(on2[selected[start_index][2]])
                return on2[selected[start_index][2]]
        elif key == "!": break
        elif key in valid_characters: search += key

    return None


def handle_tags(term, tags: set[Tag], selected_tag: list[Tag]):
    head = header(term, ["Edit Decks", "Register Tags"]) + down(term)
    options = ["Browse Tags", "Select Tag", "Add Tags", "Go Back"]
    loop = True
    while loop:
        choice = option(options, style=head)
        if choice['choice'] == options[0]:
            head2 = header(term, ["Edit Decks", "Register Tags", "Browse Tags"])
            show_matches(term, tags, 3, style_without_down=head2)
        elif choice['choice'] == options[1]:
            head2 = header(term, ["Edit Decks", "Register Tags", "Browse Tags"])
            show_matches(term, tags, 3, style_without_down=head2, selected_tag=selected_tag)

        elif choice['choice'] == options[2]:
            head2 = header(term, ["Edit Decks", "Register Tags", "Add Tag"])
            res = show_matches(term, tags, 3, style_without_down=head2, add=True)
            if type(res) == Tag:
                print(term.clear)
                print(head2)
                print(term.move_down(2))
                print(term.white_on_black(term.center(f"Tag already exists!")))
                with term.cbreak(), term.hidden_cursor():
                    _ = term.inkey()
            elif res == None: pass
            else:
                print(term.clear)
                print(head2)
                print(term.move_down(2))
                print(term.black_on_plum(term.center(f"Added {res}!")))
                tags.add(Tag(res, 0))
                with term.cbreak(), term.hidden_cursor():
                    _ = term.inkey()

        else: loop = False

def create_deck(term, decks, stack, tags, selected_tag, voice):
    loop = True
    selected_index = 0

    while loop:
        head = header(term, ["Edit Decks"]) + down(term)
        extra_options = ["-------","Make a Deck", "Register Tags", "Go Back"]
        shortcuts = {"-": "Decrement Plays", "_": "Zero Plays", "k": "Kill Deck"}
        if len(stack) > 0:
            shortcuts["p"] = "Pop Item Off Stack"
            shortcuts["P"] = "Pop all Items Off Stack"
            shortcuts["l"] = "Show Top of Stack"
            shortcuts["L"] = "Show all Stack"
            shortcuts['j'] = "Jump to Top of Stack"
        choice = choose_deck(head, decks, extra_options, head_small=(header(term, ["Edit Decks"]) + term.move_y(3)), shortcuts=shortcuts, start_index=selected_index)["option"]
        if choice["choice"] == extra_options[0]: continue
        elif choice['choice'] == extra_options[1]:
            prompt = header(term, ["Edit Decks", "Name new Deck"]) + down(term)

            name = get_text(term, prompt)
            print(term.black_on_plum(term.center("Deck Created!")))
            return decks + [Deck(name=name)]
        elif choice['choice'] == extra_options[2]:
            handle_tags(term, tags, selected_tag)
        elif choice['choice'] == shortcuts["-"]:
            if choice['index'] < len(decks): #valid deck
                decks[choice['index']].times_played -= 1 
            selected_index = choice['index']
        elif choice['choice'] == shortcuts["_"]:
            if choice["index"] < len(decks):
                decks[choice["index"]].times_played = 0
            selected_index = choice['index']
        elif choice['choice'] == shortcuts["k"]:
            if choice["index"] < len(decks):
                attempt = decks[choice["index"]].name
                print(term.clear)
                print(head)
                print(term.white_on_black(term.center("Are you sure you want to delete {attempt} deck? Press [k] to actually delete.")))
                with term.cbreak(), term.hidden_cursor():
                    key = term.inkey()
                if key == "k":
                    if os.path.exists(f"{AUDIO}/{attempt}"):
                        print("hello")
                        with term.cbreak(), term.hidden_cursor():
                            key = term.inkey()
                        subprocess.run(["rm", "-rf", f"{AUDIO}/{attempt.replace("/", ".")}"])
                    new_decks = [deck for deck in decks if deck.name != attempt]
                    
                else: continue

                return new_decks
        elif len(stack) > 0 and choice['choice'] == shortcuts['p']:
            pop = stack.pop()
            print(term.clear)
            print(head)
            print(term.black_on_plum1(term.center(f"Popped [{show_translation(pop["word"])}] off")))
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()
        elif len(stack) > 0 and choice['choice'] == shortcuts["P"]:
            print(term.clear)
            print(head)
            while len(stack) > 0:
                pop = stack.pop()
                print(term.black_on_plum1(term.center(f"Popped [{show_translation(pop["word"])}] off")))
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()
        elif len(stack) > 0 and choice['choice'] == shortcuts['l']:
            pop = stack.pop()
            print(term.clear)
            print(head)
            print(term.black_on_plum1(term.center(f"Top of Stack: ")))
            print(term.black_on_plum1(term.center(f"[{show_translation(pop["word"])}]")))
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()
            stack.append(pop)
        elif len(stack) > 0 and choice['choice'] == shortcuts['L']:
            print(term.clear)
            print(head)
            print(term.black_on_plum1(term.center(f"Stack: ")))
            for item in stack:
                print(term.black_on_plum1(term.center(f"[{show_translation(item["word"])}]")))
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()
        elif len(stack) > 0 and choice['choice'] == shortcuts['j']:
            pop = stack.pop()
            handle_deck(decks, pop["deck"], stack, tags, selected_tag, voice, jump=pop["word"])


        elif choice['choice'] == extra_options[3]: loop = False #goback
        else: handle_deck(decks, choice["index"], stack, tags, selected_tag, voice)  

    return decks  

def ask(word, english, plural):
    result = {"prompt": None, "question": None, "answer": None}
    if english:
        result["question"] = word.english
        if word.part_of_speech == Part_Of_Speech.Noun and plural() and "No Plural" not in word.tags:
            result["prompt"] = word.english + " (Plural)"
            result['answer'] = word.plural
            result['plural'] = True
        else:
            result["prompt"] = word.english
            result['answer'] = word.german  
            result['plural'] = False

        if word.part_of_speech == Part_Of_Speech.Verb:
            result['prompt'] = 'To ' + result['prompt']
    else:
        result["question"] = word.german
        result['answer'] = word.english
        result["prompt"] = word.german
        result['plural'] = False

    return result

def guess_equal(x, y):
    return x.upper().strip() == y.upper().strip()

def show_playtime(p: int) -> str:
    secs = p % 60
    mins = (p // 60) % 60
    hours = (p // 3600)
    if hours == 0 and mins == 0:
        return f"{secs} Seconds"
    elif hours == 0:
        return f"{mins} Minutes and {secs} Seconds"
    else:
        return f"{hours} Hours, {mins} Minutes, and {secs} Seconds"

def get_current_time(p: Progress) -> int:
        today = dt.datetime.today()
        try:
            return p[today.year][int_to_month(today.month)][today.day].time
        except: return 0 #terrible code who cares

def play(title, words, english, plurals, times, stack, voice, always_play):
    safe_div = lambda x, y: 0 if y == 0 else x / y
    shuffle(words)
    plural_lam = (lambda: False) if plurals == 0 else (lambda: True) if plurals == 1 else (lambda: randint(0,1) == 1)
    cards = list(map(lambda x: ask(x, english, plural_lam), words))
    hint = False
    speech = False
    tag_hint = False
    redo = False
    show_time = False
    show_time_all = False
    loop = True
    index = 0
    wins = 0
    losses = 0
    fails = []
    start = dt.datetime.now()
    while loop:
        if index + 1 > len(words): break

        head_txt = ["Playing " + title + f" ({len(words)} words)"
                , f"{str(wins)} out of {str(wins + losses)} words. {(safe_div(wins, wins + losses)*100):.2f}% success rate."]
        if hint: head_txt.append("Hint: " + cards[index]['answer'][0] + "*" * (len(cards[index]['answer']) - 2) + cards[index]['answer'][-1])
        elif speech: head_txt.append("Part of Speech: " + show_speech(words[index].part_of_speech))
        elif tag_hint: 
            random_tag = choice(words[index].tags)
            head_txt.append(f"Has Tag: {random_tag}")
        elif show_time:
            show_time = False 
            now = dt.datetime.now()
            head_txt.append(f"Time Spent: {show_playtime(int((now - start).total_seconds()))}")
        elif show_time_all:
            show_time_all = False
            this = int((dt.datetime.now() - start).total_seconds())
            today = get_current_time(times)
            head_txt.append(f"Time Spent: {show_playtime(this + today)}")

        head = header(term, head_txt)
        head += term.move_y(5) + term.black_on_plum(term.center( cards[index]['prompt']))
        shortcuts = { "`": "Play Audio Hint (Causes Loss)"
                    , "#": "Show First and Last Letter", "@": "Show Part of Speech", "!": "Quit", "?": "Show Answer"
                     , "%": "Show Time Spent", "^": "Show Total Time Spent"}
        if len(words[index].tags) > 0:
            shortcuts["$"] = "Show Tag Hint"
        guess = get_text(term, head, shortcuts=shortcuts)

        if guess == shortcuts["#"]: 
            hint = True
            speech = False
            tag_hint = False
            show_time = False 
            show_time_all = False
            continue
        elif guess == shortcuts["@"]:
            speech = True 
            hint = False
            tag_hint = False
            show_time = False 
            show_time_all = False
            continue
        elif len(words[index].tags) and guess == shortcuts["$"]:
            tag_hint = True
            speech = False
            hint = False
            show_time = False 
            show_time_all = False
            continue
        elif guess == shortcuts["!"]:
            break
        elif guess == shortcuts["?"]:
            if not redo: losses += 1 # we need to do it here because redo ignores losses in the main part
            redo = True
        elif guess == shortcuts["`"]:
            if not redo: losses += 1
            words[index].play_audio(voice)
            redo = True
            continue
        elif guess == shortcuts["%"]:
            show_time = True 
            tag_hint = False
            speech = False
            hint = False
            show_time_all = False
            continue
        elif guess == shortcuts["^"]:
            show_time_all = True
            tag_hint = False
            speech = False
            hint = False
            show_time = False 
            continue

        if guess_equal(guess, cards[index]['answer']):
            print(term.move_y(2) + term.black_on_plum(term.center(f"Nice job with {guess}! Press any key to continue.")))
            if redo: redo = False #exits redo mode
            else: wins += 1
        else:
            print(term.move_y(2) + term.black_on_plum(term.center(f"Unfortunately, it's {cards[index]['answer']}. Press any key to continue.")))
            fails.append({"word": words[index], "plural": cards[index]['plural']})
            if not redo: losses += 1

        words[index].times_played += 1
        hint = False
        speech = False
        tag_hint = False

        if always_play: words[index].play_audio(voice)
        while True:
            with term.cbreak(), term.hidden_cursor():
                key = term.inkey()

            #why is this so dumb, like how do I have technical debt after 1 day of coding
            after_options = {"!": "Quit", "c": "Give win", "r": "Redo last word", "p": "Open forvo pronunciation"
                             , "P": "Show forvo pronunciation link", "o": "Push onto Stack"
                             , "v": "Play Generated Pronunciation", "V": "Stop Playing Pronunciation" if always_play else "Always Play Pronunciation"}
            if words[index].part_of_speech == Part_Of_Speech.Noun: after_options["?"] = "Show noun plural and gender"
            if key == "!":
                loop = False
            elif key == "c":
                wins += 1
                losses -= 1
            elif key == "r":
                redo = True
            elif key == "p":
                wb.open(f"https://forvo.com/search/{words[index].german}/de", new=2)
                continue
            elif key == "P":
                print(term.black_on_plum(term.center(f"https://forvo.com/search/{words[index].german}/de")))
                continue
            elif key == "?":
                if words[index].part_of_speech == Part_Of_Speech.Noun:
                    print(term.black_on_plum(term.center("The plural form is: " + words[index].plural)))
                    print(term.black_on_plum(term.center("The gender is: " + words[index].gender)))
                continue
            elif key == "+":
                for key, value in after_options.items():
                    print(term.black_on_plum1(term.center(f"[{key}]: {value:>30}")))
                continue
            elif key == "o":
                stack.append({"word": words[index], "deck": words[index].deck})
            elif key == "v":
                words[index].play_audio(voice)
                continue
            elif key == "V": 
                always_play = not always_play
                continue

            break

        if not redo: index += 1

    head = [
         "Completed " + title
        , f"{wins + losses} words with a {(safe_div(wins, wins + losses)*100):.2f}% success rate."
    ] 

    print(header(term, head))
    if len(fails) > 0:
        print(term.move_y(5) + term.black_on_plum(term.center("Words to practice:")))
        for x in fails:
            print(term.black_on_plum(term.center(show_translation(x['word'], x['plural']))))
    
    print(term.move_down(2) + term.black_on_plum(term.center("Completed press any key to continue")))
    if (len(fails) > 0): print(term.black_on_plum(term.center("Press [o] to push fails onto stack")))
    with term.cbreak(), term.hidden_cursor():
        key = term.inkey()
    added = []
    if key == "o":
        for item in fails: 
            if item not in added: stack.append({"word": item['word'], "deck": item['word'].deck})
            added.append(item)

    end = dt.datetime.now()
    return int((end - start).total_seconds())


def show_times(times: Progress): 
    year = None 
    month = None 
    loop = True

    selected_index = 0
    shortcuts = {"t": "Show Today", "!": "Go Back"}
    
    while loop:
        if year == None:
            head = header(term, ["Browse Times", "Select Year"])
            options = list(map(str, times.keys())) + ["-------", "Go Back", "Exit"]
        elif month == None:
            head = header(term, ["Browse Times", "Select Year", "Select Month"])
            options = list(map(str, times[int(year)].keys())) + ["-------", "Go Back", "Exit"]
        else: 
            head = header(term, ["Browse Times", "Select Year", "Select Month", "View By Day"])
            options = list(map(str, times[int(year)][month].keys())) 
            options = sorted(options)
            options += ["-------", "Go Back", "Exit"]
        if year == None or month == None: choice = option(options, style=(head + down(term)), shortcuts=shortcuts)    
        else: 
            after = list(map(lambda x: f"{x:>40}", map(show_playtime, map(lambda x: times[int(year)][month][x].time, sorted(times[int(year)][month].keys())))))
            choice = option(options, style=(head + down(term)), after=after, shortcuts=shortcuts, start_index=selected_index)    
        if choice['choice'] == options[-1]: loop = False 
        elif choice['choice'] == options[-2] or choice['choice'] == shortcuts['!']: 
            if month != None: month = None
            elif year != None: year = None
        elif choice['choice'] == shortcuts['t']:
            today = dt.date.today()
            year = str(today.year)
            month = int_to_month(today.month)
            if times[int(year)][month].get(today.day):
                options = list(times[int(year)][month].keys()) 
                options = sorted(options)
                selected_index = options.index(today.day)


        else:
            if year == None: 
                selected_index = 0
                year = options[int(choice['index'])]
            elif month == None: 
                selected_index = 0
                month = options[choice["index"]]
            else: selected_index = choice['index']
            

def start_play(decks, times, stack, voice):
    head = header(term, ["Play"])
    options = list(map(lambda x: x.name , decks))
    after = list(map(lambda x: " | Played " + str(x.times_played) + " times.", decks))
    options += ["Go Back"]
    shortcuts = {} if len(stack) <= 0 else {"j": "Use Stack as Deck"}
    choice = option(options, style=(head + down(term)), after=after)
    always_play = False


    if choice['choice'] == options[-1]:
        return (decks, None)
    else:
        stop = "Continue with current deck"
        exit_ = "Exit" #different than stop, this is for leaving ntirely
        exit_flag = False
        selected_decks = []

        if choice['choice'] == shortcuts.get("j"):
            name = "Stack"
            words = []
            while(stack != []): words.append(stack.pop()["word"])
        else:
            selected_decks = [decks[choice["index"]]]

            sub_choice = None
            name = selected_decks[0].name
            words = []
            words += selected_decks[0].words
            while not exit_flag:
                head = header(term, ["Play", "Build Deck", f"Current Deck: {name} with {len(words)} cards."]) + down(term)
                extra_options = ["-------", exit_, stop]
                choose_output = choose_deck(head, decks, extra_options, pred=lambda x: x.name not in map(lambda y: y.name, selected_decks))
                sub_choice = choose_output["option"]
                new_decks = choose_output["filtered"] #since the filtering will reorder it
                if sub_choice['choice'] == stop: break 
                elif sub_choice['choice'] == exit_: exit_flag = True # i don't want to recurse here because the call stack can't be even more sphagetti
                elif sub_choice["choice"] == "-------": continue
                else:
                    name +=  " + " + new_decks[sub_choice['index']].name
                    words += new_decks[sub_choice['index']].words
                    selected_decks.append(new_decks[sub_choice['index']])

        with_plurals = "Play with plural forms"
        without_plurals = "Play without plural forms"
        some_plurals = "Play with 50% plural forms"
        ten_or_less = False
        plurals = 0
        while not exit_flag:
            head = header(term, ["Play", f"Current Deck: {name} with {len(words)} cards.", "Options"]) + down(term)
            options = [
                some_plurals if plurals == 0 else with_plurals if plurals == 0.5 else without_plurals,  #cycle
                "Play with all words" if ten_or_less else "Play only words played 10 times or less", #bool cycle
                "Stop Playing Voices" if always_play else "Always Play Voices",
                "-------", exit_, stop
            ]

            shortcuts = {"V": "Stop Playing Voices" if always_play else "Always Play Voices"}
            choice = option(options, style=(head + down(term)), shortcuts=shortcuts)

            if choice['choice'] == stop: break 
            elif choice['choice'] == exit_: exit_flag = True # i don't want to recurse here because the call stack can't be even more sphagetti
            elif choice['choice'] == without_plurals: plurals = 0
            elif choice['choice'] == some_plurals: plurals = 0.5
            elif choice['choice'] == with_plurals: plurals = 1
            elif choice['choice'] == options[2]: always_play = not always_play
            elif choice['choice'] == options[1]: ten_or_less = not ten_or_less
            elif choice['choice'] == shortcuts["V"]: always_play = not always_play
        if not exit_flag:
            head = header(term, ["Play", "English or German?"])
            choice = option(["English -> German", "German -> English"], style=(head + down(term)))

            actual_words = list(filter(lambda x: x.times_played <= 10, words)) if ten_or_less else words
            play_time = play(name, actual_words, True if choice['index'] == 0 else False, plurals, times, stack, voice, always_play)
            for item in selected_decks: item.times_played += 1
            return (decks, play_time)
        else:
            return (decks, None)

def save(decks, tags: set[Tag] = None):
    try:
        if decks == None or len(decks) == 0: 
            file = open(DECKS, 'r')
            data = file.read()
            decks = list(map(deserialize, loads(data)))
            for index, deck in enumerate(decks):
                for word in deck.words:
                    word.deck = index
                    #patching tags
                    if "*" in word.german and "trennbar" not in word.tags: word.tags.append("trennbar")
                    if type(word) == Noun and word.plural.lower().replace(" ", "") == "noplural" and "No Plural" not in word.tags: word.tags.append("No Plural")
                    for u in ["ü", "Ü", "ä", "Ä", "ö", "Ö"]:
                        if u in word.german and "Has Umlauts" not in word.tags: 
                            word.tags.append("Has Umlauts")
                            break
                    for tagstr in word.tags:
                        new = Tag(tagstr, 1)
                        found = False
                        for tag in tags:
                            if tag == new: 
                                tag.refs += 1
                                found = True
                        if not found: tags.add(new)
        else:
            dicts = list(map(asdict, decks))
            json_output = dumps(dicts, indent=4)
            file = open(DECKS, 'w')
            file.write(json_output)
    except:
        raising = RuntimeError("Critical Error")
        raising.add_note("Saves folder is not properly configured")
        raise raising
    finally: file.close()
    return decks

def int_to_month(m: int) -> str:
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    if 0 <= m <= 11:
        return months[m - 1]
    else:
        raise ValueError("Input must be an integer between 0 and 11.")
    
def save_time(time: Progress | None, today_time: int | None):
    time = {} if time == None else time
    today_time = 0 if today_time == None else today_time
    try:
        if time == None or len(time) == 0:
            for year in os.listdir(TIMES):
                for month in os.listdir(f"{TIMES}/{year}/"):
                    for day in os.listdir(f"{TIMES}/{year}/{month}/"):
                        file = open(f"{TIMES}/{year}/{month}/{day}", "r")
                        new = PlayTime(int(day.split(".")[0]), int(file.read()))
                        if not time.get(int(year)): time[int(year)] = {}
                        if not time[int(year)].get(month): time[int(year)][month] = {}
                        time[int(year)][month][int(day.split(".")[0])] = new
                        file.close()
        else:

            today = dt.datetime.today()
            if not os.path.exists(f"{TIMES}/{today.year}"):
                os.mkdir(f"{TIMES}/{today.year}")
            if not os.path.exists(f"{TIMES}/{today.year}/{int_to_month(today.month)}"):
                os.mkdir(f"{TIMES}/{today.year}/{int_to_month(today.month)}")
            if not os.path.exists(f"{TIMES}/{today.year}/{int_to_month(today.month)}/{today.day}.txt"):
                file = open(f"{TIMES}/{today.year}/{int_to_month(today.month)}/{today.day}.txt", "w")
                file.close() # to create it
            file = open(f"{TIMES}/{today.year}/{int_to_month(today.month)}/{today.day}.txt", "r+")
            current = file.read()
            new_time = today_time + int(current if current != '' else 0)
            file.seek(0)
            file.write(str(new_time))
            file.truncate()
            file.close()
            if not time.get(int(today.year)): time[int(today.year)] = {}
            if not time[int(today.year)].get(int_to_month(today.month)): time[int(today.year)][int_to_month(today.month)] = {}
            current = time[int(today.year)][int_to_month(today.month)].get(today.day)
            if current == None: time[int(today.year)][int_to_month(today.month)][today.day] = PlayTime(today.day, today_time)
            else: time[int(today.year)][int_to_month(today.month)][today.day].time += today_time
    except:
        raising = RuntimeError("Critical Error")
        raising.add_note("Saves folder is not properly configured")
        raise raising
    finally:
        pass


    return time

init()
menu()

#TODO
#EDIT DECKS - 
    #✅Option menu when clicking on a word
        #Edit Word - just redoes build_word filling defaults with the current data
        #✅Add Tag - Adds a tag to the word (the tags are created elsewhere)
            #✅It would be nice with a basic search algo but for now just sort alphabetically
    #✅(in deck creation but still a menu)Main Menu gets another button for registering a tag
    #store tag metadata in its own file
    #so that the tags can find what the references them
    #thus allowing for playing off of selected tag
    #(Minor) sort decks by most played. Idk how this will work with the ordering of the list, you got it

    #PLAY MVP 
        #✅Select a Deck 
        #✅Select Eng -> Deu or Deu -> Eng
        #✅Show number of cards selecred
        #✅It shows one side of the flashcard, you have to type the other
        #✅ #if you fail, it shows the correct and allows override
            #✅Records data of hits misses and times played
        
    #PLAY FINAL PRODUCT
        #✅Combine decks 
        #Query Cards with deck by Part of Speech, Gender, Plurarity, and Tags
            #These can be hardcoded, so don't go too crazy

    #✅add a "Stack" so you can select a word while playing
    #✅and then jump to it to edit

    #STATS MVP 
        #Show time studied
    #STATS FINAL
        #Show time studied today, the week, the month, and lifetime, with graphs for week and month

    #DREAM - HOOK UP WITH COLLINS API / WEBSCRAPE IT