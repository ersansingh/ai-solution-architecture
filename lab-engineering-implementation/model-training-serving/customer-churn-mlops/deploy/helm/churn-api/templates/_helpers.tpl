{{- define "churn-api.labels" -}}
app.kubernetes.io/name: churn-api
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.image.tag | quote }}
project: teleconnect-churn
{{- end -}}

{{- define "churn-api.selector" -}}
app.kubernetes.io/name: churn-api
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
