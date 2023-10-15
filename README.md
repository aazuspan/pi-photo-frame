## Installation

```bash
pip install -e .
```

Optionally install `gpiozero` for motion sensor support:

```bash
pip install gpiozero
```

## Usage

Run `frame --help` to see usage options.

```bash
Usage: frame [OPTIONS]

  Run a photo frame slideshow.

Options:
  --dir TEXT          Photo directory to scan  [required]
  --delay INTEGER     Seconds between slides
  --shuffle           Shuffle photos  [default: True]
  --motion-gpio TEXT  GPIO pin for optional motion sensor
  --help              Show this message and exit
```

For example:

```bash
frame --dir /path/to/photos --delay 30 --motion-gpio 15
```