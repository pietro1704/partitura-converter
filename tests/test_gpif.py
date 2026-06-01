from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from app.gpif import convert_gp_to_musicxml


def write_minimal_gp(path: Path) -> None:
    gpif = '''<?xml version="1.0" encoding="utf-8"?>
<GPIF>
  <Score><Title>Tarkus Tiny</Title><Artist>ELP</Artist></Score>
  <Tracks><Track id="0"><Name>Piano</Name><Staves><Staff/></Staves></Track></Tracks>
  <MasterBars><MasterBar><Key><AccidentalCount>0</AccidentalCount><Mode>Major</Mode></Key><Time>4/4</Time><Bars>0</Bars></MasterBar></MasterBars>
  <Bars><Bar id="0"><Clef>G2</Clef><Voices>0 -1 -1 -1</Voices></Bar></Bars>
  <Voices><Voice id="0"><Beats>0</Beats></Voice></Voices>
  <Beats><Beat id="0"><Rhythm ref="0"/><Notes>0</Notes></Beat></Beats>
  <Notes><Note id="0"><Properties><Property name="ConcertPitch"><Pitch><Step>C</Step><Accidental></Accidental><Octave>4</Octave></Pitch></Property></Properties></Note></Notes>
  <Rhythms><Rhythm id="0"><NoteValue>Whole</NoteValue></Rhythm></Rhythms>
</GPIF>'''
    with ZipFile(path, 'w') as zf:
        zf.writestr('Content/score.gpif', gpif)
        zf.writestr('VERSION', '8')


def test_convert_gp_to_musicxml_creates_valid_importable_shape(tmp_path):
    gp_path = tmp_path / 'tiny.gp'
    out_path = tmp_path / 'tiny.musicxml'
    write_minimal_gp(gp_path)

    result = convert_gp_to_musicxml(gp_path, out_path)

    assert result.title == 'Tarkus Tiny'
    assert result.parts == 1
    assert result.measures == 1
    xml = out_path.read_text()
    assert '<score-partwise version="4.0">' in xml
    assert '<part-name>Piano</part-name>' in xml
    assert '<step>C</step>' in xml
    assert '<octave>4</octave>' in xml
