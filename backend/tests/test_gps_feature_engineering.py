from datetime import datetime, timedelta, timezone

from backend.app.services.gps_feature_engineering import (
    GpsPoint,
    calculate_gps_features,
)


START = datetime(2026, 8, 18, 9, 0, tzinfo=timezone.utc)


def point(minute: int, lat: float, lng: float) -> GpsPoint:
    return GpsPoint(timestamp=START + timedelta(minutes=minute), lat=lat, lng=lng)


def test_straight_movement_has_no_turn() -> None:
    features = calculate_gps_features(
        [point(0, 37.0, 126.0), point(1, 37.0, 126.001), point(2, 37.0, 126.002)]
    )

    assert features[-1].turn_count == 0


def test_direction_change_below_45_degrees_does_not_add_turn() -> None:
    features = calculate_gps_features(
        [point(0, 37.0, 126.0), point(1, 37.0, 126.001), point(2, 37.0004, 126.002)]
    )

    assert features[-1].turn_count == 0


def test_direction_change_at_least_45_degrees_adds_turn() -> None:
    features = calculate_gps_features(
        [point(0, 37.0, 126.0), point(1, 37.0, 126.001), point(2, 37.001, 126.001)]
    )

    assert features[-1].turn_count == 1


def test_turn_leaves_10_minute_window() -> None:
    points = [point(0, 37.0, 126.0), point(1, 37.0, 126.001), point(2, 37.001, 126.001)]
    points.extend(point(minute, 37.0 + (minute - 1) * 0.001, 126.001) for minute in range(3, 14))

    features = calculate_gps_features(points)

    assert features[12].turn_count == 1
    assert features[13].turn_count == 0


def test_non_crossing_movement_has_no_revisit() -> None:
    features = calculate_gps_features(
        [
            point(0, 37.0, 126.0),
            point(1, 37.0, 126.001),
            point(2, 37.0, 126.002),
            point(3, 37.0, 126.003),
        ]
    )

    assert features[-1].revisit_count == 0


def test_crossing_an_earlier_segment_adds_revisit() -> None:
    features = calculate_gps_features(
        [
            point(0, 37.0, 126.0),
            point(1, 37.0, 126.002),
            point(2, 37.001, 126.002),
            point(3, 37.001, 126.0),
            point(4, 36.999, 126.001),
        ]
    )

    assert features[-1].revisit_count == 1


def test_overlapping_the_previous_segment_adds_revisit() -> None:
    features = calculate_gps_features(
        [
            point(0, 37.0, 126.0),
            point(1, 37.0, 126.002),
            point(2, 37.0, 126.001),
        ]
    )

    assert features[-1].revisit_count == 1


def test_segment_outside_15_minute_window_is_not_a_revisit_candidate() -> None:
    points = [
        point(0, 37.0, 126.0),
        point(1, 37.0, 126.002),
        point(2, 37.001, 126.002),
    ]
    points.extend(point(minute, 37.001, 126.002) for minute in range(3, 17))
    points.append(point(17, 36.999, 126.001))

    features = calculate_gps_features(points)

    assert features[-1].revisit_count == 0
