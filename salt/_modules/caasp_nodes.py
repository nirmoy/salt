from __future__ import absolute_import

# minimum number of nodes (per role) we can have after a removal
_MIN_ETCD_MEMBERS_AFTER_REMOVAL = 1
_MIN_MASTERS_AFTER_REMOVAL = 1
_MIN_MINIONS_AFTER_REMOVAL = 1


def get_nodes(expr):
    '''
    Get all the nodes that match some expression `expr`
    '''
    assert expr
    return __salt__['caasp_grains.get'](e).keys()


def get_booted_nodes(expr):
    '''
    Get all the bootstrapped nodes that match some expression `expr`
    '''
    assert expr
    return get_nodes(expr + ' and G@bootstrap_complete:true')


def _get_replacement_for_etcd(excluded=[]):
    '''
    Get a node that can replace a etcd member
    Returns '' if no replacement can be found.
    '''
    res = __salt__['caasp_etcd.get_nodes_for_etcd'](1, excluded=excluded)
    return res[0] if len(res) > 0 else ''


def get_replacement_for(target, replacement='',
                        masters=None, minions=None, etcd_members=None,
                        excluded=[]):
    '''
    When removing a node `target`, try to get a replacement for all the roles that were
    running there.

    If the user provides an explicit `replacement`, verify that that replacement is valid.

    If no replacement can be found, we are fine as long as we have a minimum number
    of nodes with that role (ie, for masters, we are fine as long as we have at least one master).
    '''
    assert target

    replacement_provided = (replacement != '')
    replacement_roles = []

    # hack-ish shortcuts for the logging functions
    debug = __salt__['caasp_log.debug']
    warn = __salt__['caasp_log.warn']
    abort = __salt__['caasp_log.abort']

    # preparations

    # check: we cannot try to remove some 'virtual' nodes
    forbidden = get_nodes('P@roles:(admin|ca)')
    if target in forbidden:
        abort('%s cannot be removed: it has a "ca" or "admin" role',
              target)
    elif replacement_provided and replacement in forbidden:
        abort('%s cannot be replaced by %s: the replacement has a "ca" or "admin" role',
              target, replacement)

    etcd_members = etcd_members or get_nodes('G@roles:etcd')
    masters = masters or get_nodes('G@roles:kube-master')
    minions = minions or get_nodes('G@roles:kube-minion')

    #
    # replacement for etcd members
    #
    if target in etcd_members:
        if not replacement:
            # we must choose another node and promote it to be an etcd member
            replacement = _get_replacement_for_etcd(excluded=excluded)

        # check if the replacement provided is valid
        if replacement:
            bootstrapped_etcd_members = get_booted_nodes('G@roles:etcd')
            if replacement in bootstrapped_etcd_members:
                warn('the replacement for the etcd server %s cannot be %s: another etcd server is already running there',
                     target, replacement)
                replacement = ''
                if replacement_provided:
                    abort('fatal!! the user provided replacement %s cannot be used',
                          replacement)

        if replacement:
            debug('setting %s as the replacement for the etcd member %s',
                  replacement, target)
            replacement_roles.append('etcd')
        elif len(etcd_members) > _MIN_ETCD_MEMBERS_AFTER_REMOVAL:
            warn('number of etcd members will be reduced to %d, as no replacement for %s has been found (or provided)',
                 len(etcd_members), target)
        else:
            # we need at least one etcd server
            abort('cannot remove etcd member %s: too few etcd members, and no replacement found or provided',
                  target)

    #
    # replacement for k8s masters
    #
    if target in masters:
        if not replacement:
            # TODO: implement a replacement finder for k8s masters
            # NOTE: even if no `replacement` was provided in the pillar,
            #       we probably have one at this point: if the master was
            #       running etcd as well, we have already tried to find
            #       a replacement in the previous step...
            #       however, we must verify that the etcd replacement
            #       is a valid k8s master replacement too.
            #       (ideally we should find the union of etcd and
            #       masters candidates)
            pass

        # check if the replacement provided/found is valid
        if replacement:
            bootstrapped_masters = get_booted_nodes('G@roles:kube-master')
            if replacement in bootstrapped_masters:
                warn('error!! the replacement for an k8s master %s cannot be %s: another k8s master is already running there',
                     target, replacement)
                replacement = ''
                if replacement_provided:
                    abort('fatal!! the user provided replacement %s cannot be used',
                          replacement)

            elif replacement in minions:
                warn('warning!! will not replace the k8s master at %s: the replacement found/provided is the k8s minion %s',
                     target, replacement)
                replacement = ''
                if replacement_provided:
                    abort('fatal!! the user provided replacement %s cannot be used',
                          replacement)

        if replacement:
            debug('setting %s as replacement for the kubernetes master %s',
                  replacement, target)
            replacement_roles.append('kube-master')
        elif len(masters) > _MIN_MASTERS_AFTER_REMOVAL:
            warn('number of k8s masters will be reduced to %d, as no replacement for %s has been found (or provided)',
                 len(masters), target)
        else:
            # we need at least one master (for runing the k8s API at all times)
            abort('cannot remove master %s: too few k8s masters, and no replacement found or provided',
                  target)

    #
    # replacement for k8s minions
    #
    if target in minions:
        if not replacement:
            # TODO: implement a replacement finder for k8s minions
            pass

        # check if the replacement provided/found is valid
        # NOTE: maybe the new role has already been assigned in Velum...
        if replacement:

            if replacement in get_booted_nodes('G@roles:kube-minion'):
                warn('warning! replacement for %s, %s, has already been assigned a k8s minion role',
                     target, replacement)
                replacement = ''
                if replacement_provided:
                    abort('fatal!! the user provided replacement %s cannot be used',
                          replacement)

            elif replacement in masters:
                warn('will not replace the k8s minion %s: the replacement %s is already a k8s master',
                     target, replacement)
                replacement = ''
                if replacement_provided:
                    abort('fatal!! the user provided replacement %s cannot be used',
                          replacement)

            elif 'kube-master' in replacement_roles:
                warn('will not replace the k8s minion %s: the replacement found/provided, %s, is already scheduled for being a new k8s master',
                     target, replacement)
                replacement = ''
                if replacement_provided:
                    abort('fatal!! the user provided replacement %s cannot be used',
                          replacement)

        if replacement:
            debug('setting %s as replacement for the k8s minion %s',
                  replacement, target)
            replacement_roles.append('kube-minion')
        elif len(minions) > _MIN_MINIONS_AFTER_REMOVAL:
            warn('number of k8s minions will be reduced to %d, as no replacement for %s has been found (or provided)',
                 len(masters), target)
        else:
            # we need at least one minion (for running dex, kube-dns, etc..)
            abort('cannot remove minion %s: too few k8s minions, and no replacement found or provided',
                  target)

    # other consistency checks...
    if replacement:
        # consistency check: if there is a replacement, it must have some (new) role(s)
        if not replacement_roles:
            abort('%s cannot be removed: too few etcd members, and no replacement found',
                  target)
    else:
        # if no valid replacement has been found, clear the roles too
        replacement_roles = []

    return replacement, replacement_roles


