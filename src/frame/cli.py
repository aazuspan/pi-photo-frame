import click
import logging
from .photo_frame import PhotoFrame


@click.command
@click.option("--dir", required=True, help="Photo directory to scan")
@click.option("--delay", default=40, help="Seconds between slides")
@click.option("--shuffle", is_flag=True, default=True, show_default=True, help="Shuffle photos")
@click.option("--motion-gpio", default=None, help="GPIO pin for optional motion sensor")
def main(dir, delay, shuffle, motion_gpio):
    """Run a photo frame slideshow."""
    logging.basicConfig(filename='frameLog.log',
                        filemode='w',
                        format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.INFO)
    
    try:
        frame = PhotoFrame(photo_dir=dir, delay=delay, shuffle=shuffle, motion_gpio=motion_gpio)
    except (KeyboardInterrupt, Exception) as e:
        if isinstance(e, KeyboardInterrupt):
            logging.info('Keyboard interrupt.')
        else:
            logging.exception('Error! Shutting down gracefully.')
    finally:
        frame.stop()


if __name__ == "__main__":
    main()