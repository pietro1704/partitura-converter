from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

DIVISIONS = 960
NOTE_DURATIONS = {
    "Whole": 4 * DIVISIONS,
    "Half": 2 * DIVISIONS,
    "Quarter": DIVISIONS,
    "Eighth": DIVISIONS // 2,
    "16th": DIVISIONS // 4,
    "32nd": DIVISIONS // 8,
    "64th": DIVISIONS // 16,
}
NOTE_TYPES = {
    "Whole": "whole",
    "Half": "half",
    "Quarter": "quarter",
    "Eighth": "eighth",
    "16th": "16th",
    "32nd": "32nd",
    "64th": "64th",
}
ALTERS = {"#": 1, "b": -1, "x": 2, "bb": -2}


@dataclass(frozen=True)
class GPIFConversionResult:
    title: str
    parts: int
    measures: int
    output_file: str


def text(el: ET.Element | None, default: str = "") -> str:
    if el is None or el.text is None:
        return default
    return el.text.strip()


def ids(value: str | None) -> list[str]:
    if not value:
        return []
    return [item for item in value.split() if item != "-1"]


def load_gpif(gp_path: Path) -> ET.Element:
    with ZipFile(gp_path) as zf:
        with zf.open("Content/score.gpif") as handle:
            return ET.parse(handle).getroot()


def note_duration(rhythm: ET.Element | None) -> tuple[int, str, int]:
    value = text(rhythm.find("NoteValue") if rhythm is not None else None, "Quarter")
    duration = NOTE_DURATIONS.get(value, DIVISIONS)
    note_type = NOTE_TYPES.get(value, "quarter")
    dots_el = rhythm.find("AugmentationDot") if rhythm is not None else None
    dots = int(dots_el.attrib.get("count", "0")) if dots_el is not None else 0
    extra = duration
    for _ in range(dots):
        extra //= 2
        duration += extra
    return duration, note_type, dots


def note_pitch(note: ET.Element) -> tuple[str, int | None, str]:
    pitch = note.find("./Properties/Property[@name='ConcertPitch']/Pitch")
    if pitch is None:
        pitch = note.find("./Properties/Property[@name='TransposedPitch']/Pitch")
    if pitch is None:
        midi = int(text(note.find("./Properties/Property[@name='Midi']/Number"), "60"))
        steps = ["C", "C", "D", "D", "E", "F", "F", "G", "G", "A", "A", "B"]
        alters = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0]
        return steps[midi % 12], alters[midi % 12] or None, str(midi // 12 - 1)
    step = text(pitch.find("Step"), "C")
    accidental = text(pitch.find("Accidental"))
    octave = text(pitch.find("Octave"), "4")
    return step, ALTERS.get(accidental), octave


def child(parent: ET.Element, tag: str, content: str | None = None, **attrs: str) -> ET.Element:
    el = ET.SubElement(parent, tag, attrs)
    if content is not None:
        el.text = str(content)
    return el


def add_note(parent: ET.Element, note: ET.Element | None, duration: int, note_type: str, dots: int, chord: bool = False) -> None:
    n = child(parent, "note")
    if chord:
        child(n, "chord")
    if note is None:
        child(n, "rest")
    else:
        step, alter, octave = note_pitch(note)
        pitch = child(n, "pitch")
        child(pitch, "step", step)
        if alter is not None:
            child(pitch, "alter", str(alter))
        child(pitch, "octave", octave)
    child(n, "duration", str(duration))
    child(n, "type", note_type)
    for _ in range(dots):
        child(n, "dot")


def convert_gp_to_musicxml(gp_path: Path, output_path: Path) -> GPIFConversionResult:
    root = load_gpif(gp_path)
    title = text(root.find("Score/Title"), gp_path.stem)
    tracks = root.findall("Tracks/Track")
    master_bars = root.findall("MasterBars/MasterBar")
    bars = {bar.attrib["id"]: bar for bar in root.findall("Bars/Bar")}
    voices = {voice.attrib["id"]: voice for voice in root.findall("Voices/Voice")}
    beats = {beat.attrib["id"]: beat for beat in root.findall("Beats/Beat")}
    notes = {note.attrib["id"]: note for note in root.findall("Notes/Note")}
    rhythms = {rhythm.attrib["id"]: rhythm for rhythm in root.findall("Rhythms/Rhythm")}

    first_bars = ids(text(master_bars[0].find("Bars"))) if master_bars else []
    part_count = len(first_bars) or max(1, len(tracks))
    track_names: list[str] = []
    for track in tracks:
        name = text(track.find("Name"), "Part")
        staff_count = max(1, len(track.findall("Staves/Staff")))
        for staff_index in range(staff_count):
            suffix = f" staff {staff_index + 1}" if staff_count > 1 else ""
            track_names.append(f"{name}{suffix}")
    while len(track_names) < part_count:
        track_names.append(f"Part {len(track_names) + 1}")

    score = ET.Element("score-partwise", {"version": "4.0"})
    movement = child(score, "movement-title", title)
    part_list = child(score, "part-list")
    for index in range(part_count):
        score_part = child(part_list, "score-part", id=f"P{index + 1}")
        child(score_part, "part-name", track_names[index])

    for part_index in range(part_count):
        part = child(score, "part", id=f"P{part_index + 1}")
        for measure_index, master_bar in enumerate(master_bars, start=1):
            measure = child(part, "measure", number=str(measure_index))
            if measure_index == 1:
                attrs = child(measure, "attributes")
                child(attrs, "divisions", str(DIVISIONS))
                key = child(attrs, "key")
                child(key, "fifths", text(master_bar.find("Key/AccidentalCount"), "0"))
                time_value = text(master_bar.find("Time"), "4/4")
                beats_value, beat_type = (time_value.split("/", 1) + ["4"])[:2]
                time = child(attrs, "time")
                child(time, "beats", beats_value)
                child(time, "beat-type", beat_type)
                clef = child(attrs, "clef")
                child(clef, "sign", "G")
                child(clef, "line", "2")
            bar_ids = ids(text(master_bar.find("Bars")))
            bar = bars.get(bar_ids[part_index]) if part_index < len(bar_ids) else None
            voice_ids = ids(text(bar.find("Voices")) if bar is not None else "")
            wrote = False
            for voice_id in voice_ids[:1]:
                voice = voices.get(voice_id)
                for beat_id in ids(text(voice.find("Beats")) if voice is not None else ""):
                    beat = beats.get(beat_id)
                    if beat is None:
                        continue
                    rhythm = rhythms.get(beat.find("Rhythm").attrib.get("ref")) if beat.find("Rhythm") is not None else None
                    duration, note_type, dots = note_duration(rhythm)
                    note_ids = ids(text(beat.find("Notes")))
                    if not note_ids:
                        add_note(measure, None, duration, note_type, dots)
                    else:
                        for offset, note_id in enumerate(note_ids):
                            add_note(measure, notes.get(note_id), duration, note_type, dots, chord=offset > 0)
                    wrote = True
            if not wrote:
                add_note(measure, None, 4 * DIVISIONS, "whole", 0)

    ET.indent(score, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(score).write(output_path, encoding="utf-8", xml_declaration=True)
    return GPIFConversionResult(title=title, parts=part_count, measures=len(master_bars), output_file=str(output_path))
