import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pin_the_tail.location import Point, Region

coordinate_strategy = st.floats(min_value=0, max_value=32_000)
point_tuple_strategy = st.tuples(coordinate_strategy, coordinate_strategy)


class TestPoint:
    @staticmethod
    def test_point_from_tuple():
        point = Point.from_tuple((13, 11))

        assert point == Point(13, 11)

    @staticmethod
    def test_distance_to_same_point_is_zero():
        point = Point(13, 11)

        distance = point.distance_to(point)

        assert distance == 0

    @staticmethod
    def test_distance_to_point_with_same_y():
        point1 = Point(13, 11)
        point2 = Point(100, 11)

        distance = point1.distance_to(point2)

        assert distance == math.sqrt((100 - 13) ** 2)

    @staticmethod
    def test_distance_to_point_with_same_x():
        point1 = Point(13, 11)
        point2 = Point(13, 100)

        distance = point1.distance_to(point2)

        assert distance == math.sqrt((100 - 11) ** 2)

    @staticmethod
    @given(point_tuple_strategy, point_tuple_strategy)
    def test_distance_between_points(point1_tuple, point2_tuple):
        point1 = Point.from_tuple(point1_tuple)
        point2 = Point.from_tuple(point2_tuple)

        distance = point1.distance_to(point2)
        distance_reverse = point2.distance_to(point1)

        assert distance == distance_reverse
        assert distance >= 0
        assert distance == pytest.approx(math.dist(point1_tuple, point2_tuple))


class TestRegion:
    @staticmethod
    def test_point_contained_within_region():
        point = Point(2, 2)
        region = Region.from_coordinates(0, 0, 10, 10)
        assert region.contains(point)

    @staticmethod
    def test_point_not_contained_within_region():
        point = Point(20, 20)
        region = Region.from_coordinates(0, 0, 10, 10)
        assert not region.contains(point)

    @staticmethod
    @pytest.mark.parametrize(
        "point",
        [
            Point(0, 0),
            Point(0, 10),
            Point(10, 10),
            Point(10, 0),
            Point(0, 3),
            Point(10, 3),
            Point(3, 0),
            Point(3, 10),
        ],
    )
    def test_point_on_border_contained_within_region(point):
        region = Region.from_coordinates(0, 0, 10, 10)
        assert region.contains(point)

    @staticmethod
    @pytest.mark.parametrize("overlap", ["any", "all"])
    def test_inner_region_contained_within_outer_region(overlap):
        inner_region = Region.from_coordinates(1, 1, 5, 5)
        outer_region = Region.from_coordinates(0, 0, 10, 10)

        assert outer_region.contains(inner_region, overlap=overlap)

    @staticmethod
    @pytest.mark.parametrize("overlap", ["any", "all"])
    def test_no_overlap_in_regions(overlap):
        region1 = Region.from_coordinates(30, 30, 50, 50)
        region2 = Region.from_coordinates(0, 0, 10, 10)

        assert not region2.contains(region1, overlap=overlap)

    @staticmethod
    @pytest.mark.parametrize(
        "contained_region",
        [
            # Just the corner kisses the container's region
            Region.from_points(Point(0, 0), Point(20, 30)),
            Region.from_points(Point(0, 50), Point(20, 60)),
            Region.from_points(Point(0, 50), Point(40, 60)),
            Region.from_points(Point(40, 0), Point(60, 30)),
            # At least one corner contained within edge of container region (rest of contained outside of container)
            # Top Edge
            Region.from_points(Point(0, 0), Point(35, 30)),
            Region.from_points(Point(25, 0), Point(35, 30)),
            Region.from_points(Point(25, 0), Point(60, 30)),
            Region.from_points(Point(0, 0), Point(60, 30)),
            # Left Edge
            Region.from_points(Point(0, 35), Point(20, 60)),
            Region.from_points(Point(0, 0), Point(20, 45)),
            Region.from_points(Point(0, 35), Point(20, 45)),
            Region.from_points(Point(0, 0), Point(20, 60)),
            # Bottom Edge
            Region.from_points(Point(0, 50), Point(35, 60)),
            Region.from_points(Point(25, 50), Point(35, 60)),
            Region.from_points(Point(25, 50), Point(60, 60)),
            Region.from_points(Point(0, 50), Point(60, 60)),
            # Right Edge
            Region.from_points(Point(40, 35), Point(60, 60)),
            Region.from_points(Point(40, 0), Point(60, 45)),
            Region.from_points(Point(40, 35), Point(60, 45)),
            Region.from_points(Point(40, 0), Point(60, 60)),
        ],
    )
    def test_partial_overlap_in_regions_is_contained_when_overlap_is_any(contained_region):
        container_region = Region.from_points(Point(20, 30), Point(40, 50))
        assert container_region.contains(contained_region, overlap="any")

    @staticmethod
    @pytest.mark.parametrize(
        "contained_region",
        [
            # Just the corner kisses the container's region
            Region.from_points(Point(0, 0), Point(20, 30)),
            Region.from_points(Point(0, 50), Point(20, 60)),
            Region.from_points(Point(0, 50), Point(40, 60)),
            Region.from_points(Point(40, 0), Point(60, 30)),
            # At least one corner contained within edge of container region (rest of contained outside of container)
            # Top Edge
            Region.from_points(Point(0, 0), Point(35, 30)),
            Region.from_points(Point(25, 0), Point(35, 30)),
            Region.from_points(Point(25, 0), Point(60, 30)),
            Region.from_points(Point(0, 0), Point(60, 30)),
            # Left Edge
            Region.from_points(Point(0, 35), Point(20, 60)),
            Region.from_points(Point(0, 0), Point(20, 45)),
            Region.from_points(Point(0, 35), Point(20, 45)),
            Region.from_points(Point(0, 0), Point(20, 60)),
            # Bottom Edge
            Region.from_points(Point(0, 50), Point(35, 60)),
            Region.from_points(Point(25, 50), Point(35, 60)),
            Region.from_points(Point(25, 50), Point(60, 60)),
            Region.from_points(Point(0, 50), Point(60, 60)),
            # Right Edge
            Region.from_points(Point(40, 35), Point(60, 60)),
            Region.from_points(Point(40, 0), Point(60, 45)),
            Region.from_points(Point(40, 35), Point(60, 45)),
            Region.from_points(Point(40, 0), Point(60, 60)),
        ],
    )
    def test_partial_overlap_in_regions_is_not_contained_when_overlap_is_all(contained_region):
        container_region = Region.from_points(Point(20, 30), Point(40, 50))
        assert not container_region.contains(contained_region, overlap="all")
