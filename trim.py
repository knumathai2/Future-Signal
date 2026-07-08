import sys
for file in sys.argv[1:]:
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with open(file, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line.rstrip() + '\n')
