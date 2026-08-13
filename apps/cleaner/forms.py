from django import forms


class CleanerUploadForm(forms.Form):

    file = forms.FileField(
        label="CSV file",
        required=True,
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]

        filename = uploaded_file.name.lower()

        if not filename.endswith(".csv"):
            raise forms.ValidationError(
                "Only CSV files are allowed."
            )

        max_size = 50 * 1024 * 1024

        if uploaded_file.size > max_size:
            raise forms.ValidationError(
                "The maximum file size is 50MB."
            )

        return uploaded_file