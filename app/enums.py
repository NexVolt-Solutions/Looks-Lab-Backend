import enum


class AuthProviderEnum(str, enum.Enum):
    GOOGLE = "google"
    APPLE = "apple"


class DomainEnum(str, enum.Enum):
    SKINCARE  = "skincare"
    HAIRCARE  = "haircare"
    FASHION   = "fashion"
    WORKOUT   = "workout"
    DIET      = "diet"
    HEIGHT    = "height"
    QUIT_PORN = "quit_porn"
    FACIAL    = "facial"

    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]

