import sandhi as sandhi_module
S = sandhi_module.Sandhi()

A = "रामः"
B = "च"
C = "रामश्च"

results = S.sandhi(A, B)
# results is a list of [output_form, rule_chain, rule_names]

valid_forms = {r[0] for r in results}
print(valid_forms)
# see all valid sandhi results

is_valid = C in valid_forms
print(is_valid)
# True or False
