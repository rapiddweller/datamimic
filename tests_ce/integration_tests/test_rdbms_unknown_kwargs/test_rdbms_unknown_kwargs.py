from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def test_unknown_connection_knobs_do_not_reach_create_engine(project_dir):
    engine = DataMimicTest(test_dir=project_dir, filename="unknown_kwarg.xml", capture_test_result=True)
    engine.test_with_timer()  # must not raise "Invalid argument(s) 'clean' sent to create_engine"
    assert engine.capture_result()["g"][0]["v"] == 5
