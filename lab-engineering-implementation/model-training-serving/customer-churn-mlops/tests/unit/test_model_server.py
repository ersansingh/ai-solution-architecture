import csv

from fastapi.testclient import TestClient

from server import create_app


def test_local_run_meets_gates_and_server_scores_raw_rows(trained):
    work, summary = trained
    assert summary["metrics"]["auc"] > 0.9
    app = create_app(str(work / "model"))
    rows = list(csv.reader(open(work / "processed" / "test_raw" / "test_raw.csv")))[1:21]
    body = "\n".join(",".join(r[1:-1]) for r in rows)
    with TestClient(app) as c:
        assert c.get("/ping").status_code == 200
        response = c.post("/invocations", content=body, headers={"Content-Type": "text/csv"})
    probs = [float(x) for x in response.text.split()]
    assert response.status_code == 200 and len(probs) == 20 and all(0 <= p <= 1 for p in probs)


def test_wrong_column_count_is_400(trained):
    work, _ = trained
    with TestClient(create_app(str(work / "model"))) as c:
        assert c.post("/invocations", content="1,2,3", headers={"Content-Type": "text/csv"}).status_code == 400
