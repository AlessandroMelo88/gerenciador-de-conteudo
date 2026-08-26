from src.publisher import _prepare_publication_clip


def test_prepare_publication_clip_appends_related_video_without_mutating_input():
    clip = {
        'title': 'Clip atual',
        'description': 'Descrição editorial',
        'related_video_id': 'published123',
        'related_video_title': 'Outro assunto completo',
        'source_youtube_video_id': 'source12345',
    }

    prepared = _prepare_publication_clip(clip)

    assert prepared is not clip
    assert prepared['description'].endswith(
        'Assista também: Outro assunto completo\nhttps://www.youtube.com/watch?v=published123'
    )
    assert clip['description'] == 'Descrição editorial'
