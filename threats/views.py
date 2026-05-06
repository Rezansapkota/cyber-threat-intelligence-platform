from django.shortcuts import redirect, render

from .models import Threat


def index(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if title:
            severity = request.POST.get('severity', Threat.SEVERITY_MEDIUM)
            if severity not in dict(Threat.SEVERITY_CHOICES):
                severity = Threat.SEVERITY_MEDIUM

            Threat.objects.create(
                title=title,
                source=request.POST.get('source', '').strip(),
                severity=severity,
                description=request.POST.get('description', '').strip(),
            )
        return redirect('index')

    threats = Threat.objects.all()
    return render(
        request,
        'threats/index.html',
        {
            'severity_choices': Threat.SEVERITY_CHOICES,
            'threats': threats,
        },
    )
