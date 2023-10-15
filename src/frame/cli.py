import click
import logging
from .frame import PhotoFrame


@click.command
@click.option("--dir", required=True, help="Photo directory to scan")
@click.option("--delay", default=40, help="Seconds between slides")
@click.option("--shuffle", is_flag=True, default=True, show_default=True, help="Shuffle photos")
def main(dir, delay, shuffle):
    """Run a photo frame slideshow."""
    logging.basicConfig(filename='frameLog.log',
                        filemode='w',
                        format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.INFO)
    
    frame = PhotoFrame(photo_dir=dir, delay=delay, shuffle=shuffle)
    try:
        frame.play()
    # If the program is killed by keyboard, or a bug occurs, make sure the display is awake
    except (KeyboardInterrupt, Exception) as e:
        if isinstance(e, KeyboardInterrupt):
            logging.info('Keyboard interrupt.')
        else:
            logging.exception('Error! Shutting down gracefully.')
    finally:
        frame.wake(force=True)


if __name__ == "__main__":
    main()