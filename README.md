# ShareBot+

## Introduction

Welcome to the ShareBot+ Python project! This is a simple discord bot for sharing your server with other discord servers the bot is in. To get started, follow the installation and run guide below.

## Installation

Before running the project, ensure that you have Python installed on your system. If not, you can download and install Python from [python.org](https://www.python.org/downloads/)

1. **Clone the Repository:**

   Clone this repository to your local machine using Git:

   ```bash
   git clone https://github.com/CutyCat2000/ShareBot-.git
   ```

2. **Navigate to the Project Directory:**

   Change your current working directory to the project folder:

   ```bash
   cd "ShareBot-"
   ```

3. **Create a Virtual Environment (Optional but recommended):**

   It's a good practice to create a virtual environment for your project to isolate dependencies. You can create a virtual environment using `venv` (Python 3.3+):

   ```bash
   python -m venv venv
   ```

4. **Activate the Virtual Environment (Optional but recommended):**

   On Windows:

   ```bash
   venv\Scripts\activate
   ```

   On macOS and Linux:

   ```bash
   source venv/bin/activate
   ```

5. **Install Dependencies:**

   Install the project dependencies using pip:

   ```bash
   pip install -r requirements.txt
   ```

6. **Configurate your Bot**

   Go to [config.py](config.py) and set all the variables.

7. **Run the Bot:**

   Start the bot by running:

   ```bash
   python main.py
   ```

   If the config is correct, the bot will be running now.

## Customization

You can customize the project further by modifying the Django settings, adding new features, or changing the frontend templates. Refer to the Django documentation for more information on customization: [Django Documentation](https://docs.djangoproject.com/en/3.2/)

## Contributing

If you'd like to contribute to the project, feel free to submit pull requests or open issues on the GitHub repository.

## New Releases

To update your bot without loosing data, keep the db.sqlite3 and the config.py file the same as you have, just replace all other files with the new ones. Then restart your bot.

## License

This project is licensed under the MPL License - see the [LICENSE](LICENSE) file for details.

## Contact

If you have any questions or need further assistance, feel free to open an issue.

Enjoy using ShareBot+!
