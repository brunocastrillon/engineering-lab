from calc import media


def test_media_simples():
    assert media([2, 4, 6]) == 4


def test_media_um_elemento():
    assert media([5]) == 5
