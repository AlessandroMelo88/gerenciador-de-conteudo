from src.meme_editor import build_panico_face_bulge_filter, detect_meme_moments


def test_detect_meme_moments_finds_trigger_words():
    segments = [
        {'start': 0.0, 'end': 4.0, 'text': 'Hoje vamos falar sobre programação.'},
        {'start': 4.5, 'end': 8.0, 'text': 'Isso que aconteceu foi bizarro demais!'},
        {'start': 15.0, 'end': 19.0, 'text': 'O sistema quebrou completamente.'},
        {'start': 20.0, 'end': 24.0, 'text': 'Foi uma garotada sem tamanho.'},
    ]
    # Clip de 0 a 30s
    events = detect_meme_moments(segments, 0.0, 30.0, max_effects=2, min_spacing_seconds=5.0)

    assert len(events) == 2
    assert events[0]['keyword'] == 'bizarro'
    assert events[0]['type'] == 'panico_face_bulge'
    assert events[0]['rel_start'] >= 4.0
    assert events[1]['keyword'] == 'quebrou'


def test_detect_meme_moments_empty_transcript():
    events = detect_meme_moments([], 0.0, 30.0)
    assert events == []

    events_none = detect_meme_moments(None, 0.0, 30.0)
    assert events_none == []


def test_detect_meme_moments_short_clip():
    segments = [{'start': 0.0, 'end': 2.0, 'text': 'Absurdo!'}]
    events = detect_meme_moments(segments, 0.0, 2.0)
    assert events == []


def test_build_panico_face_bulge_filter_generates_valid_syntax():
    events = [
        {'rel_start': 4.5, 'rel_end': 6.5, 'keyword': 'bizarro'},
        {'rel_start': 15.0, 'rel_end': 17.0, 'keyword': 'quebrou'},
    ]
    filter_str = build_panico_face_bulge_filter(events)

    assert 'lenscorrection=' in filter_str
    assert 'cx=0.50' in filter_str
    assert 'cy=0.38' in filter_str
    assert 'k1=-0.50' in filter_str
    assert 'between(t,4.50,6.50)+between(t,15.00,17.00)' in filter_str
    assert 'eq=saturation=1.40' in filter_str


def test_build_panico_face_bulge_filter_empty_events():
    assert build_panico_face_bulge_filter([]) == ''
