from datetime import datetime

# -------------------------------
# Warranty assignment
# -------------------------------
from datetime import datetime

def assign_warranty(make: str, year: int, mileage: int) -> str:
    """
    Determines warranty type based on vehicle make, year, and mileage.

    Kia:
        - CPO: ≤5 years AND <80k miles
        - Limited: (≤5 years AND 80k–<100k miles) OR (>5 years AND ≤7 years AND <100k miles)
        - As-Is: >7 years OR ≥100k miles

    Non-Kia:
        - Limited: <7 years AND <100k miles
        - As-Is: ≥7 years OR ≥100k miles

    :param make: Vehicle make (string)
    :param year: Vehicle year (int)
    :param mileage: Vehicle mileage (int)
    :return: Warranty type (string)
    """
    current_year = datetime.now().year
    age = current_year - year
    mileage = max(0, mileage)  # ensure mileage isn't negative
    make_lower = make.lower()

    if make_lower == "kia":
        if age <= 5:
            if mileage < 80000:
                return "CPO"
            elif mileage < 100000:
                return "Limited"
            else:
                return "As-Is"
        elif age <= 7:
            if mileage < 100000:
                return "Limited"
            else:
                return "As-Is"
        else:  # age > 7
            return "As-Is"
    else:  # Non-Kia
        if age < 7 and mileage < 100000:
            return "Limited"
        else:
            return "As-Is"

# -------------------------------
# VIN validator (format only)
# -------------------------------
def validate_vin(vin: str) -> bool:
    """
    Validates VIN format only.
    - Required
    - Exactly 17 characters
    - Alphanumeric only
    - No spaces or special characters

    :param vin: VIN string
    :return: True if valid, False otherwise
    """
    if not vin:
        return False

    vin = vin.upper()

    # Must be exactly 17 characters
    if len(vin) != 17:
        return False

    # Must contain only letters and numbers
    if not vin.isalnum():
        return False

    return True
