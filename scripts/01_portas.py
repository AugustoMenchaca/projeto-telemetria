"""Lista interfaces seriais sem abrir as portas."""

import argparse
import json
from pathlib import Path

from _comum import abrir_saida, agora, biblioteca_serial, executar


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Salvar inventário JSON em arquivo novo.")
    args = parser.parse_args()
    print("Inventário do conversor: uma porta COM não confirma comunicação com o ABS CEL S.")
    biblioteca_serial()
    from serial.tools import list_ports

    portas = [{"port": p.device, "description": p.description,
               "manufacturer": p.manufacturer, "vid": p.vid, "pid": p.pid,
               "serial_number": p.serial_number, "hwid": p.hwid}
              for p in sorted(list_ports.comports(), key=lambda p: p.device)]
    if not portas:
        print("Nenhuma porta serial encontrada.")
    for porta in portas:
        print(f"{porta['port']} | {porta['description']} | "
              f"fabricante={porta['manufacturer']} | VID={porta['vid']} PID={porta['pid']}")
    if args.output:
        with abrir_saida(args.output) as arquivo:
            json.dump({"timestamp": agora(), "ports": portas}, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")
        print(f"Inventário: {args.output.resolve()}")


if __name__ == "__main__":
    raise SystemExit(executar(main))
