{{/*
Expand the name of the chart.
*/}}
{{- define "project-chimera.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "project-chimera.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "project-chimera.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "project-chimera.labels" -}}
helm.sh/chart: {{ include "project-chimera.chart" . }}
{{ include "project-chimera.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "project-chimera.selectorLabels" -}}
app.kubernetes.io/name: {{ include "project-chimera.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "project-chimera.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "project-chimera.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Image reference
*/}}
{{- define "project-chimera.image" -}}
{{- $registry := .Values.global.imageRegistry | default "" }}
{{- if $registry }}
{{- $registry }}/{{ .Values.images.repository }}:{{ .Values.images.tag | default .Chart.AppVersion }}
{{- else }}
{{- .Values.images.repository }}:{{ .Values.images.tag | default .Chart.AppVersion }}
{{- end }}
{{- end }}
