"""Compute rolling movement features from ordered synthetic GPS points."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import atan2, cos, degrees, isfinite, radians, sin
from typing import Sequence


TURN_THRESHOLD_DEGREES = 45.0
TURN_WINDOW = timedelta(minutes=10)
REVISIT_WINDOW = timedelta(minutes=15)
_GEOMETRY_EPSILON = 1e-12


@dataclass(frozen=True)
class GpsPoint:
    timestamp: datetime
    lat: float
    lng: float


@dataclass(frozen=True)
class GpsFeatures:
    turn_count: int
    revisit_count: int

    def as_dict(self) -> dict[str, int]:
        return {
            "turn_count": self.turn_count,
            "revisit_count": self.revisit_count,
        }


@dataclass(frozen=True)
class _MovementSegment:
    start: GpsPoint
    end: GpsPoint
    bearing: float


def _validate_points(points: Sequence[GpsPoint]) -> None:
    previous_timestamp: datetime | None = None
    for point in points:
        if point.timestamp.tzinfo is None or point.timestamp.utcoffset() is None:
            raise ValueError("GPS timestamps must include a timezone")
        if previous_timestamp is not None and point.timestamp <= previous_timestamp:
            raise ValueError("GPS points must be in strictly increasing timestamp order")
        if not isfinite(point.lat) or not -90 <= point.lat <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not isfinite(point.lng) or not -180 <= point.lng <= 180:
            raise ValueError("longitude must be between -180 and 180")
        previous_timestamp = point.timestamp


def _bearing(start: GpsPoint, end: GpsPoint) -> float | None:
    if start.lat == end.lat and start.lng == end.lng:
        return None

    start_lat = radians(start.lat)
    end_lat = radians(end.lat)
    longitude_delta = radians(end.lng - start.lng)
    y = sin(longitude_delta) * cos(end_lat)
    x = cos(start_lat) * sin(end_lat) - sin(start_lat) * cos(end_lat) * cos(longitude_delta)
    return (degrees(atan2(y, x)) + 360.0) % 360.0


def _direction_change(first: float, second: float) -> float:
    difference = abs(second - first) % 360.0
    return min(difference, 360.0 - difference)


def _cross(
    first: tuple[float, float],
    second: tuple[float, float],
    third: tuple[float, float],
) -> float:
    return (second[0] - first[0]) * (third[1] - first[1]) - (
        second[1] - first[1]
    ) * (third[0] - first[0])


def _on_segment(
    start: tuple[float, float],
    point: tuple[float, float],
    end: tuple[float, float],
) -> bool:
    return (
        min(start[0], end[0]) - _GEOMETRY_EPSILON
        <= point[0]
        <= max(start[0], end[0]) + _GEOMETRY_EPSILON
        and min(start[1], end[1]) - _GEOMETRY_EPSILON
        <= point[1]
        <= max(start[1], end[1]) + _GEOMETRY_EPSILON
    )


def _segments_intersect(first: _MovementSegment, second: _MovementSegment) -> bool:
    first_start = (first.start.lng, first.start.lat)
    first_end = (first.end.lng, first.end.lat)
    second_start = (second.start.lng, second.start.lat)
    second_end = (second.end.lng, second.end.lat)

    orientations = (
        _cross(first_start, first_end, second_start),
        _cross(first_start, first_end, second_end),
        _cross(second_start, second_end, first_start),
        _cross(second_start, second_end, first_end),
    )
    first_side, second_side, third_side, fourth_side = orientations

    if (
        ((first_side > _GEOMETRY_EPSILON and second_side < -_GEOMETRY_EPSILON)
         or (first_side < -_GEOMETRY_EPSILON and second_side > _GEOMETRY_EPSILON))
        and ((third_side > _GEOMETRY_EPSILON and fourth_side < -_GEOMETRY_EPSILON)
             or (third_side < -_GEOMETRY_EPSILON and fourth_side > _GEOMETRY_EPSILON))
    ):
        return True

    return (
        (abs(first_side) <= _GEOMETRY_EPSILON and _on_segment(first_start, second_start, first_end))
        or (abs(second_side) <= _GEOMETRY_EPSILON and _on_segment(first_start, second_end, first_end))
        or (abs(third_side) <= _GEOMETRY_EPSILON and _on_segment(second_start, first_start, second_end))
        or (abs(fourth_side) <= _GEOMETRY_EPSILON and _on_segment(second_start, first_end, second_end))
    )


def _segments_overlap_beyond_shared_endpoint(
    first: _MovementSegment,
    second: _MovementSegment,
) -> bool:
    """Distinguish backtracking overlap from an adjacent shared endpoint."""

    first_start = (first.start.lng, first.start.lat)
    first_end = (first.end.lng, first.end.lat)
    second_start = (second.start.lng, second.start.lat)
    second_end = (second.end.lng, second.end.lat)
    if (
        abs(_cross(first_start, first_end, second_start)) > _GEOMETRY_EPSILON
        or abs(_cross(first_start, first_end, second_end)) > _GEOMETRY_EPSILON
    ):
        return False

    longitude_span = abs(first_end[0] - first_start[0])
    latitude_span = abs(first_end[1] - first_start[1])
    axis = 0 if longitude_span >= latitude_span else 1
    overlap = min(
        max(first_start[axis], first_end[axis]),
        max(second_start[axis], second_end[axis]),
    ) - max(
        min(first_start[axis], first_end[axis]),
        min(second_start[axis], second_end[axis]),
    )
    return overlap > _GEOMETRY_EPSILON


def calculate_gps_features(points: Sequence[GpsPoint]) -> list[GpsFeatures]:
    """Return rolling turn/revisit counts for each ordered GPS point."""

    _validate_points(points)
    if not points:
        return []

    results = [GpsFeatures(turn_count=0, revisit_count=0)]
    segments: list[_MovementSegment] = []
    turn_events: list[datetime] = []
    revisit_events: list[datetime] = []

    for index in range(1, len(points)):
        current_time = points[index].timestamp
        bearing = _bearing(points[index - 1], points[index])

        turn_cutoff = current_time - TURN_WINDOW
        revisit_cutoff = current_time - REVISIT_WINDOW
        turn_events = [event for event in turn_events if event >= turn_cutoff]
        revisit_events = [event for event in revisit_events if event >= revisit_cutoff]

        if bearing is not None:
            current_segment = _MovementSegment(points[index - 1], points[index], bearing)

            if segments and _direction_change(segments[-1].bearing, bearing) >= TURN_THRESHOLD_DEGREES:
                turn_events.append(current_time)

            recent_segments = [
                segment
                for segment in segments
                if segment.end.timestamp >= revisit_cutoff
            ]
            if any(
                _segments_overlap_beyond_shared_endpoint(segment, current_segment)
                if segment is recent_segments[-1]
                else _segments_intersect(segment, current_segment)
                for segment in recent_segments
            ):
                revisit_events.append(current_time)

            segments.append(current_segment)
            segments = [segment for segment in segments if segment.end.timestamp >= revisit_cutoff]

        results.append(
            GpsFeatures(
                turn_count=len(turn_events),
                revisit_count=len(revisit_events),
            )
        )

    return results
