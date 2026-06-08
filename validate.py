from nirukta.util import (
    SlokaVisitor,
    SutraVisitor,
    choose_nirukta_file,
    is_nirukta_file,
)

chosen = choose_nirukta_file()
assert is_nirukta_file(chosen), "Invalid file"

while True:
    if ".sutra" in chosen:
        SutraVisitor(chosen).parse()
    else:
        sf = SlokaVisitor(chosen).parse()
        for line in sf.sloka.lines:
            for v in line.vAkyAni:
                for x in v.tokens:
                    print(x)
    c = input("validate again? [Y]/n\n")
    if c == "n":
        break
