{{- define "roomops.name" -}}
roomops
{{- end }}

{{- define "roomops.labels" -}}
app.kubernetes.io/name: {{ include "roomops.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
