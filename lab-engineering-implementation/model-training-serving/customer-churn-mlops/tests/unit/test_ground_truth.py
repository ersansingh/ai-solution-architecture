import json

from ground_truth import ground_truth_lines


def test_ground_truth_uses_inference_id_and_skips_unlabelled():
    capture = [
        json.dumps({"eventMetadata": {"eventId": "e1", "inferenceId": "100:20260712"}}),
        json.dumps({"eventMetadata": {"eventId": "e2", "inferenceId": "200:20260712"}}),
        json.dumps({"eventMetadata": {"eventId": "e3"}}),
        "",
    ]
    lines = [json.loads(x) for x in ground_truth_lines(capture, {"100": 1})]
    assert lines == [{"groundTruthData": {"data": "1", "encoding": "CSV"},
                      "eventMetadata": {"eventId": "100:20260712"}, "eventVersion": "0"}]
