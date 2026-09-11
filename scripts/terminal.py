#!/usr/bin/env python3
"""The same activity geometry, rendered live in a truecolor Braille terminal."""
import argparse
import json
import math
import pathlib
import shutil
import sys
import time

import numpy as np
from collect_activity import validate
from render_profile import geometry, rotation

ROOT = pathlib.Path(__file__).resolve().parents[1]
BITS = np.array([[1, 8], [2, 16], [4, 32], [64, 128]])


def render(snapshot, mesh_data, phase, columns=72, rows=27):
    mesh, normals, _, share = mesh_data
    transform = rotation(phase, snapshot['seed'])
    points = (mesh @ transform.T).reshape(-1, 3)
    facing = (normals @ transform.T).reshape(-1, 3)
    shares = np.repeat(share, mesh.shape[1])
    width, height = columns*2, rows*4
    extent = float(np.linalg.norm(mesh, axis=-1).max())
    scale = min(width, height)/(2*extent+1)
    x = np.rint(points[:, 0]*scale+width/2).astype(int)
    y = np.rint(-points[:, 1]*scale+height/2).astype(int)
    dots = np.zeros((rows, columns), dtype=int)
    colors = np.zeros((rows, columns, 3), dtype=int)
    # Draw far to near; the nearest surface sets each cell's material.
    for k in np.argsort(points[:, 2]):
        if facing[k, 2] < 0 or not (0 <= x[k] < width and 0 <= y[k] < height):
            continue
        row, column = y[k]//4, x[k]//2
        dots[row, column] |= int(BITS[y[k]%4, x[k]%2])
        public = np.array([169, 209, 210])
        private = np.array([214, 174, 135])
        light = .4+.6*max(float(facing[k] @ np.array([-.3, .5, .8])), 0)
        colors[row, column] = np.clip((public*(1-shares[k])+private*shares[k])*light, 0, 255)
    lines = []
    for row in range(rows):
        parts = []
        for column in range(columns):
            bits = int(dots[row, column])
            if bits:
                r,g,b = colors[row, column]
                parts.append(f'\x1b[38;2;{r};{g};{b}m'+chr(0x2800+bits))
            else:
                parts.append(' ')
        lines.append(''.join(parts)+'\x1b[0m')
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--still',action='store_true',help='Print one frame without terminal control')
    args=parser.parse_args()
    snapshot=validate(json.loads((ROOT/'activity.json').read_text()))
    mesh=geometry(snapshot)
    size=shutil.get_terminal_size((80,32))
    columns=max(20,min(size.columns-2,96));rows=max(8,min(size.lines-5,36))
    if args.still or not sys.stdout.isatty():
        print(render(snapshot,mesh,0,columns,rows))
        return
    try:
        sys.stdout.write('\x1b[?1049h\x1b[?25l')
        start=time.monotonic()
        while True:
            phase=(time.monotonic()-start)/7.68*math.tau
            sys.stdout.write('\x1b[H'+render(snapshot,mesh,phase,columns,rows))
            sys.stdout.write('\n\x1b[0mBenjamin Marshall  /  public + private activity  /  Ctrl-C to exit\x1b[K')
            sys.stdout.flush()
            time.sleep(.05)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\x1b[0m\x1b[?25h\x1b[?1049l');sys.stdout.flush()


if __name__=='__main__': main()
