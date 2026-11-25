import csv
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.scripts.prepare_douban_reviews import (
    Translations,
    prepare_records,
    translate_batch,
    write_output,
)


def test_prepares_only_rated_reviews_and_tracks_unmatched_movies(tmp_path):
    source = tmp_path / "source.csv"
    mapping = tmp_path / "mapping.json"
    catalog = tmp_path / "catalog.csv"
    fields = ["状态", "豆瓣条目ID", "星级", "短评", "片名", "原名/别名", "豆瓣链接", "标记日期"]
    original = "演得真好。\n第二遍看还是很喜欢。"
    with source.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(fields)
        for movie_id, rating, review in (
            ("1", "4", original), ("2", "5", "Great."), ("3", "3", " "),
            ("4", "", ""), ("5", "6", original),
        ):
            writer.writerow(["看过", movie_id, rating, review, "片名", "", "", "2020-01-01"])
    mapping.write_text('[{"dbid": 1, "imdbid": "tt123"}]', encoding="utf-8")
    catalog.write_text("id,imdb_id\n99,tt123\n", encoding="utf-8")

    records = prepare_records(source, mapping, catalog)
    assert [row["record_id"] for row in records] == ["1", "2"]
    assert records[0]["movie_id"] == "99"
    assert records[0]["rating"] == 4
    assert records[0]["review_original"] == original
    assert records[0]["translation_status"] == "pending"
    assert records[1]["match_status"] == "missing_imdb_id"
    assert records[1]["translation_status"] == "not_needed"
    output = tmp_path / "output.json"
    write_output(output, "test-model", records)
    assert json.loads(output.read_text(encoding="utf-8"))["records"] == records


def test_translations_are_paired_by_id_and_reject_missing_ids():
    client = Mock()
    rows = [{"record_id": "1", "review_original": "很棒"}, {"record_id": "2", "review_original": "好看"}]
    translation = [{"record_id": "2", "review_en": "A good watch."}, {"record_id": "1", "review_en": "Great."}]
    client.responses.parse.return_value = SimpleNamespace(
        output_parsed=Translations(translations=translation),
    )
    assert translate_batch(client, "test-model", rows) == {"1": "Great.", "2": "A good watch."}
    assert client.responses.parse.call_args.kwargs["store"] is False
    client.responses.parse.return_value = SimpleNamespace(
        output_parsed=Translations(translations=translation[:1]),
    )
    with pytest.raises(ValueError, match="record IDs"):
        translate_batch(client, "test-model", rows)
