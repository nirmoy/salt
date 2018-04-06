include:
  - ca-cert
  - cert
  - crypto

{% set plugin = salt['pillar.get']('cni:plugin', 'cilium').lower() %}
{% if plugin == "cilium" %}

{% from '_macros/certs.jinja' import certs with context %}
{{ certs("cilium",
         pillar['ssl']['cilium_crt'],
         pillar['ssl']['cilium_key'],
         cn = grains['nodename'],
         o = 'system:nodes') }}

{% endif %}

