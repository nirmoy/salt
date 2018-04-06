include:
  - kube-apiserver
  - addons
  - kubectl-config

#######################
# flannel CNI plugin
#######################

{% set plugin = salt['pillar.get']('cni:plugin', 'flannel').lower() %}
{% if plugin == "flannel" %}

/etc/kubernetes/addons/kube-flannel-rbac.yaml:
  file.managed:
    - source:      salt://cni/kube-flannel-rbac.yaml.jinja
    - template:    jinja
    - makedirs:    true
    - require:
      - file:      /etc/kubernetes/addons
  cmd.run:
    - name: |
        kubectl apply --namespace kube-system -f /etc/kubernetes/addons/kube-flannel-rbac.yaml
    - env:
      - KUBECONFIG: {{ pillar['paths']['kubeconfig'] }}
    - require:
      - kube-apiserver
      - file:      {{ pillar['paths']['kubeconfig'] }}
    - watch:
      - file:       /etc/kubernetes/addons/kube-flannel-rbac.yaml

/etc/kubernetes/addons/kube-flannel.yaml:
  file.managed:
    - source:      salt://cni/kube-flannel.yaml.jinja
    - template:    jinja
    - makedirs:    true
    - require:
      - file:      /etc/kubernetes/addons
  cmd.run:
    - name: |
        kubectl apply --namespace kube-system -f /etc/kubernetes/addons/kube-flannel.yaml
    - env:
      - KUBECONFIG: {{ pillar['paths']['kubeconfig'] }}
    - require:
      - kube-apiserver
      - file:      {{ pillar['paths']['kubeconfig'] }}
    - watch:
      - /etc/kubernetes/addons/kube-flannel-rbac.yaml
      - file:      /etc/kubernetes/addons/kube-flannel-rbac.yaml

{% endif %}


#######################
# cilium CNI plugin
#######################
{% set plugin = salt['pillar.get']('cni:plugin', 'cilium').lower() %}
{% if plugin == "cilium" %}

/etc/kubernetes/addons/cilium.yaml:
  file.managed:
    - source:      salt://cni/cilium.yaml.jinja
    - template:    jinja
    - makedirs:    true
    - require:
      - file:      /etc/kubernetes/addons
    - defaults:
        user: 'cluster-admin'
        cilium_certificate: {{ pillar['ssl']['cilium_crt'] }}
        cilium_key: {{ pillar['ssl']['cilium_key'] }}

  cmd.run:
    - name: |
        kubectl apply --namespace kube-system -f /etc/kubernetes/addons/cilium.yaml
    - env:
      - KUBECONFIG: {{ pillar['paths']['kubeconfig'] }}
    - require:
      - kube-apiserver
      - file:      {{ pillar['paths']['kubeconfig'] }}
    - watch:
      - file:       /etc/kubernetes/addons/cilium.yaml
{% endif %}

