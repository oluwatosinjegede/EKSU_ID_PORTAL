from django import forms
from django.contrib.auth.forms import SetPasswordForm


class ForcePasswordChangeForm(SetPasswordForm):
    """
    Forces user to change password on first login.
    Uses Django's secure password validation.
    """

    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            "class": "w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        }),
    )

    new_password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "class": "w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        }),
    )
