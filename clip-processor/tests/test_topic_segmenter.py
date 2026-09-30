import json
from unittest.mock import MagicMock

import pytest

from src.topic_segmenter import TopicSegmentationError, segment_transcript_topics


def _client_with_topics(topics):
    client = MagicMock()
    client.messages.create.return_value.content = [MagicMock(text=json.dumps({'topics': topics}))]
    return client


def test_segments_are_grouped_chronologically_from_ai_ranges():
    transcript = {
        'text': 'Privacidade dos dados. Criptografia local. Kernel Linux.',
        'segments': [
            {'start': 0.0, 'end': 1.5, 'text': 'Privacidade dos dados'},
            {'start': 1.5, 'end': 3.0, 'text': 'Criptografia local'},
            {'start': 3.0, 'end': 4.0, 'text': 'Kernel Linux'},
        ],
    }
    client = _client_with_topics(
        [
            {'start_segment_index': 0, 'end_segment_index': 1, 'title': 'Privacidade'},
            {'start_segment_index': 2, 'end_segment_index': 2, 'title': 'Linux'},
        ]
    )

    topics = segment_transcript_topics(transcript, ai_client=client)

    assert topics == [
        {
            'position': 1,
            'title': 'Privacidade',
            'start_seconds': 0.0,
            'end_seconds': 3.0,
            'first_segment_index': 0,
            'last_segment_index': 1,
            'transcript_text': 'Privacidade dos dados Criptografia local',
        },
        {
            'position': 2,
            'title': 'Linux',
            'start_seconds': 3.0,
            'end_seconds': 4.0,
            'first_segment_index': 2,
            'last_segment_index': 2,
            'transcript_text': 'Kernel Linux',
        },
    ]


def test_segmenter_rejects_ranges_with_gaps():
    transcript = {
        'text': 'Uma fala completa.',
        'segments': [
            {'start': 0.0, 'end': 1.0, 'text': 'Uma fala'},
            {'start': 1.0, 'end': 2.0, 'text': 'completa'},
        ],
    }
    client = _client_with_topics(
        [{'start_segment_index': 0, 'end_segment_index': 0, 'title': 'Assunto'}]
    )

    with pytest.raises(TopicSegmentationError, match='lacunas'):
        segment_transcript_topics(transcript, ai_client=client)
