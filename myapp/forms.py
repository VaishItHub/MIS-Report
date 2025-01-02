from django import forms

class GenerateReportForm(forms.Form):
    generate_report = forms.BooleanField(required=False, initial=True, widget=forms.HiddenInput)
