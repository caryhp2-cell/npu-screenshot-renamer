from npu_screenshot_renamer import app


def test_main_starts_qt_application_and_shows_main_window(monkeypatch):
    events = []

    class FakeApplication:
        def __init__(self, argv):
            events.append(("app", argv))

        def exec(self):
            events.append(("exec", None))
            return 17

    class FakeMainWindow:
        def __init__(self):
            events.append(("window", None))

        def show(self):
            events.append(("show", None))

    monkeypatch.setattr(app, "QApplication", FakeApplication)
    monkeypatch.setattr(app, "MainWindow", FakeMainWindow)
    monkeypatch.setattr(app.sys, "argv", ["renamer"])

    assert app.main() == 17
    assert events == [
        ("app", ["renamer"]),
        ("window", None),
        ("show", None),
        ("exec", None),
    ]
