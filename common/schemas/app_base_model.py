from pydantic import BaseModel, ConfigDict


class AppBaseModel(BaseModel):
    """
    A custom base model that serves as the foundation or all the models in the application.

    This model includes global configuration settings that are inherited by all subclasses,
    ensuring consistent behaviour across the application's data models.

    Key Features:
    - Allows creation of model instances from ORM objects.
    - Validates attribute assignments.
    - Uses enum values instead of enum objects.

    """

    model_config = ConfigDict(
        from_attributes=True,  # Allow creation of model instances from ORM objects
        validate_assignment=True,  # Validate attribute assignments
        use_enum_values=True,  # Use enum values instead of enum objects
    )
