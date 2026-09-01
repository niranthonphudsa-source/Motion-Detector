from esp32_ng_controller import NGThresholdController


def test_threshold_triggers_once_when_count_reaches_limit():
    triggered = []
    controller = NGThresholdController(threshold=10, on_trigger=lambda: triggered.append("triggered"))

    for _ in range(9):
        controller.register_ng()
        assert controller.is_triggered is False

    controller.register_ng()
    assert controller.is_triggered is True
    assert len(triggered) == 1

    controller.register_ng()
    assert len(triggered) == 1


def test_threshold_can_be_updated():
    controller = NGThresholdController(threshold=3)
    controller.register_ng()
    controller.register_ng()
    assert controller.is_triggered is False

    controller.set_threshold(2)
    controller.register_ng()
    assert controller.is_triggered is True
