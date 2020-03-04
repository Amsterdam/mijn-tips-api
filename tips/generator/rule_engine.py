from objectpath import Tree


def get_tips(userdata, tips, compound_rules):  # fixme: does not belong here.
    new_tips = []

    user_data_tree = Tree(userdata)

    for t in tips:
        if "rules" in t:
            passed = apply_rules(user_data_tree, t["rules"], compound_rules)
            print("passed", passed)
            if passed:
                new_tips.append(t)
        else:
            new_tips.append(t)

    return new_tips


def apply_rules(userdata, rules, compound_rules):
    """ returns True when it matches the rules. """
    return all([_apply_rule(userdata, r, compound_rules) for r in rules])


def _apply_rule(userdata, rule, compound_rules):
    print("rule", [rule])
    if rule['type'] == "rule":
        print("2-1")
        print("> ", userdata.execute(rule['rule']))
        return userdata.execute(rule['rule'])

    if rule['type'] == "ref":
        print("2-2")
        compound_rule = compound_rules[rule['ref_id']]
        return apply_rules(userdata, compound_rule['rules'], compound_rules)
    return False


