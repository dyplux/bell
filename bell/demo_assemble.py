#!/usr/bin/env python3
"""Assemble the Bell demo cut from the capture and its manifest.

Every cut point comes from `at_seconds` in the manifest the recorder wrote, so
the edit is a function of the recording rather than of somebody scrubbing for
the right frame. Re-record and re-run this and you get the same cut.

Order is claim then proof: each statement card precedes the product footage it
describes, never the other way round, and never laid over the interface.
"""
from pathlib import Path
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CAPTURE_ROOT = Path(
    os.environ.get('BELL_DEMO_DIR', '/tmp/bell-demo-video'))
CAP = CAPTURE_ROOT
CARDS = CAPTURE_ROOT / 'cards'
WORK = CAPTURE_ROOT / 'cut'
FFMPEG = os.environ.get('FFMPEG', 'ffmpeg')
FFPROBE = os.environ.get('FFPROBE', 'ffprobe')

# card index -> the step it introduces. 'head' plays before everything and
# 'tail' after, which is why they name no step.
PLAN = [
    (0, 'head', 2.8),
    (1, 'hero', 3.4),
    (2, 'silver-search', 2.6),
    (3, 'silver-evidence', 3.0),
    (4, 'population-shape', 2.6),
    (5, 'population-concentration', 2.6),
    (6, 'facts-open', 2.8),
    (7, 'gold-repeat-window', 2.6),
    (8, 'map-only', 2.6),
    (9, 'receipt', 3.0),
    (10, 'tail', 3.6),
]

V = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
     '-pix_fmt', 'yuv420p', '-r', '25', '-vsync', 'cfr']
A = ['-c:a', 'aac', '-b:a', '96k', '-ar', '48000', '-ac', '2']


def run(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"{' '.join(args[:6])} failed:\n{result.stderr[-1200:]}")


def duration(path: Path) -> float:
    out = subprocess.run([FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
                          '-of', 'default=nw=1:nk=1', str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def main() -> int:
    manifest = json.loads((CAP / 'manifest.json').read_text())
    source = CAP / manifest['video']
    total = duration(source)
    at = {step['id']: float(step['at_seconds']) for step in manifest['steps']}
    order = [step['id'] for step in manifest['steps']]
    WORK.mkdir(parents=True, exist_ok=True)

    # The first plan named eight of the nine steps, so the cut simply ended
    # before the receipt: eleven seconds of the closing proof dropped, silently,
    # because nothing compared the plan against the recording. A cut that leaves
    # out evidence without saying so is the thing this whole project reports.
    planned = {step for _, step, _ in PLAN} - {'head', 'tail'}
    missing = [name for name in order if name not in planned]
    if missing:
        raise SystemExit(
            'the edit plan leaves these recorded steps out of the cut: '
            + ', '.join(missing))
    unknown = sorted(planned - set(order))
    if unknown:
        raise SystemExit('the edit plan names steps the recording does not have: '
                         + ', '.join(unknown))

    # Each step runs until the next one is stamped; the last runs to the end.
    span = {}
    for index, name in enumerate(order):
        start = at[name]
        end = at[order[index + 1]] if index + 1 < len(order) else total
        span[name] = (start, end)

    pieces: list[Path] = []
    for card, step, seconds in PLAN:
        image = CARDS / f'card-{card:02d}.png'
        if not image.is_file():
            raise SystemExit(f'missing {image}')
        piece = WORK / f'{len(pieces):02d}-card{card:02d}.mp4'
        run([FFMPEG, '-y', '-loop', '1', '-t', f'{seconds}', '-i', str(image),
             '-f', 'lavfi', '-t', f'{seconds}', '-i', 'anullsrc=r=48000:cl=stereo',
             '-vf', 'scale=1920:1080', *V, *A, '-shortest', str(piece)])
        pieces.append(piece)

        if step in ('head', 'tail'):
            continue
        start, end = span[step]
        piece = WORK / f'{len(pieces):02d}-{step}.mp4'
        run([FFMPEG, '-y', '-ss', f'{start}', '-to', f'{end}', '-i', str(source),
             '-f', 'lavfi', '-t', f'{end - start}', '-i', 'anullsrc=r=48000:cl=stereo',
             '-map', '0:v:0', '-map', '1:a:0', *V, *A, '-shortest', str(piece)])
        pieces.append(piece)

    listing = WORK / 'pieces.txt'
    listing.write_text(''.join(f"file '{p}'\n" for p in pieces), encoding='utf-8')
    final = CAPTURE_ROOT / 'bell-demo.mp4'
    run([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', str(listing),
         '-c', 'copy', '-movflags', '+faststart', str(final)])

    print(f'source      {total:.2f}s, {len(order)} steps')
    for card, step, seconds in PLAN:
        if step in ('head', 'tail'):
            print(f'  card {card:02d}  {seconds:5.1f}s  ({step})')
        else:
            start, end = span[step]
            print(f'  card {card:02d}  {seconds:5.1f}s  +  {step:26s} '
                  f'{start:6.2f} to {end:6.2f}  ({end - start:5.2f}s)')
    print(f'\n{final.name}  {duration(final):.2f}s  {final.stat().st_size / 1e6:.1f} MB')
    return 0


if __name__ == '__main__':
    sys.exit(main())
