# Tide Indicator

A Python-based application indicator for Linux desktop environments that displays tidal information.

## Description

This application fetches tidal data from the UK National Tide Gauge Network API (Admiralty API) and presents it conveniently in your system tray. It provides essential information such as high/low water times and heights. The application is designed to be easily configurable with user-defined scripts for data retrieval and supports dynamic time adjustments for daylight saving.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Electrik-rich546456/tide_indicator.git
    cd tide_indicator
    ```

2.  **Install dependencies:**
    ```bash
    pip install requests pytz
    ```

3.  **Configure API Key:**
    Create a file named `config.py` in the `src/` directory with your Admiralty API key:
    ```python
    # src/config.py
    API_KEY = "YOUR_ADMIRALTY_API_KEY_HERE"
    ```
    (Replace `YOUR_ADMIRALTY_API_KEY_HERE` with your actual key. This file is ignored by Git for security.)

4.  **Make the .desktop file executable:**
    ```bash
    chmod +x indicator-tide.py.desktop
    ```

5.  **Install the .desktop file (optional, for system-wide use):**
    ```bash
    cp indicator-tide.py.desktop ~/.local/share/applications/
    cp indicator-tide.svg ~/.local/share/icons/
    ```
    You might need to update your desktop's icon cache:
    ```bash
    gtk-update-icon-cache -f -t ~/.local/share/icons/
    ```

## Usage

To run the indicator, you can execute the main Python script directly:

```bash
python3 src/indicator-tide.py
```

If you installed the `.desktop` file, you should be able to find "Tide Indicator" in your applications menu and launch it from there.

## Credits

*   **Original Author:** Bernard Giannetti
*   **Contributions by:** Electrik.rich

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
