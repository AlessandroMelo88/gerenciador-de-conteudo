from unittest.mock import MagicMock

import src.related_video as related_video
from src.related_video import (
    append_related_video,
    download_related_thumbnail,
    related_video_from_clip,
)


def test_related_video_prefers_published_video_from_same_destination():
    result = related_video_from_clip(
        {
            'related_video_id': 'published123',
            'related_video_title': 'Como proteger seus dados',
            'source_youtube_video_id': 'source12345',
        }
    )

    assert result == {
        'video_id': 'published123',
        'title': 'Como proteger seus dados',
        'url': 'https://www.youtube.com/watch?v=published123',
        'thumbnail_url': 'https://i.ytimg.com/vi/published123/hqdefault.jpg',
    }


def test_related_video_falls_back_to_source_video():
    result = related_video_from_clip(
        {'source_youtube_video_id': 'source12345', 'source_title': 'Vídeo fonte'}
    )

    assert result['video_id'] == 'source12345'
    assert result['title'] == 'Vídeo fonte'


def test_append_related_video_keeps_link_at_description_end_and_is_idempotent():
    related = related_video_from_clip(
        {'related_video_id': 'published123', 'related_video_title': 'Próximo assunto'}
    )

    result = append_related_video('Descrição principal', related)

    assert result.endswith(
        'Assista também: Próximo assunto\nhttps://www.youtube.com/watch?v=published123'
    )
    assert append_related_video(result, related) == result


def test_download_related_thumbnail_writes_bounded_response(tmp_path, monkeypatch):
    response = MagicMock()
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    response.read.return_value = b'jpeg-bytes'
    opener = MagicMock(return_value=response)
    monkeypatch.setattr(related_video.urllib.request, 'urlopen', opener)

    output_path = tmp_path / 'related.jpg'
    assert download_related_thumbnail('published123', output_path) is True

    assert output_path.read_bytes() == b'jpeg-bytes'
    opener.assert_called_once()
