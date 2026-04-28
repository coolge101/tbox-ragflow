import tbox_pipelines


def test_version_defined() -> None:
    assert hasattr(tbox_pipelines, "__version__")
    assert isinstance(tbox_pipelines.__version__, str)
