# Luna - Voice-Activated AI Assistant

## Overview

**Luna** is a voice-activated AI assistant designed to understand speech, process user requests, play music on Spotify, and respond using text-to-speech. Leveraging advanced technologies such as OpenAI's o1 models, Whisper API, and ElevenLabs API, Luna provides a seamless and interactive experience tailored to meet various automation and creative needs.

## Features

- **Speech Recognition:** Converts user speech into text using the Whisper API.
- **Natural Language Processing:** Processes and understands user requests using OpenAI's o1 models.
- **Music Playback:** Plays requested songs on Spotify via the Spotify API.
- **Text-to-Speech:** Responds to user queries with synthesized speech using ElevenLabs API.
- **Structured Responses:** Utilizes Pydantic models to structure assistant responses for efficient processing.
- **Customizable Personality:** Luna's responses are tailored to exhibit a unique personality, ensuring engaging interactions.

## Technologies Used

- **Python 3.11**
- **OpenAI API (o1-mini)**
- **Whisper API (OpenAI)**
- **Spotify API**
- **ElevenLabs API**
- **Pydantic**
- **Pygame**
- **SoundDevice**
- **SoundFile**
- **Keyboard**
- **Dotenv**
- **Logging**

## Installation

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/yourusername/luna-assistant.git
    cd luna-assistant
    ```

2. **Create a Virtual Environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install Dependencies:**

    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

## Configuration

1. **Create a `.env` File:**

    In the root directory, create a `.env` file to store your API keys and configuration parameters.

    ```bash
    touch .env
    ```

2. **Add the Following Variables to `.env`:**

    ```env
    # OpenAI API Key
    LUNAS_OPENAI_API_KEY=your_openai_api_key_here

    # ElevenLabs API Key and Voice ID
    ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
    ELEVENLABS_VOICE_ID=your_elevenlabs_voice_id_here
    ELEVENLABS_MODEL_ID=eleven_multilingual_v2

    # Spotify API Credentials
    SPOTIFY_CLIENT_ID=your_spotify_client_id_here
    SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
    SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
    ```

    **Note:** Replace the placeholder values with your actual API keys and IDs. Ensure that your `.env` file is **not** committed to version control to protect your sensitive information.

## Usage

1. **Run the Application:**

    ```bash
    python luna_assistant.py
    ```

    Upon running, you should see:

    ```
    Luna is ready! Hold Alt+X to record, release to process.
    ```

2. **Interact with Luna:**

    - **Start Recording:** Press and hold the `Alt+X` key combination.
    - **Speak Your Request:** For example, "Yo yo Luna, are you there?"
    - **Stop Recording:** Release the `Alt+X` key to end recording.

    Luna will process your request and respond verbally. If a song is requested, it will be played on Spotify.

## Pydantic Models

Luna uses Pydantic models to structure the assistant's responses, ensuring consistency and ease of processing.

### `Step` Model

Represents individual steps or reasoning processes that Luna undertakes to reach a conclusion.

```python
from pydantic import BaseModel

class Step(BaseModel):
    description: str
    action: str
```

### `AssistantResponse` Model

Aggregates all steps and provides a final resolution. Optionally includes `song_title` and `confidence`.

```python
from typing import List, Optional
from pydantic import BaseModel

class AssistantResponse(BaseModel):
    steps: List[Step]
    final_resolution: str
    song_title: Optional[str] = None
    confidence: Optional[float] = None
```

## User Interaction Flow

1. **Activation:** User presses and holds `Alt+X` to start recording.
2. **Speech Input:** User speaks their request.
3. **Processing:** Upon release of `Alt+X`, the recording is transcribed, processed by Luna, and a response is generated.
4. **Response:** Luna responds verbally. If a song is requested, it plays on Spotify.

## Component Interactions

### 1. Speech Recognition (Whisper API)

- **Function:** `transcribe_audio(audio_file)`
- **Input:** Audio file in WAV format.
- **Output:** Transcribed text.

### 2. Natural Language Processing (OpenAI o1-mini)

- **Function:** `send_to_openai(user_text)`
- **Input:** Transcribed text.
- **Output:** Structured `AssistantResponse` object.
- **Note:** Custom instructions are embedded within the user prompt to maintain Luna's personality.

### 3. Music Playback (Spotify API)

- **Function:** `play_song_on_spotify(song_title)`
- **Input:** Title of the song.
- **Output:** Boolean indicating success or failure of playback.

### 4. Text-to-Speech (ElevenLabs API)

- **Function:** `generate_elevenlabs_audio(text)`
- **Input:** Text to be spoken.
- **Output:** Audio data.
- **Note:** Only the final resolution is sent to ElevenLabs to exclude internal reasoning processes.

## Error Handling

- **Spotify Playback Failure:** An error message is appended to the final response.
- **Text-to-Speech Generation Failure:** An error is printed to the console.
- **API Errors:** All API interactions are wrapped in try-except blocks to capture and log errors without crashing the application.
- **Recording Issues:** Errors during recording are logged, and the application continues to wait for user input.

## Customization

- **Luna's Personality:** Defined within the custom instructions embedded in the user prompt. You can adjust Luna's traits by modifying the `luna_instructions` string in the `send_to_openai` function.
- **Spotify Integration:** Customize the `play_song_on_spotify` function to modify playback behavior, such as selecting different devices or handling playlists.
- **Voice Characteristics:** Adjust ElevenLabs voice settings by changing the `VOICE_ID` and `MODEL_ID` in the `.env` file.
- **Token Management:** Adjust the `max_completion_tokens` parameter in the `send_to_openai` function to balance between response length and cost.

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**
2. **Create a Feature Branch**

    ```bash
    git checkout -b feature/YourFeature
    ```

3. **Commit Your Changes**

    ```bash
    git commit -m "Add your feature"
    ```

4. **Push to the Branch**

    ```bash
    git push origin feature/YourFeature
    ```

5. **Open a Pull Request**

## License

[MIT](LICENSE)

## Acknowledgements

- [OpenAI](https://openai.com/)
- [ElevenLabs](https://elevenlabs.io/)
- [Spotify](https://www.spotify.com/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [pygame](https://www.pygame.org/)
- [Whisper](https://openai.com/blog/whisper/)

---

**Note:** This project is intended for educational and development purposes. Ensure that you comply with the terms of service of all integrated APIs and services.
