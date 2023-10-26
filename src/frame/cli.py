import click
import logging
from .photo_frame import PhotoFrame

@click.command()
@click.option("--dir", required=True, help="Photo directory to scan")
@click.option("--delay", default=40, help="Seconds between slides")
@click.option("--shuffle", is_flag=True, default=True, show_default=True, help="Shuffle photos")
@click.option("--motion-gpio", default=None, help="GPIO pin for optional motion sensor")
@click.option("--use-irw", is_flag=True, default=False, show_default=True, help="Use IR remote")
def main(dir, delay, shuffle, motion_gpio, use_irw):
    """Run a photo frame slideshow."""
    logging.basicConfig(filename='frameLog.log',
                        filemode='w',
                        format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler())

    frame = PhotoFrame(photo_dir=dir, delay=delay, shuffle=shuffle, motion_gpio=motion_gpio, use_irw=use_irw)
    
    try:
        frame.play()
    except Exception as e:
        logging.exception(e)
    finally:
        frame.stop()


if __name__ == "__main__":
    main()
