from objectpath import ExecutionError


def apply_rules(userdata, rules, compound_rules):
    """ returns True when it matches the rules. """
    return all([_apply_rule(userdata, r, compound_rules) for r in rules])


def _apply_rule(userdata, rule, compound_rules):
    if rule['type'] == "rule":
        try:
            return userdata.execute(rule['rule'])
        except ExecutionError:
            return False

    if rule['type'] == "ref":
        compound_rule = compound_rules[rule['ref_id']]
        return apply_rules(userdata, compound_rule['rules'], compound_rules)
    return False