def get_affected_by(target, excluded=[],
                    masters=None, minions=None, etcd_members=None):
    '''
    Get the list of roles that are affected by the
    addition/removal of `target`. Those affected nodes should
    be highstated in order to update their configuration.

    Some notes:

      * we only consider bootstraped nodes.
      * we ignore nodes where some oither operation is in progress (ie, an update)
    '''
    affected_expr = ''
    affected_roles = []

    etcd_members = etcd_members or get_nodes('G@roles:etcd')
    masters = masters or get_nodes('G@roles:kube-master')
    minions = minions or get_nodes('G@roles:kube-minion')

    if target in etcd_members:
        # we must highstate:
        # * etcd members (ie, peers list in /etc/sysconfig/etcd)
        affected_roles.append('etcd')
        # * api servers (ie, etcd endpoints in /etc/kubernetes/apiserver
        affected_roles.append('kube-master')

    if target in masters:
        # we must highstate:
        # * admin (ie, haproxy)
        affected_roles.append('admin')
        # * minions (ie, haproxy)
        affected_roles.append('kube-minion')

    if target in minions:
        # ok, ok, /etc/hosts will contain the old node, but who cares!
        pass

    if affected_roles:

        affected_expr += ('G@bootstrap_complete:true' +
                          ' and not G@bootstrap_in_progress:true' +
                          ' and not G@update_in_progress:true' +
                          ' and not G@removal_in_progress:true' +
                          ' and P@roles:(' + affected_roles | join('|') + ')')

        excluded_nodes = [target]
        if excluded:
            excluded_nodes += [x for x in excluded if x]

        affected_expr += ' and not L@' + excluded_nodes | join(',')

    return affected_expr
