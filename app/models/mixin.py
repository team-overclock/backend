from decimal import Decimal
from geoalchemy2.shape import to_shape


class CoordinatesMixin:
    """
    좌표 모델 Mixin (POINT 타입)
    - point: 상속받는 모델에서 POINT 타입으로 반드시 선언해야 함
    - coordinates: point 값을 (x, y) 형식의 튜플로 리턴 및 입력받는 getter/setter
    - latitude: 위도
    - longitude: 경도
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "point"):
            raise NotImplementedError(f"{cls.__name__} 모델이 CoordinatesMixin을 상속받았지만 'point' 컬럼이 선언되지 않았습니다.")
        
    def __get_point__(self):
        """바이너리로 저장된 point 값을 Point 객체로 변환"""
        if not hasattr(self, "_cached_shape") or self._cached_shape is None:
            self._cached_shape = to_shape(self.point)
        return self._cached_shape

    @property
    def coordinates(self) -> tuple[float, float]:
        """좌표 (위도, 경도)"""
        point = self.__get_point__()
        return point.y, point.x

    @property
    def latitude(self):
        """위도"""
        return self.coordinates[0]

    @property
    def longitude(self):
        """경도"""
        return self.coordinates[1]

    @coordinates.setter
    def coordinates(self, value: tuple[Decimal | float, Decimal | float]):
        """
        입력받은 값을 POINT 문자열로 변환하여 point에 저장
        - 입력 가능 형식: tuple(latitude, longitude)
        """
        try:
            latitude, longitude = value
            lat = f"{latitude:.12f}".rstrip("0").rstrip(".")
            lon = f"{longitude:.12f}".rstrip("0").rstrip(".")
            self.point = f"POINT({lon} {lat})"
            self._cached_shape = None  # 값이 바뀌었으므로 캐시 초기화
        except (ValueError, TypeError):
            raise ValueError("coordinates 값이 올바르지 않습니다. (latitude, longitude) 형식의 튜플을 입력해야 합니다.")
