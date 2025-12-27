This project demonstrates a sample-oriented AI voice assistant for dental appointment scheduling,
 focusing on reliability, compliance awareness, and controlled AI behavior rather than fully autonomous decision-making.


how to run:
1️⃣ Clone the project:

    git clone https://github.com/arashmjr/ai-voice-agent.git
    cd ai-voice-agent

2️⃣ Create and activate virtual environment:

        command: python -m venv venv

        # Windows:
        venv\Scripts\activate
        # macOS/Linux:
        source venv/bin/activate

3️⃣ Add .env file:

    Copy your .env file to the root of the project

4️⃣ Install requirements:

    pip install -r requirements.txt

5️⃣ Set up MongoDB:

    Make sure you have MongoDB running.
    The connection string in .env should point to your MongoDB instance.

6️⃣ Run the Flask app:
    command: python app.py
    The app should now be accessible at http://localhost:5000