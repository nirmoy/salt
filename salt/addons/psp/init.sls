{% if salt.caasp_pillar.get('addons:psp', True) %}

include:
  - kube-apiserver
  - kubectl-config

{% from '_macros/kubectl.jinja' import kubectl, kubectl_apply_template, kubectl_apply_dir_template with context %}


{{ kubectl_apply_dir_template("salt://addons/psp/manifests/",
                              "/etc/kubernetes/addons/psp/") }}

# TODO: In order for the lockdown PSP to be usable, we have to
# allow users to remove this CRB without us/salt recreating it.
# i.e. we must only apply this role to a cluster once.
{{ kubectl_apply_template("salt://addons/psp/podsecuritypolicy-crb.yaml.jinja",
                          "/etc/kubernetes/addons/podsecuritypolicy-crb.yaml") }}

{% else %}

dummy:
  cmd.run:
    - name: echo "PSP addon not enabled in config"

{% endif %}
