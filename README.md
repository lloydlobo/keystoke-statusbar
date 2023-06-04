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

To run the `keystrokes` script, use the following command:

```shell
python src/app.py
```

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
