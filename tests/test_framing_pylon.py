from protocols.pylon_lv_rs485 import PylonLvProfile


def test_split_frames():
    p = PylonLvProfile()
    data = b"noise~20024600800800000000FC22\r~20024600D01270805460064006A4C0F9E5\r"
    frames = p.split_frames(data)
    assert len(frames) == 2
    assert frames[0].startswith(b"~200246")
