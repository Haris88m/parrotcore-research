from parrotcore.feetech_protocol import goal_position_packet, ping_packet, read_packet


def test_ping_packet_matches_protocol_example():
    assert ping_packet(1) == bytes.fromhex("FF FF 01 02 01 FB")


def test_read_position_packet_matches_protocol_example():
    assert read_packet(1, 0x38, 2) == bytes.fromhex("FF FF 01 04 02 38 02 BE")


def test_goal_position_packet_matches_protocol_example():
    # Official protocol example: ID 1, position 2048, time 0, speed 1000.
    assert goal_position_packet(1, 2048, 1000, 0) == bytes.fromhex(
        "FF FF 01 09 03 2A 00 08 00 00 E8 03 D5"
    )


def test_goal_position_requires_raw_ticks_not_unbounded_values():
    try:
        goal_position_packet(1, 70000, 1000)
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range tick value must fail")
