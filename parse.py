import json
from collections import defaultdict
from itertools import combinations
import sys
from tabulate import tabulate
from typing import Optional

script = open('script.txt', 'r').readlines()
script = [f"{l[15:].rstrip()}\n" for l in script]

state = "scene"
curscene = {'name': None, 'people': set(), 'lines': []}
curscene_num = 0

scenes = []

first_appearances = {}
last_appearances = {}

def is_all_caps(line: str) -> bool:
  return line.upper() == line

def is_blank(line: str) -> bool:
  return len(line.strip()) == 0

SCENE_MARKERS = ['INT.', 'EXT.', 'INSIDE -', 'THE DOOR -']
def starts_with_scene_marker(line: str) -> bool:
  return any(line.startswith(scene_marker) for scene_marker in SCENE_MARKERS)

def scene_change(idx, line) -> bool:
  prev = script[idx-1]

  try:
    next_ = script[idx+1]
  except IndexError:
    next_ = ''

  return is_blank(prev) and is_blank(next_) and is_all_caps(line) and starts_with_scene_marker(line)

def is_script_line(line) -> bool:
  left_side = line[0:36]
  return not is_blank(left_side)

def new_person(idx, line) -> Optional[str]:
  if is_blank(line):
    return None

  prevline = script[idx-1]
  try:
    nextline = script[idx+1]
  except IndexError:
    nextline = ''

  if is_blank(prevline) and is_all_caps(line) and line[0] == ' ' and is_script_line(nextline):
    person = line.strip()
    person = person.split('(')[0].strip()
    return person.lower()

  else:
    return None

cur_person = ''
lines = defaultdict(list)

for idx, line in enumerate(script):
  if scene_change(idx, line):
    curscene_num += 1
    new_scene = {'name': line.strip().lower(), 'people': set(), 'lines': []}
    curscene = new_scene
    scenes.append(curscene)
    cur_person = None

  person = new_person(idx, line)
  if person:
    cur_person = person
    curscene['people'].add(person)
    if person not in first_appearances:
        first_appearances[person] = curscene_num
    last_appearances[person] = curscene_num

  if is_blank(line):
    cur_person = None

  if cur_person and not person:
    lines[cur_person].append(line)

  curscene['lines'].append(line)


all_chars = set()
for s in scenes:
  all_chars = all_chars.union(s['people'])

in_scene_with = {char: set() for char in all_chars}
for s in scenes:
  for person in s['people']:
    in_scene_with[person] = in_scene_with[person].union(s['people'])

def is_in_scene_with(char1, char2) -> bool:
    return char1 in in_scene_with[char2]

not_in_scene_with = {char: all_chars.difference(in_scene_with[char]) for char in all_chars}

counts = {p: len(l) for p, l in lines.items()}
counts_sorted = sorted(counts.items(), key = lambda x: x[1], reverse=True)
print("LINE COUNTS")
print("")
print(tabulate(counts_sorted, headers=["Character", "# Lines"]))
print("")

casting = {}
casting_file = sys.argv[1]
if casting_file:
    with open(casting_file, 'r') as f:
        casting = json.loads(f.read())

roles = defaultdict(list)
for character, actor in casting.items():
    if actor is None:
        continue

    roles[actor].append(character)

print('CURRENT CASTING')
print('')
table = []
for actor, characters in sorted(roles.items(), key = lambda x: x[0]):
    characters = sorted(characters, key=lambda c: counts[c], reverse=True)
    character_list = "\n".join(characters)

    num_characters = len(characters)
    num_lines = sum(counts[c] for c in characters)
    first_appearance = min(first_appearances[c] for c in characters)
    last_appearance = max(last_appearances[c] for c in characters)

    table.append([actor, character_list, num_characters, num_lines, first_appearance, last_appearance])
print(tabulate(sorted(table, key=lambda x: [x[3], x[2]], reverse=True), headers=["Actor", "Characters", "# Parts", "# Lines", "1st Appearance", "Last"]))
print('')

uncast = []
for character, num_lines in sorted(counts.items(), key = lambda x: x[1], reverse=True):
    if casting[character] is None:
        uncast.append([character, num_lines])
uncast_sorted = sorted(uncast, key=lambda x: x[1], reverse=True)
if len(uncast_sorted) > 0:
    print('UNCAST ROLES')
    print('')
    print(tabulate(uncast_sorted, headers=['Character', '# Lines']))
    print('')
else:
    print('ALL ROLES CAST, GOOD JOB')

conflicts = []
for actor, characters in roles.items():
    pairs = combinations(characters, r=2)
    for c1, c2 in pairs:
        if is_in_scene_with(c1, c2):
            conflicts.append([actor, c1, c2])
if len(conflicts) > 0:
    print('CONFLICTS')
    print('')
    print(tabulate(conflicts, headers=['Actor', 'Character 1', 'Character 2']))
else:
    print('NO CONFLICTING CASTING, GOOD JOB')

with open('script-with-casting.txt', 'w') as f:
    for idx, scene in enumerate(scenes):
        num = idx + 1
        name = scene['name'].upper()
        characters_str = ", ".join(character.title() for character in scene['people'])
        actors_str = ", ".join(casting[c].title() for c in scene['people'])
        f.write(f"============================================================================\n")
        f.write("\n")
        f.write(f"SCENE {num}: {name}\n")
        f.write("\n")
        f.write(f"============================================================================\n")
        f.write("\n")
        if len(actors_str) > 0:
            f.write(f"Actors: {actors_str}\n")
            f.write(f"Characters: {characters_str}\n")
            f.write("\n")
            f.write(f"============================================================================\n")
        f.write(f"\n")
        for line in scene['lines']:
            if len(line) > 1:
                f.write("               ")
            f.write(line)
