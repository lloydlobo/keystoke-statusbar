# Keystrokes

The `keystrokes` project allows you to print your keyboard keystrokes to
`stdout` or display them in your status bar. This can be useful for
monitoring and displaying your keystrokes in real-time.

## Usage

> **Note:** Make sure you have Python and pip installed locally.
> Install `python3-pip` or a similar package using your package manager.

### Installation

To install the required dependencies, clone the repository and run
the following command:

```shell
cd keystrokes
pip install -r requirements.txt
```

### Running the Script

To run the `keystrokes` script, follow the instructions below:

#### Emulate 1D terminal game

1. Open a terminal and navigate to the `keystrokes` directory.
2. Run the following command:

   ```shell
   python -u src/app.py > game.log &
   ```

   This command emulates a 1D terminal game and redirects the output to a log file named `game.log`. The `-u` flag is used to enable unbuffered output, ensuring that the log file is updated in real-time as the game progresses. The `&` at the end runs the process in the background.

3. In a separate terminal instance or the same if `&` was used, run the following command:

   ```shell
   watch -n 0.033 "tail -n 1 game.log"
   ```

   This command continuously monitors the `game.log` file and displays the latest line every 0.033 seconds, creating a live gameplay experience. The interval of 0.033 seconds corresponds to a frame rate of approximately 30 frames per second (fps), providing smooth gameplay.

#### For raw live output

1. Open a terminal and navigate to the `keystrokes` directory.
2. Run the following command:

   ```shell
   python src/app.py
   ```

   This command runs the script and provides raw live output without any logging.

Make sure you have Python installed and the necessary dependencies are installed before running the script.

### Keybindings

The following keybindings are available:

- Press the `Escape` key to toggle listening to key events.
  - This can be useful when you don't want to display sensitive information,
    such as passwords, in your status bar.
  - **Note:** Even when the event listener is toggled off, it continues running
    silently in the background. If you want complete silence, you can stop
    the script and resume it later.

## Integration with Polybar

To integrate `keystrokes` with Polybar, you can use the following configuration:

```ini
modules-center = keystrokes

[module/keystrokes]
type = custom/script
exec = "/usr/bin/python3 -u $HOME/keystrokes/src/app.py"
tail = true
```

This configuration adds the `keystrokes` module to the center section of
your Polybar. It executes the `keystrokes` script using Python and
displays the output in the status bar. The `tail = true` option ensures
that the output is continuously updated in the status bar.

## Credits

- [@petternett](https://github.com/petternett/railway-statusbar)
  for providing inspiration for this project.

Feel free to modify the configuration and adapt it to your specific setup
or requirements.

If you have any questions or need further assistance, please let us know.
