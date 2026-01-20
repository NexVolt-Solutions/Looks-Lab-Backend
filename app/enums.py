import enum

class AuthProviderEnum(str, enum.Enum):
    GOOGLE = "google"
    APPLE = "apple"


class DomainEnum(str, enum.Enum):
    """Valid domain values - single source of truth."""
    SKINCARE = "skincare"
    HAIRCARE = "haircare"
    FASHION = "fashion"
    WORKOUT = "workout"
    DIET = "diet"
    HEIGHT = "height"
    QUIT_PORN = "quit porn"
    FACIAL = "facial"

    @classmethod
    def values(cls) -> set[str]:
        """Return set of all domain values."""
        return {item.value for item in cls}

