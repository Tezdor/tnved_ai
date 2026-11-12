from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.registration_password_validators = [
            validator
            for validator in password_validation.get_default_password_validators()
            if not isinstance(
                validator,
                password_validation.UserAttributeSimilarityValidator,
            )
        ]

        self.fields["password1"].help_text = (
            password_validation.password_validators_help_text_html(
                self.registration_password_validators
            )
        )

    @sensitive_variables("password")
    def validate_password_for_user(self, user, password_field_name="password2"):
        password = self.cleaned_data.get(password_field_name)
        if not password:
            return

        try:
            password_validation.validate_password(
                password,
                user,
                password_validators=self.registration_password_validators,
            )
        except ValidationError as error:
            self.add_error(password_field_name, error)