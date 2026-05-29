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
        SlokaVisitor(chosen).parse()
    c = input("validate again? y/n")
    if c == "n":
        break
