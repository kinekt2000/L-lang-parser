import os

for i in range(1, 6):
    exe = ".\\src\\LParser.py"
    input = f".\\examples\\exmp{i}.l"
    output_txt = f".\\examples\\output\\txt\\exmp{i}"
    output_png = f".\\examples\\output\\png\\exmp{i}"

    cmd = f"python {exe} {input} -o {output_txt} -i {output_png}"
    os.system(cmd)
