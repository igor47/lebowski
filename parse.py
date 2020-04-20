
from collections import defaultdict
from typing import Optional

script = open('script.txt', 'r').readlines()
script = [l[15:] for l in script]

state = "scene"
curscene = {'name': None, 'people': set()}

scenes = []

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
    new_scene = {'name': line.strip().lower(), 'people': set()}
    curscene = new_scene
    scenes.append(curscene)
    cur_person = None

  person = new_person(idx, line)
  if person:
    cur_person = person
    curscene['people'].add(person)

  if is_blank(line):
    cur_person = None

  if cur_person and not person:
    lines[cur_person].append(line)


all_chars = set()
for s in scenes:
  all_chars = all_chars.union(s['people'])

in_scene_with = {char: set() for char in all_chars}
for s in scenes:
  for person in s['people']:
    in_scene_with[person] = in_scene_with[person].union(s['people'])

not_in_scene_with = {char: all_chars.difference(in_scene_with[char]) for char in all_chars}

counts = {p: len(l) for p, l in lines.items()}
counts = sorted(counts.items(), key = lambda x: x[1], reverse=True)

for c in counts:
  print(f"{c[0]}:{c[1]}")
