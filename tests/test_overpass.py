from kosm.overpass import build_military_query


def test_build_military_query_includes_bbox_and_tag_filters():
    query = build_military_query((66.5, -180.0, 90.0, 180.0), timeout=90)

    assert "[timeout:90]" in query
    assert 'node["military"](66.5,-180.0,90.0,180.0);' in query
    assert 'way["military"](66.5,-180.0,90.0,180.0);' in query
    assert 'relation["military"](66.5,-180.0,90.0,180.0);' in query
    assert 'node["landuse"="military"](66.5,-180.0,90.0,180.0);' in query
    assert "out body geom;" in query


def test_build_military_query_uses_given_bbox():
    query = build_military_query((70.0, 10.0, 75.0, 20.0))
    assert "(70.0,10.0,75.0,20.0)" in query
